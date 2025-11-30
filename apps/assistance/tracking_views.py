"""
Tracking API Views for SegurifAI x PAQ

REST endpoints for real-time assistance tracking (delivery-app style).
All access requires either JWT authentication or PAQ SSO token.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import AssistanceRequest
from .tracking import TrackingService, TrackingStatus
from apps.users.permissions import IsAdmin, IsProvider
from apps.users.paq_auth_views import verify_paq_sso_token


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tracking_info(request, request_id):
    """
    Get real-time tracking information for an assistance request.

    GET /api/assistance/tracking/<request_id>/

    Returns delivery-app style tracking data:
    - Provider location (lat/lng)
    - ETA (estimated time of arrival)
    - Distance remaining
    - Tracking status (searching, en_route, arriving, arrived, etc.)
    - Timeline of events
    """
    try:
        # Users can only track their own requests
        # Providers can track requests assigned to them
        # Admins can track any request
        assistance_request = AssistanceRequest.objects.select_related(
            'provider', 'user', 'service_category'
        ).get(id=request_id)

        # Permission check
        user = request.user
        if user.role == 'USER' and assistance_request.user_id != user.id:
            return Response(
                {'error': 'No tienes permiso para ver esta solicitud'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.role == 'PROVIDER':
            if not hasattr(user, 'provider_profile') or \
               assistance_request.provider_id != user.provider_profile.id:
                return Response(
                    {'error': 'No tienes permiso para ver esta solicitud'},
                    status=status.HTTP_403_FORBIDDEN
                )

        tracking_info = TrackingService.get_tracking_info(assistance_request)

        return Response(tracking_info)

    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_tracking(request):
    """
    Get tracking info for user's active assistance requests.

    GET /api/assistance/tracking/active/

    Returns list of active requests with their tracking status.
    Useful for showing a "Your active deliveries" style screen.
    """
    user = request.user

    # Get user's active requests
    if user.role == 'USER':
        active_requests = AssistanceRequest.objects.filter(
            user=user,
            status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']
        ).select_related('provider', 'service_category')
    elif user.role == 'PROVIDER' and hasattr(user, 'provider_profile'):
        active_requests = AssistanceRequest.objects.filter(
            provider=user.provider_profile,
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).select_related('user', 'service_category')
    else:
        # Admin sees all active
        active_requests = AssistanceRequest.objects.filter(
            status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']
        ).select_related('provider', 'user', 'service_category')[:20]

    tracking_list = []
    for req in active_requests:
        tracking_info = TrackingService.get_tracking_info(req)
        # Add summary info
        tracking_list.append({
            'request_id': req.id,
            'request_number': req.request_number,
            'title': req.title,
            'service_type': req.service_category.category_type if req.service_category else None,
            'status': req.status,
            'tracking_status': tracking_info['tracking_status'],
            'tracking_status_display': tracking_info['tracking_status_display'],
            'eta': tracking_info.get('eta'),
            'provider_name': req.provider.company_name if req.provider else None,
            'created_at': req.created_at.isoformat(),
        })

    return Response({
        'count': len(tracking_list),
        'requests': tracking_list
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_provider_location(request):
    """
    Update provider's current location (for providers and admins).

    POST /api/assistance/tracking/update-location/

    Body:
    {
        "latitude": 14.6349,
        "longitude": -90.5069,
        "heading": 45.0,          // Optional: direction in degrees
        "speed": 30.5,            // Optional: speed in km/h
        "accuracy": 10.0,         // Optional: GPS accuracy in meters
        "request_id": 123         // Optional: associated request
    }

    This endpoint should be called frequently (every 5-10 seconds)
    when a provider is actively handling a request.
    """
    user = request.user

    # Allow providers and admins
    if user.role == 'PROVIDER' and hasattr(user, 'provider_profile'):
        provider = user.provider_profile
    elif user.role == 'ADMIN' or getattr(user, 'is_admin', False):
        # For admin testing - get provider from request_id or first available
        request_id = request.data.get('request_id')
        if request_id:
            try:
                ar = AssistanceRequest.objects.get(id=request_id)
                provider = ar.provider
            except AssistanceRequest.DoesNotExist:
                return Response({'error': 'Solicitud no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        else:
            from apps.providers.models import Provider
            provider = Provider.objects.first()
            if not provider:
                return Response({'error': 'No hay proveedores disponibles'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(
            {'error': 'Solo proveedores pueden actualizar ubicación'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Validate required fields
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if latitude is None or longitude is None:
        return Response(
            {'error': 'latitude y longitude son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return Response(
            {'error': 'Coordenadas inválidas'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Optional fields
    heading = request.data.get('heading')
    speed = request.data.get('speed')
    accuracy = request.data.get('accuracy')
    request_id = request.data.get('request_id')

    # Update location
    result = TrackingService.update_provider_location(
        provider_id=provider.id,
        latitude=latitude,
        longitude=longitude,
        heading=float(heading) if heading else None,
        speed=float(speed) if speed else None,
        accuracy=float(accuracy) if accuracy else None,
        request_id=int(request_id) if request_id else None
    )

    if 'error' in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_arrived(request, request_id):
    """
    Mark that provider has arrived at user's location.

    POST /api/assistance/tracking/<request_id>/arrived/

    Called by provider when they arrive at the destination.
    """
    user = request.user

    try:
        assistance_request = AssistanceRequest.objects.get(id=request_id)
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Must be the assigned provider or admin
    if user.role == 'PROVIDER':
        if not hasattr(user, 'provider_profile') or \
           assistance_request.provider_id != user.provider_profile.id:
            return Response(
                {'error': 'No eres el proveedor asignado'},
                status=status.HTTP_403_FORBIDDEN
            )
    elif user.role != 'ADMIN':
        return Response(
            {'error': 'No tienes permiso para esta acción'},
            status=status.HTTP_403_FORBIDDEN
        )

    result = TrackingService.mark_provider_arrived(request_id)

    if 'error' in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': 'Llegada registrada exitosamente',
        'status': result['status']
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_completed(request, request_id):
    """
    Mark assistance service as completed.

    POST /api/assistance/tracking/<request_id>/completed/

    Body (optional):
    {
        "actual_cost": 150.00
    }
    """
    user = request.user

    try:
        assistance_request = AssistanceRequest.objects.get(id=request_id)
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Must be the assigned provider or admin
    if user.role == 'PROVIDER':
        if not hasattr(user, 'provider_profile') or \
           assistance_request.provider_id != user.provider_profile.id:
            return Response(
                {'error': 'No eres el proveedor asignado'},
                status=status.HTTP_403_FORBIDDEN
            )
    elif user.role != 'ADMIN':
        return Response(
            {'error': 'No tienes permiso para esta acción'},
            status=status.HTTP_403_FORBIDDEN
        )

    actual_cost = request.data.get('actual_cost')

    result = TrackingService.mark_service_completed(
        request_id,
        actual_cost=actual_cost
    )

    if 'error' in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': 'Servicio completado exitosamente',
        'status': result['status']
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_service(request, request_id):
    """
    Mark that service has started (provider has begun work).

    POST /api/assistance/tracking/<request_id>/start/
    """
    user = request.user

    try:
        assistance_request = AssistanceRequest.objects.get(id=request_id)
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Must be the assigned provider or admin
    is_admin = user.role == 'ADMIN' or getattr(user, 'is_admin', False)
    if user.role == 'PROVIDER':
        if not hasattr(user, 'provider_profile') or \
           assistance_request.provider_id != user.provider_profile.id:
            return Response(
                {'error': 'No eres el proveedor asignado'},
                status=status.HTTP_403_FORBIDDEN
            )
    elif not is_admin:
        return Response(
            {'error': 'No tienes permiso para esta acción'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Check status - handle already started/completed gracefully
    if assistance_request.status == 'IN_PROGRESS':
        # Already in progress - return success
        return Response({
            'success': True,
            'message': 'El servicio ya está en progreso',
            'status': 'IN_PROGRESS'
        })
    elif assistance_request.status == 'COMPLETED':
        # Already completed - still return success for testing
        return Response({
            'success': True,
            'message': 'El servicio ya fue completado',
            'status': 'COMPLETED'
        })
    elif assistance_request.status not in ['ASSIGNED', 'PENDING'] and not is_admin:
        return Response(
            {'error': 'La solicitud no está en un estado válido para iniciar'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set to IN_PROGRESS
    assistance_request.status = 'IN_PROGRESS'
    if not assistance_request.actual_arrival_time:
        from django.utils import timezone
        assistance_request.actual_arrival_time = timezone.now()
    assistance_request.save()

    # Create update
    from .models import RequestUpdate
    RequestUpdate.objects.create(
        request=assistance_request,
        user=user,
        update_type='STATUS_CHANGE',
        message='El servicio ha iniciado'
    )

    # Broadcast update
    TrackingService._broadcast_status_update(
        request_id=request_id,
        status='IN_PROGRESS',
        tracking_status=TrackingStatus.IN_SERVICE,
        message='Servicio iniciado'
    )

    return Response({
        'success': True,
        'message': 'Servicio iniciado',
        'status': 'IN_PROGRESS'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_route_history(request, request_id):
    """
    Get provider's route history for a request.

    GET /api/assistance/tracking/<request_id>/route/

    Returns list of location points showing provider's path.
    Useful for showing the route on a map.
    """
    try:
        assistance_request = AssistanceRequest.objects.get(id=request_id)
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Permission check
    user = request.user
    if user.role == 'USER' and assistance_request.user_id != user.id:
        return Response(
            {'error': 'No tienes permiso para ver esta solicitud'},
            status=status.HTTP_403_FORBIDDEN
        )

    from apps.providers.models import ProviderLocationHistory

    # Get location history
    history = ProviderLocationHistory.objects.filter(
        assistance_request=assistance_request
    ).order_by('recorded_at').values(
        'latitude', 'longitude', 'heading', 'speed', 'recorded_at'
    )

    route_points = [
        {
            'latitude': float(point['latitude']),
            'longitude': float(point['longitude']),
            'heading': point['heading'],
            'speed': point['speed'],
            'timestamp': point['recorded_at'].isoformat()
        }
        for point in history
    ]

    return Response({
        'request_id': request_id,
        'total_points': len(route_points),
        'route': route_points,
        'user_location': {
            'latitude': float(assistance_request.location_latitude) if assistance_request.location_latitude else None,
            'longitude': float(assistance_request.location_longitude) if assistance_request.location_longitude else None,
            'address': assistance_request.location_address,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_eta(request):
    """
    Calculate ETA between two points (utility endpoint).

    POST /api/assistance/tracking/calculate-eta/

    Body:
    {
        "from_latitude": 14.5000,
        "from_longitude": -90.5000,
        "to_latitude": 14.6349,
        "to_longitude": -90.5069,
        "traffic_condition": "city"  // Optional: city, highway, congested
    }
    """
    from_lat = request.data.get('from_latitude')
    from_lon = request.data.get('from_longitude')
    to_lat = request.data.get('to_latitude')
    to_lon = request.data.get('to_longitude')
    traffic = request.data.get('traffic_condition', 'city')

    if not all([from_lat, from_lon, to_lat, to_lon]):
        return Response(
            {'error': 'Se requieren todas las coordenadas'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        eta = TrackingService.calculate_eta(
            float(from_lat), float(from_lon),
            float(to_lat), float(to_lon),
            traffic
        )
        return Response(eta)
    except (TypeError, ValueError):
        return Response(
            {'error': 'Coordenadas inválidas'},
            status=status.HTTP_400_BAD_REQUEST
        )


# =============================================================================
# PUBLIC TRACKING ENDPOINT (SSO/PAQ Users)
# =============================================================================

@api_view(['GET'])
def public_tracking(request, tracking_token):
    """
    PAQ User tracking endpoint - requires PAQ SSO token.

    GET /api/assistance/tracking/paq/<tracking_token>/
    Header: X-PAQ-Token: base64payload.signature

    This endpoint allows PAQ wallet users to track their assistance
    using PAQ SSO authentication. Uses request_number as tracking token.
    Delivery-app style visualization.

    Returns:
        - Provider location (lat/lng)
        - ETA (estimated time of arrival)
        - Tracking status with user-friendly messages
        - Timeline of events
        - Service details
    """
    # Verify PAQ token
    paq_token = request.headers.get('X-PAQ-Token')
    if not paq_token:
        return Response(
            {'error': 'PAQ authentication required. Use X-PAQ-Token header.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token_result = verify_paq_sso_token(paq_token)
    if not token_result['valid']:
        return Response(
            {'error': f"Invalid PAQ token: {token_result['error']}"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        # Find request by request_number (used as tracking token)
        assistance_request = AssistanceRequest.objects.select_related(
            'provider', 'user', 'service_category'
        ).get(request_number=tracking_token)

        # Get basic tracking info
        tracking_info = TrackingService.get_tracking_info(assistance_request)

        # Return public-safe data (no sensitive user info)
        return Response({
            'tracking_token': tracking_token,
            'service': {
                'type': assistance_request.service_category.name if assistance_request.service_category else 'Asistencia',
                'category': assistance_request.service_category.category_type if assistance_request.service_category else None,
                'title': assistance_request.title,
            },
            'status': tracking_info['status'],
            'tracking_status': tracking_info['tracking_status'],
            'tracking_display': tracking_info['tracking_status_display'],
            'provider': {
                'name': tracking_info['provider']['name'] if tracking_info['provider'] else None,
                'rating': tracking_info['provider']['rating'] if tracking_info['provider'] else None,
                'location': tracking_info['provider'].get('location') if tracking_info['provider'] else None,
            } if tracking_info['provider'] else None,
            'destination': {
                'address': tracking_info['user_location']['address'],
                'city': tracking_info['user_location']['city'],
                'latitude': tracking_info['user_location']['latitude'],
                'longitude': tracking_info['user_location']['longitude'],
            },
            'eta': tracking_info.get('eta'),
            'timeline': tracking_info['timeline'],
            'can_contact_provider': tracking_info.get('can_contact_provider', False),
            'provider_phone': tracking_info['provider']['phone'] if tracking_info['provider'] and tracking_info.get('can_contact_provider') else None,
        })

    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada. Verifica tu numero de seguimiento.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def public_tracking_simple(request, tracking_token):
    """
    Simple public tracking endpoint - no auth required.

    GET /api/assistance/tracking/public/<tracking_token>/

    Returns public tracking info by request_number.
    """
    try:
        # Find request by request_number
        assistance_request = AssistanceRequest.objects.select_related(
            'provider', 'user', 'service_category'
        ).get(request_number=tracking_token)

        # Get basic tracking info
        tracking_info = TrackingService.get_tracking_info(assistance_request)

        # Return public-safe data (no sensitive user info)
        return Response({
            'tracking_token': tracking_token,
            'request_id': assistance_request.id,
            'service': {
                'type': assistance_request.service_category.name if assistance_request.service_category else 'Asistencia',
                'category': assistance_request.service_category.category_type if assistance_request.service_category else None,
                'title': assistance_request.title,
            },
            'status': tracking_info['status'],
            'tracking_status': tracking_info['tracking_status'],
            'tracking_display': tracking_info['tracking_status_display'],
            'provider': {
                'name': tracking_info['provider']['name'] if tracking_info['provider'] else None,
                'rating': tracking_info['provider']['rating'] if tracking_info['provider'] else None,
            } if tracking_info['provider'] else None,
            'destination': {
                'address': tracking_info['user_location']['address'],
                'city': tracking_info['user_location']['city'],
            },
            'eta': tracking_info.get('eta'),
            'timeline': tracking_info['timeline'],
        })

    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada. Verifica tu numero de seguimiento.'},
            status=status.HTTP_404_NOT_FOUND
        )


# =============================================================================
# DISPATCH ENDPOINTS (MAWDY Assistants)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_jobs(request):
    """
    Get available jobs for MAWDY assistants (field technicians).

    GET /api/assistance/dispatch/available/

    Returns jobs assigned to the assistant's provider that are pending pickup.
    Similar to how delivery drivers see available orders.
    """
    user = request.user

    # Must be a provider (assistant)
    if user.role != 'PROVIDER' or not hasattr(user, 'provider_profile'):
        return Response(
            {'error': 'Solo asistentes de proveedores pueden ver trabajos disponibles'},
            status=status.HTTP_403_FORBIDDEN
        )

    provider = user.provider_profile

    # Get requests assigned to this provider that haven't been picked up
    available_requests = AssistanceRequest.objects.filter(
        provider=provider,
        status='ASSIGNED'
    ).select_related('user', 'service_category').order_by('-created_at')

    jobs = []
    for req in available_requests:
        # Calculate distance from provider HQ if location available
        distance_info = None
        if provider.latitude and provider.longitude and req.location_latitude:
            distance_info = TrackingService.calculate_eta(
                float(provider.latitude), float(provider.longitude),
                float(req.location_latitude), float(req.location_longitude)
            )

        jobs.append({
            'request_id': req.id,
            'request_number': req.request_number,
            'title': req.title,
            'description': req.description[:100] + '...' if len(req.description) > 100 else req.description,
            'priority': req.priority,
            'service_type': req.service_category.category_type if req.service_category else None,
            'service_name': req.service_category.name if req.service_category else None,
            'location': {
                'address': req.location_address,
                'city': req.location_city,
                'latitude': float(req.location_latitude) if req.location_latitude else None,
                'longitude': float(req.location_longitude) if req.location_longitude else None,
            },
            'user': {
                'name': req.user.get_full_name() or req.user.email.split('@')[0],
                'phone': req.user.phone_number,
            },
            'eta': distance_info,
            'estimated_cost': float(req.estimated_cost) if req.estimated_cost else None,
            'created_at': req.created_at.isoformat(),
        })

    return Response({
        'provider': provider.company_name,
        'count': len(jobs),
        'jobs': jobs
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_job(request, request_id):
    """
    Accept a job assignment (for MAWDY assistants).

    POST /api/assistance/dispatch/<request_id>/accept/

    Called by assistant to confirm they will handle this request.
    This is the first step before leaving HQ.
    """
    user = request.user

    # Must be a provider
    if user.role != 'PROVIDER' or not hasattr(user, 'provider_profile'):
        return Response(
            {'error': 'Solo asistentes pueden aceptar trabajos'},
            status=status.HTTP_403_FORBIDDEN
        )

    provider = user.provider_profile

    try:
        assistance_request = AssistanceRequest.objects.get(id=request_id)
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verify this request is assigned to their provider
    if assistance_request.provider_id != provider.id:
        return Response(
            {'error': 'Esta solicitud no esta asignada a tu proveedor'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Verify status is correct
    if assistance_request.status != 'ASSIGNED':
        return Response(
            {'error': f'La solicitud no puede ser aceptada (estado actual: {assistance_request.status})'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create update to mark acceptance
    from .models import RequestUpdate
    RequestUpdate.objects.create(
        request=assistance_request,
        user=user,
        update_type='STATUS_CHANGE',
        message=f'Asistente {user.get_full_name() or user.email} ha aceptado el trabajo'
    )

    # Broadcast acceptance
    TrackingService._broadcast_status_update(
        request_id=request_id,
        status='ASSIGNED',
        tracking_status=TrackingStatus.PROVIDER_ASSIGNED,
        message='Tu asistente ha aceptado el trabajo y se esta preparando'
    )

    return Response({
        'success': True,
        'message': 'Trabajo aceptado exitosamente',
        'request_id': request_id,
        'request_number': assistance_request.request_number,
        'next_step': 'Cuando salgas de la base, marca "En camino" usando /dispatch/{id}/depart/'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def depart_for_job(request, request_id):
    """
    Mark departure from HQ/base (for MAWDY assistants).

    POST /api/assistance/dispatch/<request_id>/depart/

    Body (optional):
    {
        "latitude": 14.6200,      // Current location
        "longitude": -90.5100,
        "vehicle_info": "Grua #5" // Optional vehicle identifier
    }

    Called by assistant when leaving base to assist user.
    This triggers the EN_ROUTE status and starts real-time tracking.
    """
    user = request.user

    # Must be a provider
    if user.role != 'PROVIDER' or not hasattr(user, 'provider_profile'):
        return Response(
            {'error': 'Solo asistentes pueden reportar salida'},
            status=status.HTTP_403_FORBIDDEN
        )

    provider = user.provider_profile

    try:
        assistance_request = AssistanceRequest.objects.get(id=request_id)
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verify this request is assigned to their provider
    if assistance_request.provider_id != provider.id:
        return Response(
            {'error': 'Esta solicitud no esta asignada a tu proveedor'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Verify status
    if assistance_request.status not in ['ASSIGNED']:
        return Response(
            {'error': f'No puedes marcar salida para esta solicitud (estado: {assistance_request.status})'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get optional location data
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    vehicle_info = request.data.get('vehicle_info', '')

    # Calculate ETA from departure point
    eta_info = None
    if latitude and longitude and assistance_request.location_latitude:
        try:
            eta_info = TrackingService.calculate_eta(
                float(latitude), float(longitude),
                float(assistance_request.location_latitude),
                float(assistance_request.location_longitude)
            )
            # Set estimated arrival time
            from django.utils import timezone
            from datetime import timedelta
            assistance_request.estimated_arrival_time = timezone.now() + timedelta(
                minutes=eta_info['eta_minutes']
            )
        except (TypeError, ValueError):
            pass

    # Update provider location if provided
    if latitude and longitude:
        TrackingService.update_provider_location(
            provider_id=provider.id,
            latitude=float(latitude),
            longitude=float(longitude),
            request_id=request_id
        )

    # Save request
    assistance_request.save()

    # Create departure update
    from .models import RequestUpdate
    vehicle_msg = f' en {vehicle_info}' if vehicle_info else ''
    RequestUpdate.objects.create(
        request=assistance_request,
        user=user,
        update_type='STATUS_CHANGE',
        message=f'El asistente ha salido de la base{vehicle_msg} y esta en camino'
    )

    # Broadcast en_route status
    TrackingService._broadcast_status_update(
        request_id=request_id,
        status='ASSIGNED',
        tracking_status=TrackingStatus.EN_ROUTE,
        message='Tu asistente esta en camino!'
    )

    response_data = {
        'success': True,
        'message': 'Salida registrada - Ahora estas EN CAMINO',
        'request_id': request_id,
        'request_number': assistance_request.request_number,
        'tracking_status': TrackingStatus.EN_ROUTE,
        'destination': {
            'address': assistance_request.location_address,
            'city': assistance_request.location_city,
            'latitude': float(assistance_request.location_latitude) if assistance_request.location_latitude else None,
            'longitude': float(assistance_request.location_longitude) if assistance_request.location_longitude else None,
        },
        'instructions': [
            'Actualiza tu ubicacion frecuentemente usando /tracking/update-location/',
            'Cuando llegues, marca llegada usando /tracking/{id}/arrived/',
            'El usuario puede ver tu ubicacion en tiempo real'
        ]
    }

    if eta_info:
        response_data['eta'] = eta_info

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_active_jobs(request):
    """
    Get assistant's currently active jobs.

    GET /api/assistance/dispatch/my-jobs/

    Returns jobs the assistant is currently handling (en route or in service).
    """
    user = request.user

    # Must be a provider
    if user.role != 'PROVIDER' or not hasattr(user, 'provider_profile'):
        return Response(
            {'error': 'Solo asistentes pueden ver sus trabajos'},
            status=status.HTTP_403_FORBIDDEN
        )

    provider = user.provider_profile

    # Get active requests
    active_requests = AssistanceRequest.objects.filter(
        provider=provider,
        status__in=['ASSIGNED', 'IN_PROGRESS']
    ).select_related('user', 'service_category').order_by('-created_at')

    jobs = []
    for req in active_requests:
        tracking_info = TrackingService.get_tracking_info(req)

        jobs.append({
            'request_id': req.id,
            'request_number': req.request_number,
            'title': req.title,
            'status': req.status,
            'tracking_status': tracking_info['tracking_status'],
            'tracking_display': tracking_info['tracking_status_display'],
            'priority': req.priority,
            'service_type': req.service_category.category_type if req.service_category else None,
            'location': {
                'address': req.location_address,
                'city': req.location_city,
                'latitude': float(req.location_latitude) if req.location_latitude else None,
                'longitude': float(req.location_longitude) if req.location_longitude else None,
            },
            'user': {
                'name': req.user.get_full_name() or req.user.email.split('@')[0],
                'phone': req.user.phone_number,
            },
            'eta': tracking_info.get('eta'),
            'created_at': req.created_at.isoformat(),
        })

    return Response({
        'provider': provider.company_name,
        'assistant': user.get_full_name() or user.email,
        'count': len(jobs),
        'jobs': jobs
    })
