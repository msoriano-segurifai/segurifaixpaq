"""
Automated Rewards System for Gamification

Automatically generates promo codes when users reach point milestones
through educational modules.
"""
import uuid
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List

from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


# Point thresholds and their rewards (conservative for MVP)
POINT_REWARDS = {
    100: {
        'name': 'Recompensa Aprendiz',
        'description': '2% de descuento por alcanzar 100 puntos',
        'discount_type': 'PERCENTAGE',
        'discount_value': Decimal('2.00'),
        'valid_days': 30,
        'level': 'APRENDIZ',
    },
    250: {
        'name': 'Recompensa Conocedor',
        'description': '3% de descuento por alcanzar 250 puntos',
        'discount_type': 'PERCENTAGE',
        'discount_value': Decimal('3.00'),
        'valid_days': 30,
        'level': 'CONOCEDOR',
    },
    500: {
        'name': 'Recompensa Experto',
        'description': '5% de descuento por alcanzar 500 puntos',
        'discount_type': 'PERCENTAGE',
        'discount_value': Decimal('5.00'),
        'valid_days': 45,
        'level': 'EXPERTO',
    },
    1000: {
        'name': 'Recompensa Maestro',
        'description': '7% de descuento por alcanzar 1000 puntos',
        'discount_type': 'PERCENTAGE',
        'discount_value': Decimal('7.00'),
        'max_discount': Decimal('50.00'),
        'valid_days': 60,
        'level': 'MAESTRO',
    },
}

# Special achievement rewards (conservative for MVP)
ACHIEVEMENT_REWARDS = {
    'first_module': {
        'name': 'Primer Paso',
        'description': 'Q5 de descuento por completar tu primer modulo',
        'discount_type': 'FIXED_AMOUNT',
        'discount_value': Decimal('5.00'),
        'valid_days': 14,
    },
    'perfect_quiz': {
        'name': 'Quiz Perfecto',
        'description': '2% extra por responder todo correctamente',
        'discount_type': 'PERCENTAGE',
        'discount_value': Decimal('2.00'),
        'valid_days': 7,
    },
    'streak_7_days': {
        'name': 'Racha Semanal',
        'description': 'Q5 de descuento por 7 dias consecutivos',
        'discount_type': 'FIXED_AMOUNT',
        'discount_value': Decimal('5.00'),
        'valid_days': 14,
    },
    'all_modules': {
        'name': 'Graduado SegurifAI',
        'description': '10% de descuento por completar todos los modulos',
        'discount_type': 'PERCENTAGE',
        'discount_value': Decimal('10.00'),
        'valid_days': 45,
    },
}


class RewardsService:
    """
    Service for managing automated rewards based on gamification progress.
    """

    @classmethod
    def generate_promo_code(cls, prefix: str = 'EDU') -> str:
        """Generate a unique promo code"""
        unique_part = uuid.uuid4().hex[:8].upper()
        return f'{prefix}-{unique_part}'

    @classmethod
    @transaction.atomic
    def check_and_award_point_rewards(cls, user) -> List[Dict[str, Any]]:
        """
        Check if user has reached any point thresholds and award promo codes.

        Args:
            user: User instance

        Returns:
            List of awarded rewards
        """
        from .models import UserPoints
        from apps.promotions.models import PromoCode

        awarded = []

        try:
            user_points = UserPoints.objects.get(user=user)
        except UserPoints.DoesNotExist:
            return awarded

        # Get user's already claimed reward thresholds
        claimed_thresholds = cls._get_claimed_thresholds(user)

        # Check each threshold
        for threshold, reward_config in POINT_REWARDS.items():
            if user_points.puntos_totales >= threshold and threshold not in claimed_thresholds:
                # Award this reward
                promo_code = cls._create_reward_promo_code(
                    user=user,
                    reward_config=reward_config,
                    threshold=threshold
                )

                if promo_code:
                    awarded.append({
                        'threshold': threshold,
                        'level': reward_config['level'],
                        'promo_code': promo_code.code,
                        'discount': f"{reward_config['discount_value']}%",
                        'valid_until': promo_code.valid_until.isoformat(),
                        'message': f"Felicidades! Has alcanzado {threshold} puntos y desbloqueaste: {reward_config['name']}"
                    })

                    logger.info(f'Awarded {reward_config["name"]} to {user.email} for reaching {threshold} points')

        return awarded

    @classmethod
    @transaction.atomic
    def award_achievement_reward(cls, user, achievement_key: str) -> Optional[Dict[str, Any]]:
        """
        Award a promo code for a specific achievement.

        Args:
            user: User instance
            achievement_key: Key from ACHIEVEMENT_REWARDS

        Returns:
            Reward info dict or None
        """
        if achievement_key not in ACHIEVEMENT_REWARDS:
            return None

        # Check if already awarded
        if cls._has_achievement_reward(user, achievement_key):
            return None

        reward_config = ACHIEVEMENT_REWARDS[achievement_key]

        promo_code = cls._create_achievement_promo_code(
            user=user,
            achievement_key=achievement_key,
            reward_config=reward_config
        )

        if promo_code:
            logger.info(f'Awarded achievement "{achievement_key}" to {user.email}')
            return {
                'achievement': achievement_key,
                'promo_code': promo_code.code,
                'name': reward_config['name'],
                'discount': str(reward_config['discount_value']),
                'discount_type': reward_config['discount_type'],
                'valid_until': promo_code.valid_until.isoformat(),
                'message': reward_config['description']
            }

        return None

    @classmethod
    def _create_reward_promo_code(cls, user, reward_config: dict, threshold: int):
        """Create a promo code for a point threshold reward"""
        from apps.promotions.models import PromoCode

        now = timezone.now()
        valid_until = now + timedelta(days=reward_config['valid_days'])

        code = cls.generate_promo_code(f'PTS{threshold}')

        promo_code = PromoCode.objects.create(
            code=code,
            name=f"{reward_config['name']} - {user.email}",
            description=reward_config['description'],
            discount_type=reward_config['discount_type'],
            discount_value=reward_config['discount_value'],
            max_discount_amount=reward_config.get('max_discount'),
            max_uses=1,
            max_uses_per_user=1,
            valid_from=now,
            valid_until=valid_until,
            status='ACTIVE',
            created_by=None,  # System generated
        )

        # Track that this threshold was claimed
        cls._mark_threshold_claimed(user, threshold, promo_code)

        return promo_code

    @classmethod
    def _create_achievement_promo_code(cls, user, achievement_key: str, reward_config: dict):
        """Create a promo code for an achievement reward"""
        from apps.promotions.models import PromoCode

        now = timezone.now()
        valid_until = now + timedelta(days=reward_config['valid_days'])

        code = cls.generate_promo_code(f'ACH-{achievement_key[:4].upper()}')

        promo_code = PromoCode.objects.create(
            code=code,
            name=f"{reward_config['name']} - {user.email}",
            description=reward_config['description'],
            discount_type=reward_config['discount_type'],
            discount_value=reward_config['discount_value'],
            max_uses=1,
            max_uses_per_user=1,
            valid_from=now,
            valid_until=valid_until,
            status='ACTIVE',
            created_by=None,
        )

        cls._mark_achievement_claimed(user, achievement_key, promo_code)

        return promo_code

    @classmethod
    def _get_claimed_thresholds(cls, user) -> set:
        """Get set of point thresholds user has already claimed"""
        from .models import UserReward
        try:
            rewards = UserReward.objects.filter(
                user=user,
                reward_type='POINT_THRESHOLD'
            ).values_list('threshold', flat=True)
            return set(rewards)
        except Exception:
            return set()

    @classmethod
    def _mark_threshold_claimed(cls, user, threshold: int, promo_code):
        """Mark a threshold as claimed"""
        from .models import UserReward
        UserReward.objects.create(
            user=user,
            reward_type='POINT_THRESHOLD',
            threshold=threshold,
            promo_code=promo_code,
            reward_data={'level': POINT_REWARDS[threshold]['level']}
        )

    @classmethod
    def _has_achievement_reward(cls, user, achievement_key: str) -> bool:
        """Check if user already has this achievement reward"""
        from .models import UserReward
        return UserReward.objects.filter(
            user=user,
            reward_type='ACHIEVEMENT',
            achievement_key=achievement_key
        ).exists()

    @classmethod
    def _mark_achievement_claimed(cls, user, achievement_key: str, promo_code):
        """Mark an achievement as claimed"""
        from .models import UserReward
        UserReward.objects.create(
            user=user,
            reward_type='ACHIEVEMENT',
            achievement_key=achievement_key,
            promo_code=promo_code,
            reward_data=ACHIEVEMENT_REWARDS[achievement_key]
        )

    @classmethod
    def get_user_rewards(cls, user) -> Dict[str, Any]:
        """
        Get all rewards status for a user.

        Returns:
            Dict with available, claimed, and upcoming rewards
        """
        from .models import UserPoints, UserReward
        from apps.promotions.models import PromoCode

        try:
            user_points = UserPoints.objects.get(user=user)
            current_points = user_points.puntos_totales
        except UserPoints.DoesNotExist:
            current_points = 0

        claimed = list(UserReward.objects.filter(user=user).select_related('promo_code'))

        # Build response
        result = {
            'current_points': current_points,
            'current_level': user_points.nivel if user_points else 'NOVATO',
            'claimed_rewards': [],
            'available_rewards': [],
            'upcoming_rewards': [],
            'active_promo_codes': [],
        }

        # Get claimed reward codes
        claimed_thresholds = set()
        claimed_achievements = set()

        for reward in claimed:
            claimed_data = {
                'type': reward.reward_type,
                'claimed_at': reward.created_at.isoformat(),
            }

            if reward.reward_type == 'POINT_THRESHOLD':
                claimed_thresholds.add(reward.threshold)
                claimed_data['threshold'] = reward.threshold
                claimed_data['level'] = reward.reward_data.get('level')
            else:
                claimed_achievements.add(reward.achievement_key)
                claimed_data['achievement'] = reward.achievement_key

            if reward.promo_code:
                claimed_data['promo_code'] = reward.promo_code.code
                claimed_data['promo_code_status'] = reward.promo_code.status
                claimed_data['valid_until'] = reward.promo_code.valid_until.isoformat()

                # Check if still active
                if reward.promo_code.is_valid:
                    result['active_promo_codes'].append({
                        'code': reward.promo_code.code,
                        'name': reward.promo_code.name,
                        'discount': f"{reward.promo_code.discount_value}{'%' if reward.promo_code.discount_type == 'PERCENTAGE' else ' GTQ'}",
                        'valid_until': reward.promo_code.valid_until.isoformat(),
                    })

            result['claimed_rewards'].append(claimed_data)

        # Check upcoming point rewards
        for threshold, config in POINT_REWARDS.items():
            if threshold in claimed_thresholds:
                continue

            if current_points >= threshold:
                # Available to claim
                result['available_rewards'].append({
                    'type': 'POINT_THRESHOLD',
                    'threshold': threshold,
                    'level': config['level'],
                    'name': config['name'],
                    'discount': f"{config['discount_value']}%",
                    'message': f"Disponible! Has alcanzado {threshold} puntos"
                })
            else:
                # Upcoming
                points_needed = threshold - current_points
                result['upcoming_rewards'].append({
                    'type': 'POINT_THRESHOLD',
                    'threshold': threshold,
                    'level': config['level'],
                    'name': config['name'],
                    'discount': f"{config['discount_value']}%",
                    'points_needed': points_needed,
                    'progress_percent': int((current_points / threshold) * 100)
                })

        return result

    @classmethod
    def process_quiz_completion(cls, user, progress) -> List[Dict[str, Any]]:
        """
        Process rewards after quiz completion.

        Called after user completes a module quiz.

        Args:
            user: User instance
            progress: UserProgress instance

        Returns:
            List of awarded rewards
        """
        from .models import UserPoints, UserProgress

        rewards = []

        # Check point threshold rewards
        point_rewards = cls.check_and_award_point_rewards(user)
        rewards.extend(point_rewards)

        # Check for first module achievement
        completed_count = UserProgress.objects.filter(
            user=user,
            estado='COMPLETADO'
        ).count()

        if completed_count == 1:
            first_module_reward = cls.award_achievement_reward(user, 'first_module')
            if first_module_reward:
                rewards.append(first_module_reward)

        # Check for perfect quiz
        if progress.respuestas_correctas == progress.total_preguntas and progress.total_preguntas > 0:
            perfect_reward = cls.award_achievement_reward(user, 'perfect_quiz')
            if perfect_reward:
                rewards.append(perfect_reward)

        # Check for all modules completed
        from .models import EducationalModule
        total_modules = EducationalModule.objects.filter(activo=True).count()
        if completed_count >= total_modules and total_modules > 0:
            all_modules_reward = cls.award_achievement_reward(user, 'all_modules')
            if all_modules_reward:
                rewards.append(all_modules_reward)

        # Check streak
        try:
            user_points = UserPoints.objects.get(user=user)
            if user_points.racha_dias >= 7:
                streak_reward = cls.award_achievement_reward(user, 'streak_7_days')
                if streak_reward:
                    rewards.append(streak_reward)
        except UserPoints.DoesNotExist:
            pass

        return rewards
