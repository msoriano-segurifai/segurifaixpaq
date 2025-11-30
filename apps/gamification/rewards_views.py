"""
Rewards API Views for Gamification

Endpoints for viewing and claiming rewards based on educational progress.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .rewards import RewardsService, POINT_REWARDS, ACHIEVEMENT_REWARDS


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_rewards(request):
    """
    Get user's rewards status and available promo codes.

    GET /api/educacion/rewards/

    Returns:
    - Current points and level
    - Claimed rewards with promo codes
    - Available rewards ready to claim
    - Upcoming rewards and progress
    - Active (unused) promo codes
    """
    rewards_data = RewardsService.get_user_rewards(request.user)
    return Response(rewards_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claim_available_rewards(request):
    """
    Claim all available point threshold rewards.

    POST /api/educacion/rewards/claim/

    Automatically generates promo codes for any unclaimed
    point thresholds the user has reached.
    """
    awarded = RewardsService.check_and_award_point_rewards(request.user)

    if awarded:
        return Response({
            'success': True,
            'message': f'Has desbloqueado {len(awarded)} recompensas!',
            'rewards': awarded
        })
    else:
        return Response({
            'success': True,
            'message': 'No hay recompensas nuevas disponibles',
            'rewards': []
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rewards_tiers(request):
    """
    Get all available reward tiers and achievements.

    GET /api/educacion/rewards/tiers/

    Returns the reward structure so users know what to work towards.
    """
    tiers = []
    for threshold, config in POINT_REWARDS.items():
        tiers.append({
            'type': 'POINT_THRESHOLD',
            'threshold': threshold,
            'level': config['level'],
            'name': config['name'],
            'description': config['description'],
            'discount': f"{config['discount_value']}%",
            'valid_days': config['valid_days'],
        })

    achievements = []
    for key, config in ACHIEVEMENT_REWARDS.items():
        achievements.append({
            'type': 'ACHIEVEMENT',
            'key': key,
            'name': config['name'],
            'description': config['description'],
            'discount_type': config['discount_type'],
            'discount_value': str(config['discount_value']),
            'valid_days': config['valid_days'],
        })

    return Response({
        'point_tiers': tiers,
        'achievement_rewards': achievements
    })
