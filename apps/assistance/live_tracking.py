"""
Live Tracking Views - Food Delivery Style

Provides real-time tracking endpoints that users can poll for live updates,
similar to how food delivery apps show driver location moving on the map.

All access requires PAQ authentication - no truly public endpoints.
"""
from decimal import Decimal
from datetime import timedelta
import math

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AssistanceRequest
from apps.providers.models import Provider, ProviderLocation
from apps.users.paq_auth_views import verify_paq_sso_token
from apps.core.maps_service import calculate_eta, haversine_distance as maps_haversine


def get_eta_with_google_maps(provider_lat, provider_lng, dest_lat, dest_lng):
    """
    Get ETA using Google Maps API for accurate traffic-aware routing.
    Falls back to haversine calculation if API fails.
    """
    try:
        eta_result = calculate_eta(
            (float(provider_lat), float(provider_lng)),
            (float(dest_lat), float(dest_lng))
        )
        return {
            'distance_km': eta_result.get('distance_km', 0),
            'eta_minutes': eta_result.get('eta_minutes', 0),
            'source': eta_result.get('source', 'google_maps')
        }
    except Exception:
        # Fallback to haversine
        distance = haversine_distance(provider_lat, provider_lng, dest_lat, dest_lng)
        return {
            'distance_km': distance,
            'eta_minutes': calculate_eta_minutes(distance),
            'source': 'haversine_fallback'
        }


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    delta_lat = math.radians(float(lat2) - float(lat1))
    delta_lon = math.radians(float(lon2) - float(lon1))

    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def calculate_eta_minutes(distance_km, vehicle_type='MOTORCYCLE'):
    """Calculate ETA based on distance and vehicle type (fallback when no API)"""
    speeds = {
        'MOTORCYCLE': 35,  # km/h average in Guatemala City
        'CAR': 25,
        'VAN': 25,
        'TOW_TRUCK': 20,
        'AMBULANCE': 45,  # Emergency priority
    }
    speed = speeds.get(vehicle_type, 30)
    hours = distance_km / speed
    return max(1, round(hours * 60))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def live_tracking(request, request_id):
    """
    Get live tracking data for a request - Food Delivery Style.

    GET /api/assistance/live/{request_id}/

    Poll this endpoint every 3-5 seconds to get live location updates.

    Response includes:
    - Provider's exact current location (lat/lng)
    - Distance remaining to destination
    - ETA in minutes
    - Provider heading/direction
    - Status timeline
    - Provider info (name, photo, vehicle, rating)

    This is the MAIN endpoint for the tracking map UI.
    """
    try:
        assistance_request = AssistanceRequest.objects.select_related(
            'provider', 'user', 'service_category'
        ).get(id=request_id)

        # Permission: users see their own, admins see all
        if not request.user.is_admin and assistance_request.user_id != request.user.id:
            return Response(
                {'error': 'No autorizado'},
                status=status.HTTP_403_FORBIDDEN
            )

    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get destination (user's location)
    destination = {
        'latitude': float(assistance_request.location_latitude) if assistance_request.location_latitude else None,
        'longitude': float(assistance_request.location_longitude) if assistance_request.location_longitude else None,
        'address': assistance_request.location_address,
    }

    # Tracking status
    status_map = {
        'PENDING': {'code': 'searching', 'message': 'Buscando asistente cercano...', 'step': 1},
        'ASSIGNED': {'code': 'assigned', 'message': 'Asistente asignado, en camino', 'step': 2},
        'EN_ROUTE': {'code': 'en_route', 'message': 'Asistente en camino', 'step': 2},
        'ARRIVED': {'code': 'arrived', 'message': 'Asistente ha llegado', 'step': 3},
        'IN_PROGRESS': {'code': 'in_service', 'message': 'Servicio en progreso', 'step': 4},
        'COMPLETED': {'code': 'completed', 'message': 'Servicio completado', 'step': 5},
        'CANCELLED': {'code': 'cancelled', 'message': 'Solicitud cancelada', 'step': 0},
    }
    tracking_status = status_map.get(assistance_request.status, {'code': 'unknown', 'message': '', 'step': 0})

    # Provider/tech location
    provider_location = None
    provider_info = None
    distance_km = None
    eta_minutes = None
    heading = None
    vehicle_type = 'MOTORCYCLE'

    # Try field tech first (dispatch system)
    try:
        from apps.providers.dispatch import FieldTechProfile, JobOffer

        # Find the tech assigned to this request
        job = JobOffer.objects.filter(
            assistance_request=assistance_request,
            status__in=['ACCEPTED', 'EN_ROUTE', 'ARRIVED', 'IN_PROGRESS']
        ).select_related('tech', 'tech__user').first()

        if job and job.tech:
            tech = job.tech
            if tech.current_latitude and tech.current_longitude:
                provider_location = {
                    'latitude': float(tech.current_latitude),
                    'longitude': float(tech.current_longitude),
                    'updated_at': tech.last_location_update.isoformat() if tech.last_location_update else None,
                    'accuracy_meters': 10,  # Default
                }

                provider_info = {
                    'id': tech.id,
                    'name': f"{tech.user.first_name} {tech.user.last_name}",
                    'phone': tech.user.phone_number,
                    'photo_url': None,  # Add if you have profile photos
                    'vehicle_type': tech.vehicle_type,
                    'vehicle_plate': tech.vehicle_plate,
                    'rating': float(tech.rating),
                    'total_jobs': tech.total_jobs,
                }

                vehicle_type = tech.vehicle_type

                # Calculate distance and ETA using Google Maps API
                if destination['latitude'] and destination['longitude']:
                    eta_data = get_eta_with_google_maps(
                        tech.current_latitude, tech.current_longitude,
                        destination['latitude'], destination['longitude']
                    )
                    distance_km = eta_data['distance_km']
                    eta_minutes = eta_data['eta_minutes']

                # Get heading from location history if available
                from apps.providers.dispatch import FieldTechLocationHistory
                recent_locations = FieldTechLocationHistory.objects.filter(
                    tech=tech
                ).order_by('-timestamp')[:2]

                if len(recent_locations) >= 2:
                    # Calculate heading from movement
                    loc1 = recent_locations[1]
                    loc2 = recent_locations[0]
                    delta_lng = float(loc2.longitude) - float(loc1.longitude)
                    delta_lat = float(loc2.latitude) - float(loc1.latitude)
                    heading = math.degrees(math.atan2(delta_lng, delta_lat)) % 360

                # Update status based on job
                if job.status == 'EN_ROUTE':
                    tracking_status = {'code': 'en_route', 'message': 'Asistente en camino', 'step': 2}
                elif job.status == 'ARRIVED':
                    tracking_status = {'code': 'arrived', 'message': 'Asistente ha llegado', 'step': 3}
                elif job.status == 'IN_PROGRESS':
                    tracking_status = {'code': 'in_service', 'message': 'Servicio en progreso', 'step': 4}

    except ImportError:
        pass

    # Fallback to traditional provider
    if not provider_location and assistance_request.provider:
        provider = assistance_request.provider

        # Get latest location
        loc = ProviderLocation.objects.filter(
            provider=provider,
            is_online=True
        ).first()

        if loc:
            provider_location = {
                'latitude': float(loc.latitude),
                'longitude': float(loc.longitude),
                'updated_at': loc.last_updated.isoformat() if loc.last_updated else None,
                'accuracy_meters': float(loc.accuracy) if loc.accuracy else None,
            }

            if destination['latitude'] and destination['longitude']:
                eta_data = get_eta_with_google_maps(
                    loc.latitude, loc.longitude,
                    destination['latitude'], destination['longitude']
                )
                distance_km = eta_data['distance_km']
                eta_minutes = eta_data['eta_minutes']

            heading = float(loc.heading) if loc.heading else None

        provider_info = {
            'id': provider.id,
            'name': provider.company_name,
            'phone': provider.business_phone,
            'photo_url': None,
            'vehicle_type': 'VAN',
            'rating': float(provider.rating) if provider.rating else 4.5,
        }

    # Build timeline
    timeline = []
    timeline.append({
        'step': 1,
        'title': 'Solicitud Creada',
        'time': assistance_request.created_at.isoformat(),
        'completed': True,
    })

    if assistance_request.provider or provider_info:
        timeline.append({
            'step': 2,
            'title': 'Asistente Asignado',
            'time': assistance_request.assigned_at.isoformat() if assistance_request.assigned_at else None,
            'completed': True,
        })

    if tracking_status['step'] >= 3:
        timeline.append({
            'step': 3,
            'title': 'Asistente Llegó',
            'time': assistance_request.actual_arrival_time.isoformat() if assistance_request.actual_arrival_time else None,
            'completed': tracking_status['step'] >= 3,
        })

    if tracking_status['step'] >= 4:
        timeline.append({
            'step': 4,
            'title': 'Servicio en Progreso',
            'time': assistance_request.service_started_at.isoformat() if hasattr(assistance_request, 'service_started_at') and assistance_request.service_started_at else None,
            'completed': tracking_status['step'] >= 4,
        })

    if tracking_status['step'] >= 5:
        timeline.append({
            'step': 5,
            'title': 'Completado',
            'time': assistance_request.completion_time.isoformat() if assistance_request.completion_time else None,
            'completed': True,
        })

    return Response({
        'request_id': assistance_request.id,
        'request_number': assistance_request.request_number,

        'status': {
            'code': tracking_status['code'],
            'message': tracking_status['message'],
            'step': tracking_status['step'],
            'total_steps': 5,
        },

        'provider': provider_info,

        # Current location alias for frontend compatibility
        'current_location': {
            'latitude': provider_location['latitude'] if provider_location else None,
            'longitude': provider_location['longitude'] if provider_location else None,
            'last_update': provider_location['updated_at'] if provider_location else None,
        } if provider_location else None,

        'location': {
            'provider': provider_location,
            'destination': destination,
            'distance_km': round(distance_km, 2) if distance_km else None,
            'heading': round(heading, 1) if heading else None,
        },

        'eta': {
            'minutes': eta_minutes,
            'eta_minutes': eta_minutes,  # Alias for frontend compatibility
            'display': f"{eta_minutes} min" if eta_minutes else None,
            'distance_km': round(distance_km, 2) if distance_km else None,
        },

        'timeline': timeline,

        'service': {
            'type': assistance_request.service_category.category_type if assistance_request.service_category else None,
            'title': assistance_request.title,
            'description': assistance_request.description,
        },

        'meta': {
            'poll_interval_ms': 3000,  # Recommended poll interval
            'last_update': timezone.now().isoformat(),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def live_route_history(request, request_id):
    """
    Get the full route history for a request.

    GET /api/assistance/live/{request_id}/route/

    Returns all location points for drawing the route on a map.
    Useful for showing the provider's path traveled.
    """
    try:
        assistance_request = AssistanceRequest.objects.get(id=request_id)

        if not request.user.is_admin and assistance_request.user_id != request.user.id:
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

    except AssistanceRequest.DoesNotExist:
        return Response({'error': 'Solicitud no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    route_points = []

    # Try dispatch system first
    try:
        from apps.providers.dispatch import JobOffer, FieldTechLocationHistory

        job = JobOffer.objects.filter(
            assistance_request=assistance_request
        ).first()

        if job and job.tech:
            locations = FieldTechLocationHistory.objects.filter(
                tech=job.tech,
                timestamp__gte=job.created_at
            ).order_by('timestamp')

            route_points = [
                {
                    'lat': float(loc.latitude),
                    'lng': float(loc.longitude),
                    'time': loc.timestamp.isoformat(),
                }
                for loc in locations
            ]

    except ImportError:
        pass

    # Fallback to provider location history
    if not route_points and assistance_request.provider:
        from apps.providers.models import ProviderLocationHistory

        locations = ProviderLocationHistory.objects.filter(
            provider=assistance_request.provider,
            timestamp__gte=assistance_request.created_at
        ).order_by('timestamp')

        route_points = [
            {
                'lat': float(loc.latitude),
                'lng': float(loc.longitude),
                'time': loc.timestamp.isoformat(),
            }
            for loc in locations
        ]

    return Response({
        'request_id': request_id,
        'points_count': len(route_points),
        'route': route_points,
        'destination': {
            'lat': float(assistance_request.location_latitude) if assistance_request.location_latitude else None,
            'lng': float(assistance_request.location_longitude) if assistance_request.location_longitude else None,
        }
    })


@api_view(['GET'])
def paq_live_tracking(request, tracking_token):
    """
    PAQ User live tracking - requires PAQ SSO token.

    GET /api/assistance/live/paq/{tracking_token}/
    Header: X-PAQ-Token: base64payload.signature

    For PAQ users accessing SegurifAI.
    Uses request_number as the tracking identifier.
    Requires valid PAQ SSO token in header.
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
        assistance_request = AssistanceRequest.objects.select_related(
            'provider', 'service_category'
        ).get(request_number=tracking_token)
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Numero de solicitud no valido'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Same logic as live_tracking but without user-specific data
    destination = {
        'latitude': float(assistance_request.location_latitude) if assistance_request.location_latitude else None,
        'longitude': float(assistance_request.location_longitude) if assistance_request.location_longitude else None,
        'address': assistance_request.location_address,
    }

    status_map = {
        'PENDING': {'code': 'searching', 'message': 'Buscando asistente...'},
        'ASSIGNED': {'code': 'en_route', 'message': 'Asistente en camino'},
        'IN_PROGRESS': {'code': 'in_service', 'message': 'Servicio en progreso'},
        'COMPLETED': {'code': 'completed', 'message': 'Completado'},
    }
    tracking_status = status_map.get(assistance_request.status, {'code': 'unknown', 'message': ''})

    # Get provider location (simplified)
    provider_location = None
    eta_minutes = None

    try:
        from apps.providers.dispatch import JobOffer

        job = JobOffer.objects.filter(
            assistance_request=assistance_request,
            status__in=['ACCEPTED', 'EN_ROUTE', 'ARRIVED', 'IN_PROGRESS']
        ).select_related('tech').first()

        if job and job.tech and job.tech.current_latitude:
            provider_location = {
                'latitude': float(job.tech.current_latitude),
                'longitude': float(job.tech.current_longitude),
            }

            if destination['latitude']:
                distance = haversine_distance(
                    job.tech.current_latitude, job.tech.current_longitude,
                    destination['latitude'], destination['longitude']
                )
                eta_minutes = calculate_eta_minutes(distance, job.tech.vehicle_type)

    except ImportError:
        pass

    return Response({
        'request_number': assistance_request.request_number,
        'status': tracking_status,
        'provider_location': provider_location,
        'destination': destination,
        'eta_minutes': eta_minutes,
        'service_type': assistance_request.service_category.category_type if assistance_request.service_category else None,
    })
