"""
Promo Code Service

Handles validation and application of promotional codes.
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, Any

from django.utils import timezone
from django.db import transaction
from django.db.models import F

from .models import PromoCode, PromoCodeUsage
from apps.users.models import User
from apps.services.models import ServicePlan, UserService

logger = logging.getLogger(__name__)


class PromoCodeService:
    """Service for handling promo code operations"""

    @classmethod
    def validate_code(
        cls,
        code: str,
        user: User,
        plan: Optional[ServicePlan] = None,
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Validate a promo code for a user and optional plan.

        Args:
            code: The promo code string
            user: The user trying to use the code
            plan: Optional service plan the code will apply to
            amount: Optional purchase amount

        Returns:
            Dictionary with validation result and discount info
        """
        try:
            promo = PromoCode.objects.get(code__iexact=code.strip())
        except PromoCode.DoesNotExist:
            return {
                'valid': False,
                'error': 'Codigo promocional no encontrado',
                'error_code': 'NOT_FOUND'
            }

        # Check if code is active
        if promo.status != PromoCode.Status.ACTIVE:
            return {
                'valid': False,
                'error': 'Este codigo no esta activo',
                'error_code': 'INACTIVE'
            }

        # Check validity dates
        now = timezone.now()
        if now < promo.valid_from:
            return {
                'valid': False,
                'error': f'Este codigo sera valido a partir de {promo.valid_from.strftime("%d/%m/%Y")}',
                'error_code': 'NOT_YET_VALID'
            }
        if now > promo.valid_until:
            return {
                'valid': False,
                'error': 'Este codigo ha expirado',
                'error_code': 'EXPIRED'
            }

        # Check total usage limit
        if promo.max_uses and promo.current_uses >= promo.max_uses:
            return {
                'valid': False,
                'error': 'Este codigo ha alcanzado su limite de usos',
                'error_code': 'DEPLETED'
            }

        # Check user usage limit
        user_usage_count = PromoCodeUsage.objects.filter(
            promo_code=promo,
            user=user
        ).count()
        if user_usage_count >= promo.max_uses_per_user:
            return {
                'valid': False,
                'error': 'Ya has utilizado este codigo el numero maximo de veces',
                'error_code': 'USER_LIMIT_REACHED'
            }

        # Check first purchase only restriction
        if promo.first_purchase_only:
            has_previous_purchase = UserService.objects.filter(user=user).exists()
            if has_previous_purchase:
                return {
                    'valid': False,
                    'error': 'Este codigo es solo para primera compra',
                    'error_code': 'NOT_FIRST_PURCHASE'
                }

        # Check new users only restriction
        if promo.new_users_only:
            # Consider users registered within last 7 days as "new"
            from datetime import timedelta
            new_user_cutoff = timezone.now() - timedelta(days=7)
            if user.date_joined < new_user_cutoff:
                return {
                    'valid': False,
                    'error': 'Este codigo es solo para usuarios nuevos',
                    'error_code': 'NOT_NEW_USER'
                }

        # Check plan restrictions
        if plan and promo.applicable_plans.exists():
            if not promo.applicable_plans.filter(id=plan.id).exists():
                return {
                    'valid': False,
                    'error': 'Este codigo no es valido para el plan seleccionado',
                    'error_code': 'PLAN_NOT_APPLICABLE'
                }

        # Check minimum purchase
        purchase_amount = amount or (plan.price if plan else Decimal('0'))
        if purchase_amount < promo.minimum_purchase:
            return {
                'valid': False,
                'error': f'Compra minima requerida: Q{promo.minimum_purchase}',
                'error_code': 'MINIMUM_NOT_MET'
            }

        # Calculate discount
        discount_amount = promo.calculate_discount(purchase_amount)
        final_price = purchase_amount - discount_amount

        return {
            'valid': True,
            'promo_code': {
                'code': promo.code,
                'name': promo.name,
                'description': promo.description,
                'discount_type': promo.discount_type,
                'discount_value': float(promo.discount_value),
            },
            'original_price': float(purchase_amount),
            'discount_amount': float(discount_amount),
            'final_price': float(max(Decimal('0'), final_price)),
            'currency': 'GTQ'
        }

    @classmethod
    @transaction.atomic
    def apply_code(
        cls,
        code: str,
        user: User,
        original_price: Decimal,
        user_service: Optional[UserService] = None,
        wallet_transaction=None
    ) -> Dict[str, Any]:
        """
        Apply a promo code and record its usage.

        Args:
            code: The promo code string
            user: The user using the code
            original_price: Original price before discount
            user_service: Optional linked user service
            wallet_transaction: Optional linked wallet transaction

        Returns:
            Dictionary with application result
        """
        # Validate first
        validation = cls.validate_code(code, user, amount=original_price)
        if not validation['valid']:
            return validation

        try:
            promo = PromoCode.objects.select_for_update().get(code__iexact=code.strip())
        except PromoCode.DoesNotExist:
            return {'valid': False, 'error': 'Codigo no encontrado'}

        # Calculate discount
        discount_amount = promo.calculate_discount(original_price)
        final_price = original_price - discount_amount

        # Record usage
        usage = PromoCodeUsage.objects.create(
            promo_code=promo,
            user=user,
            transaction=wallet_transaction,
            user_service=user_service,
            original_price=original_price,
            discount_amount=discount_amount,
            final_price=final_price
        )

        # Increment usage count ATOMICALLY to prevent race conditions
        PromoCode.objects.filter(id=promo.id).update(
            current_uses=F('current_uses') + 1
        )

        # Refresh to get updated count and check if depleted
        promo.refresh_from_db()
        if promo.max_uses and promo.current_uses >= promo.max_uses:
            promo.status = PromoCode.Status.DEPLETED
            promo.save(update_fields=['status'])

        logger.info(
            f'Promo code {promo.code} applied by {user.email}: '
            f'discount Q{discount_amount} on Q{original_price}'
        )

        return {
            'success': True,
            'usage_id': usage.id,
            'original_price': float(original_price),
            'discount_amount': float(discount_amount),
            'final_price': float(final_price),
            'promo_code': promo.code,
            'currency': 'GTQ'
        }

    @classmethod
    def get_available_codes_for_user(cls, user: User) -> list:
        """
        Get list of active promo codes available to a user.
        Includes:
        - General public promo codes the user can use
        - Personal promo codes from e-learning rewards

        Args:
            user: The user to check codes for

        Returns:
            List of available promo codes
        """
        now = timezone.now()
        available = []
        seen_codes = set()

        # First, get user's personal promo codes from e-learning rewards
        try:
            from apps.gamification.models import UserReward
            user_rewards = UserReward.objects.filter(
                user=user,
                promo_code__isnull=False
            ).select_related('promo_code')

            for reward in user_rewards:
                code = reward.promo_code
                if code.code in seen_codes:
                    continue
                seen_codes.add(code.code)

                # Check if code is still valid and usable
                is_used = PromoCodeUsage.objects.filter(
                    promo_code=code,
                    user=user
                ).exists()

                is_valid = (
                    code.status == PromoCode.Status.ACTIVE and
                    code.valid_from <= now <= code.valid_until and
                    (not code.max_uses or code.current_uses < code.max_uses)
                )

                available.append({
                    'id': code.id,
                    'code': code.code,
                    'name': code.name,
                    'description': code.description,
                    'discount_type': code.discount_type,
                    'discount_value': float(code.discount_value),
                    'valid_until': code.valid_until.isoformat(),
                    'minimum_purchase': float(code.minimum_purchase),
                    'remaining_uses': 0 if is_used else 1,
                    'is_used': is_used,
                    'source': 'E-Learning',
                    'reward_type': reward.reward_type,
                    'is_valid': is_valid and not is_used
                })
        except Exception as e:
            logger.warning(f'Error fetching user rewards: {e}')

        # Then, get general public promo codes
        public_codes = PromoCode.objects.filter(
            status=PromoCode.Status.ACTIVE,
            valid_from__lte=now,
            valid_until__gte=now
        ).exclude(code__in=seen_codes)

        for code in public_codes:
            # Skip codes that are single-use and created for specific users (e-learning)
            # These have patterns like PTS100-, ACH-, EDU-
            if code.max_uses == 1 and any(code.code.startswith(p) for p in ['PTS', 'ACH-', 'EDU-']):
                continue

            # Check user usage
            user_usage = PromoCodeUsage.objects.filter(
                promo_code=code,
                user=user
            ).count()

            if user_usage < code.max_uses_per_user:
                # Check total usage
                if not code.max_uses or code.current_uses < code.max_uses:
                    available.append({
                        'id': code.id,
                        'code': code.code,
                        'name': code.name,
                        'description': code.description,
                        'discount_type': code.discount_type,
                        'discount_value': float(code.discount_value),
                        'valid_until': code.valid_until.isoformat(),
                        'minimum_purchase': float(code.minimum_purchase),
                        'remaining_uses': code.max_uses_per_user - user_usage,
                        'is_used': False,
                        'source': 'Promocion',
                        'is_valid': True
                    })

        return available


# Convenience functions
validate_promo_code = PromoCodeService.validate_code
apply_promo_code = PromoCodeService.apply_code
