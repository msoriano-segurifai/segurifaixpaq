"""
Subscription Renewal Service

Handles automatic renewal, renewal reminders, and subscription lifecycle management.
"""
import logging
from datetime import timedelta
from decimal import Decimal
from typing import List, Optional

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from .models import UserService, ServicePlan
from apps.users.models import User
from apps.paq_wallet.models import WalletTransaction
from apps.paq_wallet.services import paq_wallet_service
from apps.gamification.models import UserDiscountCredits

logger = logging.getLogger(__name__)


class SubscriptionRenewalService:
    """Service for handling subscription renewals"""

    # Reminder intervals (days before expiry)
    REMINDER_DAYS = [7, 3, 1]

    @classmethod
    def get_expiring_subscriptions(cls, days: int = 7) -> List[UserService]:
        """
        Get subscriptions expiring within the specified days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of UserService objects expiring soon
        """
        expiry_date = timezone.now().date() + timedelta(days=days)
        today = timezone.now().date()

        return list(UserService.objects.filter(
            status='ACTIVE',
            end_date__gte=today,
            end_date__lte=expiry_date
        ).select_related('user', 'plan'))

    @classmethod
    def get_expired_subscriptions(cls) -> List[UserService]:
        """
        Get subscriptions that have expired but not yet marked.

        Returns:
            List of expired UserService objects
        """
        today = timezone.now().date()

        return list(UserService.objects.filter(
            status='ACTIVE',
            end_date__lt=today
        ).select_related('user', 'plan'))

    @classmethod
    def send_renewal_reminders(cls) -> dict:
        """
        Send renewal reminder emails to users with expiring subscriptions.

        Returns:
            Dictionary with sent counts and errors
        """
        results = {
            'sent': 0,
            'errors': [],
            'by_days': {}
        }

        for days in cls.REMINDER_DAYS:
            target_date = timezone.now().date() + timedelta(days=days)

            # Get subscriptions expiring on this exact date
            expiring = UserService.objects.filter(
                status='ACTIVE',
                end_date=target_date,
                auto_renew=False  # Only remind non-auto-renew users
            ).select_related('user', 'plan')

            sent_count = 0
            for subscription in expiring:
                try:
                    # Log reminder (email notifications removed)
                    logger.info(
                        f'{days}-day renewal reminder for {subscription.user.email} '
                        f'- Plan: {subscription.plan.name}'
                    )
                    sent_count += 1
                except Exception as e:
                    error_msg = f'Failed to process reminder for {subscription.user.email}: {e}'
                    results['errors'].append(error_msg)
                    logger.error(error_msg)

            results['by_days'][days] = sent_count
            results['sent'] += sent_count

        return results

    @classmethod
    def process_auto_renewals(cls) -> dict:
        """
        Process automatic renewals for subscriptions expiring today.

        Returns:
            Dictionary with renewal results
        """
        results = {
            'renewed': 0,
            'failed': 0,
            'errors': []
        }

        today = timezone.now().date()

        # Get auto-renew subscriptions expiring today
        expiring = UserService.objects.filter(
            status='ACTIVE',
            end_date=today,
            auto_renew=True
        ).select_related('user', 'plan')

        for subscription in expiring:
            try:
                result = cls.renew_subscription(subscription)
                if result.get('success'):
                    results['renewed'] += 1
                    logger.info(f'Auto-renewed subscription for {subscription.user.email}')
                else:
                    results['failed'] += 1
                    results['errors'].append(result.get('error', 'Unknown error'))
            except Exception as e:
                results['failed'] += 1
                error_msg = f'Auto-renewal failed for {subscription.user.email}: {e}'
                results['errors'].append(error_msg)
                logger.error(error_msg)

        return results

    @classmethod
    @transaction.atomic
    def renew_subscription(cls, user_service: UserService, payment_method: str = 'PAQ', apply_credits: bool = True) -> dict:
        """
        Renew a single subscription with optional credit application.

        Args:
            user_service: The subscription to renew
            payment_method: Payment method to use
            apply_credits: Whether to apply accumulated e-learning credits

        Returns:
            dict: Renewal result with success status and details
        """
        plan = user_service.plan
        user = user_service.user

        if not plan:
            logger.error(f'No plan found for subscription {user_service.id}')
            return {'success': False, 'error': 'No plan found'}

        # Calculate new dates
        new_start = user_service.end_date + timedelta(days=1)
        new_end = new_start + timedelta(days=plan.duration_days)

        # Get subscription price
        original_price = plan.price
        credits_applied = Decimal('0')
        final_price = original_price

        # Apply e-learning discount credits if enabled
        if apply_credits:
            try:
                user_credits = UserDiscountCredits.objects.get(user=user)
                if user_credits.saldo_disponible > 0:
                    # Apply credits (capped at subscription price)
                    credits_applied = user_credits.usar_credito(
                        monto_maximo=user_credits.saldo_disponible,
                        monto_suscripcion=original_price
                    )
                    final_price = original_price - credits_applied
                    logger.info(
                        f'Applied Q{credits_applied} credits for {user.email} '
                        f'(original: Q{original_price}, final: Q{final_price})'
                    )
            except UserDiscountCredits.DoesNotExist:
                pass  # No credits available

        # Generate payment reference
        import uuid
        reference = f'RENEW-{uuid.uuid4().hex[:8].upper()}'

        # Create pending transaction (store original and final prices)
        transaction_record = WalletTransaction.objects.create(
            user=user,
            transaction_type='PAYMENT',
            amount=final_price,  # Charge the discounted amount
            currency='GTQ',
            reference_number=reference,
            user_service=user_service,
            status='PENDING',
            status_message=f'Renewal for {plan.name}',
            metadata={
                'original_price': float(original_price),
                'credits_applied': float(credits_applied),
                'final_price': float(final_price)
            }
        )

        # If credits covered the full amount, complete immediately
        if final_price <= 0:
            transaction_record.status = 'COMPLETED'
            transaction_record.completed_at = timezone.now()
            transaction_record.status_message = f'Pagado con creditos de e-learning'
            transaction_record.save()

            # Update subscription dates
            user_service.start_date = new_start
            user_service.end_date = new_end
            user_service.status = 'ACTIVE'
            user_service.save()

            logger.info(f'Subscription renewed with credits only for {user.email}')
            return {
                'success': True,
                'paid_with_credits': True,
                'original_price': float(original_price),
                'credits_applied': float(credits_applied),
                'final_price': 0,
                'message': 'Suscripcion renovada con tus creditos de e-learning'
            }

        # For auto-renewal with PAQ Wallet, generate token
        if payment_method == 'PAQ' and user.paq_wallet_id:
            result = paq_wallet_service.emite_token(
                monto=final_price,  # Use discounted price
                referencia=reference,
                horas_vigencia=24,
                cliente_celular=user.phone_number,
                cliente_email=user.email,
                descripcion=f'Renovacion de {plan.name}' + (f' (Q{credits_applied} creditos aplicados)' if credits_applied > 0 else ''),
                cliente_nombre=user.get_full_name()
            )

            if result['success']:
                transaction_record.external_transaction_id = str(result.get('transaccion', ''))
                transaction_record.metadata.update({
                    'token': result.get('token'),
                    'renewal': True
                })
                transaction_record.save()

                # Note: Payment completion will be handled by webhook or user action
                logger.info(f'Renewal token generated for {user.email}: {result.get("token")}')
                return {
                    'success': True,
                    'token': result.get('token'),
                    'transaccion': result.get('transaccion'),
                    'original_price': float(original_price),
                    'credits_applied': float(credits_applied),
                    'final_price': float(final_price),
                    'reference': reference,
                    'message': f'Token generado. Paga Q{final_price} para renovar.' if credits_applied > 0 else 'Token generado'
                }
            else:
                transaction_record.status = 'FAILED'
                transaction_record.status_message = result.get('mensaje', 'Token generation failed')
                transaction_record.save()
                return {'success': False, 'error': result.get('mensaje', 'Token generation failed')}
        else:
            # Manual renewal required
            transaction_record.status_message = 'Manual renewal required'
            transaction_record.save()
            return {
                'success': False,
                'error': 'Manual renewal required',
                'original_price': float(original_price),
                'credits_applied': float(credits_applied),
                'final_price': float(final_price)
            }

    @classmethod
    def mark_expired_subscriptions(cls) -> int:
        """
        Mark expired subscriptions as inactive.

        Returns:
            Number of subscriptions marked as expired
        """
        today = timezone.now().date()

        # Get grace period from settings (default 3 days)
        grace_days = getattr(settings, 'SUBSCRIPTION_GRACE_DAYS', 3)
        grace_date = today - timedelta(days=grace_days)

        expired = UserService.objects.filter(
            status='ACTIVE',
            end_date__lt=grace_date
        )

        count = expired.count()
        expired.update(status='EXPIRED')

        if count > 0:
            logger.info(f'Marked {count} subscriptions as expired')

        return count

    @classmethod
    def get_renewal_status(cls, user_service: UserService) -> dict:
        """
        Get renewal status for a subscription, including available credits.

        Args:
            user_service: The subscription to check

        Returns:
            Dictionary with renewal status information
        """
        today = timezone.now().date()
        days_remaining = (user_service.end_date - today).days if user_service.end_date else 0
        user = user_service.user
        plan = user_service.plan

        # Get original price
        original_price = float(plan.price) if plan else 0

        # Check for available e-learning credits
        available_credits = 0
        credits_applicable = 0
        final_price = original_price

        try:
            user_credits = UserDiscountCredits.objects.get(user=user)
            available_credits = float(user_credits.saldo_disponible)
            # Credits can't exceed subscription price
            credits_applicable = min(available_credits, original_price)
            final_price = max(0, original_price - credits_applicable)
        except UserDiscountCredits.DoesNotExist:
            pass

        return {
            'subscription_id': user_service.id,
            'plan_name': plan.name if plan else None,
            'status': user_service.status,
            'end_date': user_service.end_date.isoformat() if user_service.end_date else None,
            'days_remaining': max(0, days_remaining),
            'is_expiring_soon': 0 < days_remaining <= 7,
            'is_expired': days_remaining < 0,
            'auto_renew': user_service.auto_renew,
            'can_renew': user_service.status in ['ACTIVE', 'EXPIRED'],
            'pricing': {
                'original_price': original_price,
                'available_credits': available_credits,
                'credits_applicable': credits_applicable,
                'final_price': final_price,
                'currency': 'GTQ',
                'can_pay_with_credits_only': final_price == 0
            }
        }


# Celery tasks (if using Celery)
def daily_renewal_tasks():
    """
    Daily tasks for subscription management.
    Call this from a scheduler (Celery beat, cron, etc.)
    """
    service = SubscriptionRenewalService

    # 1. Send renewal reminders
    reminder_results = service.send_renewal_reminders()
    logger.info(f'Renewal reminders sent: {reminder_results}')

    # 2. Process auto-renewals
    renewal_results = service.process_auto_renewals()
    logger.info(f'Auto-renewals processed: {renewal_results}')

    # 3. Mark expired subscriptions
    expired_count = service.mark_expired_subscriptions()
    logger.info(f'Expired subscriptions marked: {expired_count}')

    return {
        'reminders': reminder_results,
        'renewals': renewal_results,
        'expired': expired_count
    }
