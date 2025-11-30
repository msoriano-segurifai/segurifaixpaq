"""
Enhanced Admin Dashboard Views

Provides dashboards for:
- SegurifAI Admin (full access to all data)
- PAQ Admin (payment and transaction data)
- MAWDY Admin (dispatch and field tech data)
- Real-time provider location map
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate, TruncHour
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


# =============================================================================
# Permission Helpers
# =============================================================================

def is_segurifai_admin(user):
    """Check if user is SegurifAI Admin (full access)"""
    return user.is_admin or user.role == 'ADMIN'


def is_paq_admin(user):
    """Check if user is PAQ Admin"""
    return user.role == 'PAQ_ADMIN' or is_segurifai_admin(user)


def is_mawdy_admin(user):
    """Check if user is MAWDY Admin"""
    return user.role == 'MAWDY_ADMIN' or is_segurifai_admin(user)


# =============================================================================
# SegurifAI Admin - Live Provider Map
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def live_provider_map(request):
    """
    Get all active providers with their current locations.

    GET /api/admin/dashboard/providers/map/

    Returns all online providers for real-time map display.
    SegurifAI Admin only.
    """
    if not is_segurifai_admin(request.user):
        return Response(
            {'error': 'Solo administradores de SegurifAI pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Try to get field tech profiles first (dispatch system)
    try:
        from apps.providers.dispatch import FieldTechProfile

        online_techs = FieldTechProfile.objects.filter(
            is_online=True
        ).select_related('user')

        from apps.providers.dispatch import JobOffer

        tech_locations = []
        for tech in online_techs:
            if tech.current_latitude and tech.current_longitude:
                # Get current active job if any
                current_job = JobOffer.objects.filter(
                    tech=tech,
                    status=JobOffer.Status.ACCEPTED,
                    assistance_request__status__in=['EN_ROUTE', 'IN_PROGRESS']
                ).first()

                tech_locations.append({
                    'id': tech.id,
                    'type': 'field_tech',
                    'name': f"{tech.user.first_name} {tech.user.last_name}",
                    'email': tech.user.email,
                    'vehicle_type': tech.vehicle_type,
                    'latitude': float(tech.current_latitude),
                    'longitude': float(tech.current_longitude),
                    'last_update': tech.last_location_update.isoformat() if tech.last_location_update else None,
                    'rating': float(tech.rating),
                    'status': 'online',
                    'current_job': current_job.id if current_job else None,
                })
    except ImportError:
        tech_locations = []

    # Also get traditional providers with location
    from apps.providers.models import ProviderLocation

    provider_locations = ProviderLocation.objects.filter(
        is_online=True
    ).select_related('provider')

    providers = [
        {
            'id': loc.provider.id,
            'type': 'provider',
            'name': loc.provider.company_name,
            'latitude': float(loc.latitude),
            'longitude': float(loc.longitude),
            'last_update': loc.last_updated.isoformat() if loc.last_updated else None,
            'status': 'active' if loc.provider.is_available else 'busy',
        }
        for loc in provider_locations
    ]

    # Combine both
    all_locations = tech_locations + providers

    # Get active requests needing service
    active_requests = AssistanceRequest.objects.filter(
        status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']
    ).values('id', 'location_latitude', 'location_longitude', 'status', 'title')

    request_pins = [
        {
            'id': req['id'],
            'type': 'request',
            'latitude': float(req['location_latitude']) if req['location_latitude'] else None,
            'longitude': float(req['location_longitude']) if req['location_longitude'] else None,
            'status': req['status'],
            'title': req['title'],
        }
        for req in active_requests
        if req['location_latitude'] and req['location_longitude']
    ]

    return Response({
        'providers': all_locations,
        'requests': request_pins,
        'summary': {
            'online_techs': len(tech_locations),
            'active_providers': len(providers),
            'pending_requests': sum(1 for r in request_pins if r['status'] == 'PENDING'),
            'in_progress': sum(1 for r in request_pins if r['status'] == 'IN_PROGRESS'),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def segurifai_full_dashboard(request):
    """
    Complete SegurifAI Admin dashboard with ALL data access.

    GET /api/admin/dashboard/full/

    Includes: Users, MAWDY data, PAQ data, all requests, all providers.
    """
    if not is_segurifai_admin(request.user):
        return Response(
            {'error': 'Solo administradores de SegurifAI pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())

    # Users by role
    users_by_role = User.objects.values('role').annotate(count=Count('id'))

    # Total revenue
    total_revenue = WalletTransaction.objects.filter(
        status='COMPLETED',
        transaction_type='PAYMENT'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    revenue_month = WalletTransaction.objects.filter(
        status='COMPLETED',
        transaction_type='PAYMENT',
        completed_at__date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Requests by status
    requests_by_status = AssistanceRequest.objects.values('status').annotate(count=Count('id'))

    # Requests by category
    requests_by_category = AssistanceRequest.objects.values(
        'service_category__category_type'
    ).annotate(count=Count('id'))

    # Active subscriptions by plan
    subs_by_plan = UserService.objects.filter(
        status='ACTIVE'
    ).values('plan__name').annotate(count=Count('id'))

    # MAWDY specific stats
    try:
        from apps.providers.dispatch import FieldTechProfile, JobOffer

        mawdy_stats = {
            'total_field_techs': FieldTechProfile.objects.count(),
            'online_techs': FieldTechProfile.objects.filter(is_online=True).count(),
            'jobs_today': JobOffer.objects.filter(
                offered_at__date=today,
                status='COMPLETED'
            ).count(),
            'total_earnings_today': JobOffer.objects.filter(
                offered_at__date=today,
                status='COMPLETED'
            ).aggregate(total=Sum('total_earnings'))['total'] or Decimal('0'),
        }
    except ImportError:
        mawdy_stats = {'message': 'Dispatch system not configured'}

    # PAQ specific stats
    paq_stats = {
        'total_transactions': WalletTransaction.objects.count(),
        'transactions_today': WalletTransaction.objects.filter(
            created_at__date=today
        ).count(),
        'pending_payments': WalletTransaction.objects.filter(
            status='PENDING'
        ).count(),
        'failed_transactions': WalletTransaction.objects.filter(
            status='FAILED'
        ).count(),
    }

    return Response({
        'overview': {
            'total_users': User.objects.count(),
            'total_revenue': str(total_revenue),
            'revenue_this_month': str(revenue_month),
            'active_requests': AssistanceRequest.objects.filter(
                status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']
            ).count(),
        },
        'users_by_role': list(users_by_role),
        'requests_by_status': list(requests_by_status),
        'requests_by_category': list(requests_by_category),
        'subscriptions_by_plan': list(subs_by_plan),
        'mawdy': mawdy_stats,
        'paq': paq_stats,
    })


# =============================================================================
# PAQ Admin Dashboard
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paq_dashboard_overview(request):
    """
    PAQ Admin dashboard overview.

    GET /api/admin/paq/overview/

    Transaction and payment statistics.
    """
    if not is_paq_admin(request.user):
        return Response(
            {'error': 'Solo administradores de PAQ pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    yesterday = today - timedelta(days=1)

    # Transaction counts
    total_transactions = WalletTransaction.objects.count()
    transactions_today = WalletTransaction.objects.filter(created_at__date=today).count()
    transactions_yesterday = WalletTransaction.objects.filter(created_at__date=yesterday).count()

    # Revenue
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

    # Transaction status breakdown
    by_status = WalletTransaction.objects.values('status').annotate(
        count=Count('id'),
        total=Sum('amount')
    )

    # By transaction type
    by_type = WalletTransaction.objects.values('transaction_type').annotate(
        count=Count('id'),
        total=Sum('amount')
    )

    # Failed transactions (for fraud/issue monitoring)
    failed_today = WalletTransaction.objects.filter(
        status='FAILED',
        created_at__date=today
    ).count()

    # Average transaction amount
    avg_amount = WalletTransaction.objects.filter(
        status='COMPLETED'
    ).aggregate(avg=Avg('amount'))['avg'] or Decimal('0')

    return Response({
        'overview': {
            'total_transactions': total_transactions,
            'transactions_today': transactions_today,
            'transactions_yesterday': transactions_yesterday,
            'trend': 'up' if transactions_today > transactions_yesterday else 'down',
        },
        'revenue': {
            'today': str(revenue_today),
            'this_month': str(revenue_month),
            'currency': 'GTQ',
        },
        'by_status': list(by_status),
        'by_type': list(by_type),
        'alerts': {
            'failed_today': failed_today,
            'pending_count': WalletTransaction.objects.filter(status='PENDING').count(),
        },
        'metrics': {
            'average_transaction': str(avg_amount),
            'success_rate': round(
                WalletTransaction.objects.filter(status='COMPLETED').count() / max(total_transactions, 1) * 100, 2
            ),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paq_transaction_history(request):
    """
    PAQ transaction history with filtering.

    GET /api/admin/paq/transactions/

    Query params: status, type, date_from, date_to, limit
    """
    if not is_paq_admin(request.user):
        return Response(
            {'error': 'Solo administradores de PAQ pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    transactions = WalletTransaction.objects.select_related('user').order_by('-created_at')

    # Filters
    status_filter = request.query_params.get('status')
    if status_filter:
        transactions = transactions.filter(status=status_filter)

    type_filter = request.query_params.get('type')
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)

    limit = int(request.query_params.get('limit', 50))
    transactions = transactions[:limit]

    return Response({
        'count': transactions.count(),
        'transactions': [
            {
                'id': t.id,
                'user_email': t.user.email if t.user else None,
                'type': t.transaction_type,
                'amount': str(t.amount),
                'currency': t.currency,
                'status': t.status,
                'reference': t.reference_number,
                'created_at': t.created_at.isoformat(),
                'completed_at': t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in transactions
        ]
    })


# =============================================================================
# MAWDY Admin Dashboard
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mawdy_dashboard_overview(request):
    """
    MAWDY Admin dashboard overview.

    GET /api/admin/mawdy/overview/

    Dispatch and field technician statistics.
    """
    if not is_mawdy_admin(request.user):
        return Response(
            {'error': 'Solo administradores de MAWDY pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())

    try:
        from apps.providers.dispatch import FieldTechProfile, JobOffer, FieldTechShift

        # Field tech stats
        total_techs = FieldTechProfile.objects.count()
        online_techs = FieldTechProfile.objects.filter(is_online=True).count()

        # By vehicle type
        by_vehicle = FieldTechProfile.objects.values('vehicle_type').annotate(count=Count('id'))

        # Job stats
        jobs_today = JobOffer.objects.filter(offered_at__date=today).count()
        completed_today = JobOffer.objects.filter(
            offered_at__date=today,
            status='COMPLETED'
        ).count()

        pending_jobs = JobOffer.objects.filter(status='PENDING').count()
        in_progress = JobOffer.objects.filter(status='IN_PROGRESS').count()

        # Earnings
        earnings_today = JobOffer.objects.filter(
            offered_at__date=today,
            status='COMPLETED'
        ).aggregate(total=Sum('total_earnings'))['total'] or Decimal('0')

        earnings_week = JobOffer.objects.filter(
            offered_at__date__gte=start_of_week,
            status='COMPLETED'
        ).aggregate(total=Sum('total_earnings'))['total'] or Decimal('0')

        # Top performers
        top_techs = FieldTechProfile.objects.filter(
            total_jobs_completed__gt=0
        ).order_by('-rating', '-total_jobs_completed')[:5]

        # Average response time (from offer to responded)
        avg_response = JobOffer.objects.filter(
            status='COMPLETED',
            responded_at__isnull=False
        ).annotate(
            response_time=F('responded_at') - F('offered_at')
        ).aggregate(avg=Avg('response_time'))

        return Response({
            'technicians': {
                'total': total_techs,
                'online': online_techs,
                'offline': total_techs - online_techs,
                'by_vehicle': list(by_vehicle),
            },
            'jobs': {
                'today': jobs_today,
                'completed_today': completed_today,
                'pending': pending_jobs,
                'in_progress': in_progress,
                'completion_rate': round(completed_today / max(jobs_today, 1) * 100, 1),
            },
            'earnings': {
                'today': str(earnings_today),
                'this_week': str(earnings_week),
                'currency': 'GTQ',
            },
            'top_technicians': [
                {
                    'id': t.id,
                    'name': f"{t.user.first_name} {t.user.last_name}",
                    'rating': float(t.rating),
                    'total_jobs': t.total_jobs_completed,
                    'vehicle': t.vehicle_type,
                }
                for t in top_techs
            ],
            'metrics': {
                'avg_response_seconds': avg_response['avg'].total_seconds() if avg_response['avg'] else None,
            }
        })

    except ImportError:
        return Response({
            'error': 'Dispatch system not configured',
            'message': 'FieldTechProfile model not found'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mawdy_tech_list(request):
    """
    List all MAWDY field technicians.

    GET /api/admin/mawdy/technicians/
    """
    if not is_mawdy_admin(request.user):
        return Response(
            {'error': 'Solo administradores de MAWDY pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        from apps.providers.dispatch import FieldTechProfile

        techs = FieldTechProfile.objects.select_related('user').order_by('-is_online', '-rating')

        return Response({
            'count': techs.count(),
            'technicians': [
                {
                    'id': t.id,
                    'user_id': t.user.id,
                    'name': f"{t.user.first_name} {t.user.last_name}",
                    'email': t.user.email,
                    'phone': t.user.phone_number,
                    'vehicle_type': t.vehicle_type,
                    'vehicle_plate': t.vehicle_plate,
                    'is_online': t.is_online,
                    'rating': float(t.rating),
                    'total_jobs': t.total_jobs_completed,
                    'total_earnings': str(t.total_earnings),
                    'current_location': {
                        'lat': float(t.current_latitude) if t.current_latitude else None,
                        'lng': float(t.current_longitude) if t.current_longitude else None,
                    } if t.current_latitude else None,
                    'last_active': t.last_location_update.isoformat() if t.last_location_update else None,
                }
                for t in techs
            ]
        })

    except ImportError:
        return Response({'error': 'Dispatch system not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mawdy_job_history(request):
    """
    MAWDY job history.

    GET /api/admin/mawdy/jobs/

    Query params: status, tech_id, date_from, limit
    """
    if not is_mawdy_admin(request.user):
        return Response(
            {'error': 'Solo administradores de MAWDY pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        from apps.providers.dispatch import JobOffer

        jobs = JobOffer.objects.select_related(
            'tech', 'tech__user', 'assistance_request'
        ).order_by('-offered_at')

        # Filters
        status_filter = request.query_params.get('status')
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        tech_id = request.query_params.get('tech_id')
        if tech_id:
            jobs = jobs.filter(tech_id=tech_id)

        limit = int(request.query_params.get('limit', 50))
        jobs = jobs[:limit]

        return Response({
            'count': jobs.count(),
            'jobs': [
                {
                    'id': j.id,
                    'request_id': j.assistance_request.id if j.assistance_request else None,
                    'request_number': j.assistance_request.request_number if j.assistance_request else None,
                    'tech_name': f"{j.tech.user.first_name} {j.tech.user.last_name}" if j.tech else None,
                    'status': j.status,
                    'earning': str(j.total_earnings) if j.total_earnings else None,
                    'distance_km': float(j.distance_km) if j.distance_km else None,
                    'offered_at': j.offered_at.isoformat() if j.offered_at else None,
                    'responded_at': j.responded_at.isoformat() if j.responded_at else None,
                }
                for j in jobs
            ]
        })

    except ImportError:
        return Response({'error': 'Dispatch system not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# =============================================================================
# Real-Time Active Dispatch (All Admin Types)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_dispatch_realtime(request):
    """
    Real-time active dispatch data for all admin types.

    GET /api/admin/dashboard/dispatch/active/

    Returns currently active dispatch jobs with live location data.
    Accessible by: SegurifAI Admin, MAWDY Admin, PAQ Admin
    """
    if not (is_segurifai_admin(request.user) or is_mawdy_admin(request.user) or is_paq_admin(request.user)):
        return Response(
            {'error': 'Solo administradores pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        from apps.providers.dispatch import JobOffer, FieldTechProfile
        from apps.core.maps_service import calculate_eta

        # Get all active jobs (not pending offers, but actual ongoing work)
        active_jobs = JobOffer.objects.filter(
            status__in=['ACCEPTED', 'EN_ROUTE', 'ARRIVED', 'IN_PROGRESS']
        ).select_related(
            'tech', 'tech__user', 'assistance_request', 'assistance_request__user'
        ).order_by('-offered_at')

        dispatches = []
        for job in active_jobs:
            tech = job.tech
            req = job.assistance_request

            # Calculate real-time ETA using Google Maps
            eta_data = None
            if tech.current_latitude and tech.current_longitude and req.location_latitude and req.location_longitude:
                try:
                    eta_result = calculate_eta(
                        (float(tech.current_latitude), float(tech.current_longitude)),
                        (float(req.location_latitude), float(req.location_longitude))
                    )
                    eta_data = {
                        'minutes': eta_result.get('eta_minutes'),
                        'distance_km': eta_result.get('distance_km'),
                        'source': eta_result.get('source', 'google_maps')
                    }
                except Exception:
                    pass

            dispatches.append({
                'job_id': job.id,
                'status': job.status,
                'request': {
                    'id': req.id,
                    'number': req.request_number,
                    'title': req.title,
                    'service_type': req.service_category.category_type if req.service_category else None,
                    'user_name': f"{req.user.first_name} {req.user.last_name}" if req.user else None,
                    'user_phone': req.user.phone_number if req.user else None,
                    'location': {
                        'lat': float(req.location_latitude) if req.location_latitude else None,
                        'lng': float(req.location_longitude) if req.location_longitude else None,
                        'address': req.location_address,
                    },
                },
                'technician': {
                    'id': tech.id,
                    'name': f"{tech.user.first_name} {tech.user.last_name}",
                    'phone': tech.user.phone_number,
                    'vehicle_type': tech.vehicle_type,
                    'vehicle_plate': tech.vehicle_plate,
                    'current_location': {
                        'lat': float(tech.current_latitude) if tech.current_latitude else None,
                        'lng': float(tech.current_longitude) if tech.current_longitude else None,
                        'updated_at': tech.last_location_update.isoformat() if tech.last_location_update else None,
                    },
                    'rating': float(tech.rating),
                },
                'eta': eta_data,
                'earnings': str(job.total_earnings),
                'started_at': job.responded_at.isoformat() if job.responded_at else None,
            })

        # Get pending requests without dispatch
        pending_requests = AssistanceRequest.objects.filter(
            status='PENDING'
        ).select_related('user', 'service_category')[:20]

        pending = [
            {
                'id': req.id,
                'number': req.request_number,
                'title': req.title,
                'service_type': req.service_category.category_type if req.service_category else None,
                'location': {
                    'lat': float(req.location_latitude) if req.location_latitude else None,
                    'lng': float(req.location_longitude) if req.location_longitude else None,
                    'address': req.location_address,
                },
                'created_at': req.created_at.isoformat(),
                'waiting_minutes': int((timezone.now() - req.created_at).total_seconds() / 60),
            }
            for req in pending_requests
        ]

        # Online techs available for dispatch
        available_techs = FieldTechProfile.objects.filter(
            is_online=True,
            status='ACTIVE'
        ).select_related('user').count()

        return Response({
            'active_dispatches': dispatches,
            'pending_requests': pending,
            'summary': {
                'active_count': len(dispatches),
                'pending_count': len(pending),
                'available_techs': available_techs,
            },
            'timestamp': timezone.now().isoformat(),
        })

    except ImportError:
        return Response({'error': 'Dispatch system not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dispatch_action_logs(request):
    """
    Get dispatch action audit logs.

    GET /api/admin/dashboard/dispatch/logs/

    Query params: action, tech_id, request_id, limit
    Accessible by: SegurifAI Admin, MAWDY Admin
    """
    if not (is_segurifai_admin(request.user) or is_mawdy_admin(request.user)):
        return Response(
            {'error': 'Solo administradores de SegurifAI o MAWDY pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        from apps.providers.dispatch import DispatchActionLog

        logs = DispatchActionLog.objects.select_related(
            'tech', 'tech__user', 'assistance_request', 'performed_by'
        ).order_by('-created_at')

        # Filters
        action_filter = request.query_params.get('action')
        if action_filter:
            logs = logs.filter(action=action_filter)

        tech_id = request.query_params.get('tech_id')
        if tech_id:
            logs = logs.filter(tech_id=tech_id)

        request_id = request.query_params.get('request_id')
        if request_id:
            logs = logs.filter(assistance_request_id=request_id)

        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]

        return Response({
            'count': logs.count(),
            'logs': [
                {
                    'id': log.id,
                    'action': log.action,
                    'action_display': log.get_action_display(),
                    'tech_name': f"{log.tech.user.first_name} {log.tech.user.last_name}" if log.tech else None,
                    'request_number': log.assistance_request.request_number if log.assistance_request else None,
                    'performed_by': log.performed_by.email if log.performed_by else 'System',
                    'location': {
                        'lat': float(log.latitude) if log.latitude else None,
                        'lng': float(log.longitude) if log.longitude else None,
                    } if log.latitude else None,
                    'details': log.details,
                    'notes': log.notes,
                    'created_at': log.created_at.isoformat(),
                }
                for log in logs
            ]
        })

    except ImportError:
        return Response({'error': 'DispatchActionLog not found'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
