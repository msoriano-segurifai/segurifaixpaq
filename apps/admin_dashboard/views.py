"""
Admin Dashboard API Views

Provides statistics, reports, and management endpoints for administrators.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.models import User
from apps.users.permissions import IsAdmin
from apps.services.models import UserService, ServicePlan, ServiceCategory
from apps.assistance.models import AssistanceRequest
from apps.providers.models import Provider
from apps.paq_wallet.models import WalletTransaction


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def dashboard_overview(request):
    """
    Get overview statistics for admin dashboard.

    GET /api/admin/dashboard/overview/

    Returns summary statistics for users, subscriptions, requests, revenue.
    """
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())

    # User statistics
    total_users = User.objects.filter(role='USER').count()
    new_users_today = User.objects.filter(
        role='USER',
        date_joined__date=today
    ).count()
    new_users_week = User.objects.filter(
        role='USER',
        date_joined__date__gte=start_of_week
    ).count()
    new_users_month = User.objects.filter(
        role='USER',
        date_joined__date__gte=start_of_month
    ).count()

    # Subscription statistics
    active_subscriptions = UserService.objects.filter(status='ACTIVE').count()
    expiring_soon = UserService.objects.filter(
        status='ACTIVE',
        end_date__lte=today + timedelta(days=7)
    ).count()

    # Assistance request statistics
    total_requests = AssistanceRequest.objects.count()
    pending_requests = AssistanceRequest.objects.filter(status='PENDING').count()
    in_progress_requests = AssistanceRequest.objects.filter(
        status__in=['ASSIGNED', 'IN_PROGRESS']
    ).count()
    completed_today = AssistanceRequest.objects.filter(
        status='COMPLETED',
        completion_time__date=today
    ).count()

    # Revenue statistics (GTQ)
    total_revenue = WalletTransaction.objects.filter(
        status='COMPLETED',
        transaction_type='PAYMENT'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    revenue_today = WalletTransaction.objects.filter(
        status='COMPLETED',
        transaction_type='PAYMENT',
        completed_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    revenue_month = WalletTransaction.objects.filter(
        status='COMPLETED',
        transaction_type='PAYMENT',
        completed_at__date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Provider statistics
    total_providers = Provider.objects.count()
    active_providers = Provider.objects.filter(status='ACTIVE', is_available=True).count()

    return Response({
        'users': {
            'total': total_users,
            'new_today': new_users_today,
            'new_this_week': new_users_week,
            'new_this_month': new_users_month,
        },
        'subscriptions': {
            'active': active_subscriptions,
            'expiring_soon': expiring_soon,
        },
        'requests': {
            'total': total_requests,
            'pending': pending_requests,
            'in_progress': in_progress_requests,
            'completed_today': completed_today,
        },
        'revenue': {
            'total': float(total_revenue),
            'today': float(revenue_today),
            'this_month': float(revenue_month),
            'currency': 'GTQ',
        },
        'providers': {
            'total': total_providers,
            'active': active_providers,
        },
        'generated_at': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def revenue_report(request):
    """
    Get detailed revenue report.

    GET /api/admin/dashboard/revenue/
    Query params:
    - period: daily, weekly, monthly (default: daily)
    - start_date: YYYY-MM-DD (default: 30 days ago)
    - end_date: YYYY-MM-DD (default: today)
    """
    period = request.query_params.get('period', 'daily')
    end_date = request.query_params.get('end_date')
    start_date = request.query_params.get('start_date')

    # Parse dates
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=30)

    # Base queryset
    transactions = WalletTransaction.objects.filter(
        status='COMPLETED',
        transaction_type='PAYMENT',
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date
    )

    # Group by period
    if period == 'monthly':
        data = transactions.annotate(
            period=TruncMonth('completed_at')
        ).values('period').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('period')
    else:  # daily
        data = transactions.annotate(
            period=TruncDate('completed_at')
        ).values('period').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('period')

    # Format response
    chart_data = [
        {
            'date': item['period'].isoformat() if item['period'] else None,
            'amount': float(item['total'] or 0),
            'transactions': item['count']
        }
        for item in data
    ]

    # Calculate totals
    totals = transactions.aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id'),
        avg_amount=Avg('amount')
    )

    return Response({
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'chart_data': chart_data,
        'totals': {
            'total_revenue': float(totals['total_amount'] or 0),
            'total_transactions': totals['total_count'],
            'average_transaction': float(totals['avg_amount'] or 0),
        },
        'currency': 'GTQ'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_report(request):
    """
    Get user registration and activity report.

    GET /api/admin/dashboard/users/
    Query params:
    - period: daily, weekly, monthly (default: daily)
    - days: number of days to include (default: 30)
    """
    period = request.query_params.get('period', 'daily')
    days = int(request.query_params.get('days', 30))

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # User registrations
    users = User.objects.filter(
        role='USER',
        date_joined__date__gte=start_date,
        date_joined__date__lte=end_date
    )

    if period == 'monthly':
        registrations = users.annotate(
            period=TruncMonth('date_joined')
        ).values('period').annotate(
            count=Count('id')
        ).order_by('period')
    else:
        registrations = users.annotate(
            period=TruncDate('date_joined')
        ).values('period').annotate(
            count=Count('id')
        ).order_by('period')

    chart_data = [
        {
            'date': item['period'].isoformat() if item['period'] else None,
            'registrations': item['count']
        }
        for item in registrations
    ]

    # User breakdown by status
    status_breakdown = {
        'active': User.objects.filter(role='USER', is_active=True).count(),
        'inactive': User.objects.filter(role='USER', is_active=False).count(),
        'verified': User.objects.filter(role='USER', is_phone_verified=True).count(),
        'unverified': User.objects.filter(role='USER', is_phone_verified=False).count(),
    }

    return Response({
        'period': period,
        'days': days,
        'chart_data': chart_data,
        'total_registrations': users.count(),
        'status_breakdown': status_breakdown
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def assistance_report(request):
    """
    Get assistance request statistics.

    GET /api/admin/dashboard/assistance/
    Query params:
    - days: number of days to include (default: 30)
    """
    days = int(request.query_params.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # Requests in period
    requests = AssistanceRequest.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    # By status
    status_breakdown = dict(
        requests.values('status').annotate(count=Count('id')).values_list('status', 'count')
    )

    # By category
    category_breakdown = list(
        requests.values('service_category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
    )

    # Daily trend
    daily_trend = list(
        requests.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
    )

    # Average response time (for completed requests)
    completed = requests.filter(
        status='COMPLETED',
        actual_arrival_time__isnull=False
    )
    avg_response_minutes = None
    if completed.exists():
        # Calculate average time between creation and arrival
        total_minutes = sum(
            (r.actual_arrival_time - r.created_at).total_seconds() / 60
            for r in completed
            if r.actual_arrival_time and r.created_at
        )
        avg_response_minutes = total_minutes / completed.count()

    return Response({
        'days': days,
        'total_requests': requests.count(),
        'status_breakdown': status_breakdown,
        'category_breakdown': [
            {'category': item['service_category__name'] or 'Sin categoria', 'count': item['count']}
            for item in category_breakdown
        ],
        'daily_trend': [
            {'date': item['date'].isoformat(), 'count': item['count']}
            for item in daily_trend
        ],
        'avg_response_minutes': round(avg_response_minutes, 1) if avg_response_minutes else None
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def subscription_report(request):
    """
    Get subscription statistics.

    GET /api/admin/dashboard/subscriptions/
    """
    # By status
    status_breakdown = dict(
        UserService.objects.values('status').annotate(
            count=Count('id')
        ).values_list('status', 'count')
    )

    # By plan
    plan_breakdown = list(
        UserService.objects.filter(status='ACTIVE').values(
            'service_plan__name'
        ).annotate(
            count=Count('id'),
            revenue=Sum('service_plan__price')
        ).order_by('-count')
    )

    # Expiring soon (next 7 days)
    expiring_soon = UserService.objects.filter(
        status='ACTIVE',
        end_date__lte=timezone.now().date() + timedelta(days=7),
        end_date__gte=timezone.now().date()
    ).select_related('user', 'service_plan').values(
        'id', 'user__email', 'service_plan__name', 'end_date'
    )[:20]

    # Monthly recurring revenue estimate
    mrr = UserService.objects.filter(
        status='ACTIVE'
    ).aggregate(
        total=Sum('service_plan__price')
    )['total'] or Decimal('0')

    return Response({
        'status_breakdown': status_breakdown,
        'plan_breakdown': [
            {
                'plan': item['service_plan__name'] or 'Sin plan',
                'count': item['count'],
                'revenue': float(item['revenue'] or 0)
            }
            for item in plan_breakdown
        ],
        'expiring_soon': list(expiring_soon),
        'mrr': float(mrr),
        'currency': 'GTQ'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def provider_report(request):
    """
    Get provider statistics.

    GET /api/admin/dashboard/providers/
    """
    providers = Provider.objects.all()

    # By status
    status_breakdown = dict(
        providers.values('status').annotate(
            count=Count('id')
        ).values_list('status', 'count')
    )

    # Top providers by completed requests
    top_providers = list(
        providers.filter(status='ACTIVE').annotate(
            completed_requests=Count(
                'assigned_requests',
                filter=Q(assigned_requests__status='COMPLETED')
            )
        ).order_by('-completed_requests').values(
            'id', 'company_name', 'rating', 'completed_requests'
        )[:10]
    )

    # Average rating
    avg_rating = providers.filter(
        status='ACTIVE', rating__gt=0
    ).aggregate(avg=Avg('rating'))['avg']

    return Response({
        'total_providers': providers.count(),
        'status_breakdown': status_breakdown,
        'top_providers': top_providers,
        'average_rating': round(float(avg_rating or 0), 2)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def recent_activity(request):
    """
    Get recent activity feed for admin dashboard.

    GET /api/admin/dashboard/activity/
    Query params:
    - limit: number of items (default: 20)
    """
    limit = int(request.query_params.get('limit', 20))

    activity = []

    # Recent users - using only() to prevent N+1 and limit fields
    recent_users = User.objects.filter(role='USER').only(
        'id', 'email', 'date_joined'
    ).order_by('-date_joined')[:5]
    for user in recent_users:
        activity.append({
            'type': 'user_registered',
            'message': f'Nuevo usuario: {user.email}',
            'timestamp': user.date_joined.isoformat(),
            'id': user.id
        })

    # Recent requests - using only() to limit fields
    recent_requests = AssistanceRequest.objects.only(
        'id', 'request_number', 'created_at'
    ).order_by('-created_at')[:5]
    for req in recent_requests:
        activity.append({
            'type': 'request_created',
            'message': f'Nueva solicitud: {req.request_number}',
            'timestamp': req.created_at.isoformat(),
            'id': req.id
        })

    # Recent transactions - using only() to limit fields
    recent_transactions = WalletTransaction.objects.filter(
        status='COMPLETED'
    ).only(
        'id', 'amount', 'completed_at', 'created_at'
    ).order_by('-completed_at')[:5]
    for tx in recent_transactions:
        activity.append({
            'type': 'payment_completed',
            'message': f'Pago completado: Q{tx.amount}',
            'timestamp': tx.completed_at.isoformat() if tx.completed_at else tx.created_at.isoformat(),
            'id': tx.id
        })

    # Sort by timestamp and limit
    activity.sort(key=lambda x: x['timestamp'], reverse=True)

    return Response({
        'activity': activity[:limit]
    })
