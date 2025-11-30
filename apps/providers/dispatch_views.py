"""
MAWDY Field Tech Dispatch API Views

Delivery-app style endpoints for motorcycle field technicians.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .dispatch import (
    FieldTechProfile,
    FieldTechShift,
    JobOffer,
    FieldTechLocationHistory,
    DispatchService,
)
from apps.assistance.models import AssistanceRequest


# =============================================================================
# Field Tech Profile & Status
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_profile(request):
    """
    Get field tech's profile and stats.

    GET /api/providers/dispatch/profile/
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico. Contacta a tu administrador.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get current shift
    current_shift = FieldTechShift.objects.filter(
        tech=profile,
        ended_at__isnull=True
    ).first()

    return Response({
        'profile': {
            'id': profile.id,
            'email': request.user.email,
            'name': request.user.get_full_name(),
            'phone': request.user.phone_number,
            'vehicle_type': profile.vehicle_type,
            'vehicle_plate': profile.vehicle_plate,
            'service_capabilities': profile.service_capabilities,
            'status': profile.status,
            'is_online': profile.is_online,
            'is_available': profile.is_available,
        },
        'stats': {
            'rating': float(profile.rating),
            'total_jobs_completed': profile.total_jobs_completed,
            'acceptance_rate': float(profile.acceptance_rate),
            'total_earnings': float(profile.total_earnings),
            'weekly_earnings': float(profile.weekly_earnings),
            'daily_earnings': float(profile.daily_earnings),
        },
        'current_shift': {
            'id': current_shift.id if current_shift else None,
            'started_at': current_shift.started_at.isoformat() if current_shift else None,
            'duration_minutes': int(current_shift.duration.total_seconds() / 60) if current_shift else None,
            'jobs_completed': current_shift.jobs_completed if current_shift else 0,
            'earnings': float(current_shift.earnings) if current_shift else 0,
        } if current_shift else None,
        'location': {
            'latitude': float(profile.current_latitude) if profile.current_latitude else None,
            'longitude': float(profile.current_longitude) if profile.current_longitude else None,
            'last_updated': profile.last_location_update.isoformat() if profile.last_location_update else None,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def go_online(request):
    """
    Go online and start receiving job offers.

    POST /api/providers/dispatch/online/

    Body:
    {
        "latitude": 14.6349,
        "longitude": -90.5069
    }
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    if profile.status != FieldTechProfile.Status.ACTIVE:
        return Response(
            {'error': 'Tu cuenta no esta activa. Contacta a tu administrador.'},
            status=status.HTTP_403_FORBIDDEN
        )

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if not latitude or not longitude:
        return Response(
            {'error': 'latitude y longitude son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        # Update location and go online
        profile.update_location(latitude, longitude)
        profile.go_online()

        # Start a new shift
        shift = FieldTechShift.objects.create(
            tech=profile,
            start_latitude=latitude,
            start_longitude=longitude
        )

    return Response({
        'success': True,
        'message': 'Estas en linea. Comenzaras a recibir ofertas de trabajo.',
        'is_online': True,
        'shift_id': shift.id,
        'started_at': shift.started_at.isoformat()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def go_offline(request):
    """
    Go offline and stop receiving job offers.

    POST /api/providers/dispatch/offline/
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check for active jobs
    active_job = DispatchService.get_active_job_for_tech(profile)
    if active_job:
        return Response(
            {'error': 'Tienes un trabajo activo. Completalo antes de desconectarte.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        profile.go_offline()

        # End current shift
        current_shift = FieldTechShift.objects.filter(
            tech=profile,
            ended_at__isnull=True
        ).first()

        shift_summary = None
        if current_shift:
            current_shift.end_shift()
            shift_summary = {
                'shift_id': current_shift.id,
                'duration_minutes': int(current_shift.duration.total_seconds() / 60),
                'jobs_completed': current_shift.jobs_completed,
                'earnings': float(current_shift.earnings),
            }

    return Response({
        'success': True,
        'message': 'Estas desconectado.',
        'is_online': False,
        'shift_summary': shift_summary
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_location(request):
    """
    Update field tech's current location.

    POST /api/providers/dispatch/location/

    Body:
    {
        "latitude": 14.6349,
        "longitude": -90.5069,
        "accuracy": 10.5,
        "speed": 25.0,
        "heading": 180.0
    }
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if not latitude or not longitude:
        return Response(
            {'error': 'latitude y longitude son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update profile location
    profile.update_location(latitude, longitude)

    # Record in history if online
    if profile.is_online:
        current_shift = FieldTechShift.objects.filter(
            tech=profile,
            ended_at__isnull=True
        ).first()

        FieldTechLocationHistory.objects.create(
            tech=profile,
            shift=current_shift,
            latitude=latitude,
            longitude=longitude,
            accuracy=request.data.get('accuracy'),
            speed=request.data.get('speed'),
            heading=request.data.get('heading')
        )

    return Response({
        'success': True,
        'location': {
            'latitude': float(profile.current_latitude),
            'longitude': float(profile.current_longitude),
            'last_updated': profile.last_location_update.isoformat()
        }
    })


# =============================================================================
# Job Offers (Incoming Jobs)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_jobs(request):
    """
    Get pending job offers for the tech.

    GET /api/providers/dispatch/jobs/available/
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    pending_offers = DispatchService.get_pending_offers_for_tech(profile)

    jobs = []
    for offer in pending_offers:
        req = offer.assistance_request
        jobs.append({
            'offer_id': offer.id,
            'request_id': req.id,
            'request_number': req.request_number,
            'service_type': req.incident_type,
            'title': req.title,
            'description': req.description[:100] if req.description else '',
            'customer': {
                'name': req.user.get_full_name() if req.user else 'Usuario',
                'phone': req.user.phone_number if req.user else None,
            },
            'location': {
                'address': req.location_address,
                'city': req.location_city,
                'latitude': float(req.location_latitude) if req.location_latitude else None,
                'longitude': float(req.location_longitude) if req.location_longitude else None,
            },
            'distance_km': float(offer.distance_km),
            'eta_minutes': offer.estimated_arrival_minutes,
            'earnings': {
                'base': float(offer.base_earnings),
                'distance_bonus': float(offer.distance_bonus),
                'total': float(offer.total_earnings),
            },
            'expires_at': offer.expires_at.isoformat(),
            'seconds_remaining': max(0, int((offer.expires_at - timezone.now()).total_seconds())),
        })

    return Response({
        'count': len(jobs),
        'jobs': jobs
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_job(request, offer_id):
    """
    Accept a job offer.

    POST /api/providers/dispatch/jobs/<offer_id>/accept/
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        offer = JobOffer.objects.select_related('assistance_request').get(
            id=offer_id,
            tech=profile
        )
    except JobOffer.DoesNotExist:
        return Response(
            {'error': 'Oferta no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if offer.is_expired:
        offer.status = JobOffer.Status.EXPIRED
        offer.save()
        return Response(
            {'error': 'Esta oferta ha expirado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if offer.status != JobOffer.Status.PENDING:
        return Response(
            {'error': f'Esta oferta ya fue {offer.get_status_display().lower()}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Accept the offer
    with transaction.atomic():
        offer.accept()

        # Update assistance request status
        req = offer.assistance_request
        req.status = 'EN_ROUTE'
        req.assigned_provider_id = profile.id
        req.save()

    return Response({
        'success': True,
        'message': 'Trabajo aceptado. Dirigete a la ubicacion del cliente.',
        'job': {
            'offer_id': offer.id,
            'request_id': req.id,
            'request_number': req.request_number,
            'customer': {
                'name': req.user.get_full_name() if req.user else 'Usuario',
                'phone': req.user.phone_number if req.user else None,
            },
            'location': {
                'address': req.location_address,
                'city': req.location_city,
                'latitude': float(req.location_latitude) if req.location_latitude else None,
                'longitude': float(req.location_longitude) if req.location_longitude else None,
            },
            'eta_minutes': offer.estimated_arrival_minutes,
            'earnings': float(offer.total_earnings),
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_job(request, offer_id):
    """
    Decline a job offer.

    POST /api/providers/dispatch/jobs/<offer_id>/decline/

    Body (optional):
    {
        "reason": "Estoy lejos de la ubicacion"
    }
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        offer = JobOffer.objects.get(id=offer_id, tech=profile)
    except JobOffer.DoesNotExist:
        return Response(
            {'error': 'Oferta no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if offer.status != JobOffer.Status.PENDING:
        return Response(
            {'error': 'Esta oferta ya no esta pendiente'},
            status=status.HTTP_400_BAD_REQUEST
        )

    offer.decline()

    # Note: System will automatically offer to next tech in queue
    # This should be handled by a background task/celery

    return Response({
        'success': True,
        'message': 'Oferta rechazada',
        'acceptance_rate': float(profile.acceptance_rate)
    })


# =============================================================================
# Active Job Management
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_job(request):
    """
    Get the tech's current active job.

    GET /api/providers/dispatch/jobs/active/
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    active_offer = DispatchService.get_active_job_for_tech(profile)

    if not active_offer:
        return Response({
            'has_active_job': False,
            'job': None
        })

    req = active_offer.assistance_request

    return Response({
        'has_active_job': True,
        'job': {
            'offer_id': active_offer.id,
            'request_id': req.id,
            'request_number': req.request_number,
            'status': req.status,
            'service_type': req.incident_type,
            'title': req.title,
            'description': req.description,
            'customer': {
                'name': req.user.get_full_name() if req.user else 'Usuario',
                'phone': req.user.phone_number if req.user else None,
            },
            'location': {
                'address': req.location_address,
                'city': req.location_city,
                'latitude': float(req.location_latitude) if req.location_latitude else None,
                'longitude': float(req.location_longitude) if req.location_longitude else None,
            },
            'accepted_at': active_offer.responded_at.isoformat() if active_offer.responded_at else None,
            'earnings': float(active_offer.total_earnings),
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_arrived(request, offer_id):
    """
    Mark that tech has arrived at customer location.

    POST /api/providers/dispatch/jobs/<offer_id>/arrived/
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        offer = JobOffer.objects.select_related('assistance_request').get(
            id=offer_id,
            tech=profile,
            status=JobOffer.Status.ACCEPTED
        )
    except JobOffer.DoesNotExist:
        return Response(
            {'error': 'Trabajo activo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    req = offer.assistance_request
    req.status = 'ARRIVED'
    req.save()

    return Response({
        'success': True,
        'message': 'Llegada registrada',
        'status': 'ARRIVED'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_service(request, offer_id):
    """
    Start working on the service.

    POST /api/providers/dispatch/jobs/<offer_id>/start/
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        offer = JobOffer.objects.select_related('assistance_request').get(
            id=offer_id,
            tech=profile,
            status=JobOffer.Status.ACCEPTED
        )
    except JobOffer.DoesNotExist:
        return Response(
            {'error': 'Trabajo activo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    req = offer.assistance_request
    req.status = 'IN_PROGRESS'
    req.save()

    return Response({
        'success': True,
        'message': 'Servicio iniciado',
        'status': 'IN_PROGRESS'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_job(request, offer_id):
    """
    Complete the job - REQUIRES completion form with evidence.

    POST /api/providers/dispatch/jobs/<offer_id>/complete/

    Body (REQUIRED):
    {
        "completion_notes": "Descripcion del servicio realizado",
        "service_outcome": "completed|partial|cancelled",
        "photos": ["url1", "url2"],  // At least 1 photo required
        "signature_url": "url",       // Customer signature
        "customer_satisfied": true,
        "additional_notes": "Notas adicionales"
    }
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        offer = JobOffer.objects.select_related('assistance_request').get(
            id=offer_id,
            tech=profile,
            status=JobOffer.Status.ACCEPTED
        )
    except JobOffer.DoesNotExist:
        return Response(
            {'error': 'Trabajo activo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # =========================================================================
    # COMPLETION FORM VALIDATION - Required for all MAWDY field techs
    # =========================================================================
    completion_notes = request.data.get('completion_notes', '').strip()
    service_outcome = request.data.get('service_outcome', '')
    photos = request.data.get('photos', [])
    signature_url = request.data.get('signature_url', '')
    customer_satisfied = request.data.get('customer_satisfied')

    # Validate required fields
    missing_fields = []

    if not completion_notes:
        missing_fields.append('completion_notes (descripcion del servicio)')

    if service_outcome not in ['completed', 'partial', 'cancelled']:
        missing_fields.append('service_outcome (completed/partial/cancelled)')

    if not photos or len(photos) < 1:
        missing_fields.append('photos (minimo 1 foto de evidencia)')

    if not signature_url:
        missing_fields.append('signature_url (firma del cliente)')

    if customer_satisfied is None:
        missing_fields.append('customer_satisfied (satisfaccion del cliente)')

    if missing_fields:
        return Response({
            'error': 'Formulario de finalizacion incompleto',
            'missing_fields': missing_fields,
            'message': 'Por favor complete todos los campos requeridos del formulario de finalizacion'
        }, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # Update request status
        req = offer.assistance_request
        req.status = 'COMPLETED'
        req.completed_at = timezone.now()
        req.resolution_notes = completion_notes
        req.save()

        # Store completion form data in offer
        offer.completion_data = {
            'completion_notes': completion_notes,
            'service_outcome': service_outcome,
            'photos': photos,
            'signature_url': signature_url,
            'customer_satisfied': customer_satisfied,
            'additional_notes': request.data.get('additional_notes', ''),
            'completed_by': profile.user.email,
            'completed_at': timezone.now().isoformat()
        }
        offer.save()

        # Update tech earnings and stats
        result = DispatchService.complete_job(offer)

        # Log completion action
        from .dispatch import DispatchActionLog
        DispatchActionLog.log_action(
            action=DispatchActionLog.ActionType.SERVICE_COMPLETED,
            job_offer=offer,
            assistance_request=req,
            tech=profile,
            performed_by=request.user,
            details={
                'service_outcome': service_outcome,
                'customer_satisfied': customer_satisfied,
                'photos_count': len(photos),
                'has_signature': bool(signature_url)
            }
        )

    return Response({
        'success': True,
        'message': 'Trabajo completado con formulario de finalizacion!',
        'earnings': result['earnings'],
        'stats': {
            'total_jobs_completed': result['total_jobs_completed'],
            'daily_earnings': result['daily_earnings'],
        },
        'completion_form_submitted': True
    })


# =============================================================================
# Earnings & History
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_earnings(request):
    """
    Get tech's earnings summary.

    GET /api/providers/dispatch/earnings/

    Query params:
    - period: 'today', 'week', 'month', 'all' (default: 'today')
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    period = request.query_params.get('period', 'today')

    # Calculate earnings based on period
    now = timezone.now()

    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timezone.timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = None

    # Get completed jobs in period
    jobs_query = JobOffer.objects.filter(
        tech=profile,
        status=JobOffer.Status.ACCEPTED,
        assistance_request__status='COMPLETED'
    )

    if start_date:
        jobs_query = jobs_query.filter(responded_at__gte=start_date)

    completed_jobs = jobs_query.select_related('assistance_request')

    total_earnings = sum(job.total_earnings for job in completed_jobs)
    jobs_count = completed_jobs.count()

    return Response({
        'period': period,
        'earnings': {
            'total': float(total_earnings),
            'jobs_count': jobs_count,
            'average_per_job': float(total_earnings / jobs_count) if jobs_count > 0 else 0,
        },
        'lifetime': {
            'total_earnings': float(profile.total_earnings),
            'total_jobs': profile.total_jobs_completed,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_history(request):
    """
    Get tech's completed job history.

    GET /api/providers/dispatch/jobs/history/

    Query params:
    - limit: Number of jobs to return (default: 20)
    - offset: Pagination offset (default: 0)
    """
    try:
        profile = FieldTechProfile.objects.get(user=request.user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico'},
            status=status.HTTP_404_NOT_FOUND
        )

    limit = int(request.query_params.get('limit', 20))
    offset = int(request.query_params.get('offset', 0))

    completed_jobs = JobOffer.objects.filter(
        tech=profile,
        status=JobOffer.Status.ACCEPTED,
        assistance_request__status='COMPLETED'
    ).select_related('assistance_request').order_by('-responded_at')[offset:offset + limit]

    jobs = []
    for offer in completed_jobs:
        req = offer.assistance_request
        jobs.append({
            'offer_id': offer.id,
            'request_number': req.request_number,
            'service_type': req.incident_type,
            'title': req.title,
            'location': req.location_address,
            'completed_at': req.completed_at.isoformat() if req.completed_at else None,
            'earnings': float(offer.total_earnings),
            'distance_km': float(offer.distance_km),
        })

    return Response({
        'count': len(jobs),
        'jobs': jobs
    })
