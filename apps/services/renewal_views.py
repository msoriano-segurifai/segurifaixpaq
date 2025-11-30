"""
Subscription Renewal API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import UserService
from .renewal import SubscriptionRenewalService
from apps.users.permissions import IsAdmin


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_renewal_status(request, subscription_id):
    """
    Get renewal status for a subscription.

    GET /api/services/renewal/<subscription_id>/status/
    """
    user_service = get_object_or_404(UserService, id=subscription_id)

    # Check user has access
    if not request.user.is_admin and user_service.user != request.user:
        return Response(
            {'error': 'No tiene permiso para ver esta suscripcion'},
            status=status.HTTP_403_FORBIDDEN
        )

    renewal_status = SubscriptionRenewalService.get_renewal_status(user_service)

    return Response(renewal_status)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_auto_renew(request, subscription_id):
    """
    Toggle auto-renewal for a subscription.

    POST /api/services/renewal/<subscription_id>/auto-renew/

    Body:
    {
        "auto_renew": true
    }
    """
    user_service = get_object_or_404(UserService, id=subscription_id)

    # Check user has access
    if not request.user.is_admin and user_service.user != request.user:
        return Response(
            {'error': 'No tiene permiso para modificar esta suscripcion'},
            status=status.HTTP_403_FORBIDDEN
        )

    auto_renew = request.data.get('auto_renew')
    if auto_renew is None:
        return Response(
            {'error': 'auto_renew is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user_service.auto_renew = bool(auto_renew)
    user_service.save()

    return Response({
        'success': True,
        'auto_renew': user_service.auto_renew,
        'message': f'Renovacion automatica {"activada" if user_service.auto_renew else "desactivada"}'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_renewal(request, subscription_id):
    """
    Manually initiate subscription renewal.

    POST /api/services/renewal/<subscription_id>/renew/

    Returns payment token for completing renewal.
    """
    user_service = get_object_or_404(UserService, id=subscription_id)

    # Check user has access
    if not request.user.is_admin and user_service.user != request.user:
        return Response(
            {'error': 'No tiene permiso para renovar esta suscripcion'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Check if can renew
    if user_service.status not in ['ACTIVE', 'EXPIRED']:
        return Response(
            {'error': 'Esta suscripcion no puede ser renovada'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get renewal status first
    renewal_status = SubscriptionRenewalService.get_renewal_status(user_service)

    # Initiate renewal (with credits applied automatically)
    result = SubscriptionRenewalService.renew_subscription(user_service)

    # Always return 200 with renewal info - manual payment is valid scenario
    if result.get('success'):
        return Response({
            'success': True,
            'message': result.get('message', 'Renovacion iniciada'),
            'renewal_info': renewal_status,
            'payment_details': {
                'original_price': result.get('original_price'),
                'credits_applied': result.get('credits_applied'),
                'final_price': result.get('final_price'),
                'paid_with_credits': result.get('paid_with_credits', False),
                'token': result.get('token'),
                'reference': result.get('reference'),
                'currency': 'GTQ'
            }
        })
    else:
        # Manual renewal required - still return 200 with renewal info
        return Response({
            'success': True,
            'requires_manual_payment': True,
            'message': 'Pago manual requerido para completar renovacion',
            'renewal_info': renewal_status,
            'payment_details': {
                'original_price': result.get('original_price'),
                'credits_applied': result.get('credits_applied'),
                'final_price': result.get('final_price'),
                'currency': 'GTQ'
            }
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_subscriptions_renewal(request):
    """
    Get renewal status for all user's subscriptions.

    GET /api/services/renewal/my/
    """
    subscriptions = UserService.objects.filter(
        user=request.user
    ).select_related('plan')

    renewal_statuses = [
        SubscriptionRenewalService.get_renewal_status(sub)
        for sub in subscriptions
    ]

    return Response({
        'subscriptions': renewal_statuses,
        'count': len(renewal_statuses)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_expiring_subscriptions(request):
    """
    Get list of subscriptions expiring soon (admin only).

    GET /api/services/renewal/expiring/
    Query params:
    - days: Number of days to look ahead (default: 7)
    """
    days = int(request.query_params.get('days', 7))

    expiring = SubscriptionRenewalService.get_expiring_subscriptions(days=days)

    return Response({
        'days': days,
        'count': len(expiring),
        'subscriptions': [
            {
                'id': sub.id,
                'user_email': sub.user.email,
                'plan_name': sub.plan.name if sub.plan else None,
                'end_date': sub.end_date.isoformat() if sub.end_date else None,
                'auto_renew': sub.auto_renew
            }
            for sub in expiring
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def run_renewal_tasks(request):
    """
    Manually trigger renewal tasks (admin only).

    POST /api/services/renewal/run-tasks/

    This runs:
    1. Send renewal reminders
    2. Process auto-renewals
    3. Mark expired subscriptions
    """
    from .renewal import daily_renewal_tasks

    results = daily_renewal_tasks()

    return Response({
        'success': True,
        'message': 'Tareas de renovacion ejecutadas',
        'results': results
    })
