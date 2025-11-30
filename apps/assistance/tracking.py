"""
Real-Time Assistance Tracking Service

Provides delivery-app style tracking for assistance requests:
- Real-time provider location
- ETA calculations
- Status updates
- Route progress tracking
"""
import math
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from django.utils import timezone
from django.db.models import Avg

# Google Maps integration for accurate ETA
try:
    from apps.core.maps_service import calculate_eta as google_maps_eta
    GOOGLE_MAPS_AVAILABLE = True
except ImportError:
    GOOGLE_MAPS_AVAILABLE = False
    google_maps_eta = None

# Optional channels support for WebSocket broadcasting
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    get_channel_layer = lambda: None
    async_to_sync = lambda f: f

logger = logging.getLogger(__name__)


@dataclass
class TrackingStatus:
    """Tracking status stages similar to delivery apps"""
    SEARCHING = 'SEARCHING'           # Looking for available provider
    PROVIDER_ASSIGNED = 'PROVIDER_ASSIGNED'  # Provider accepted, preparing
    EN_ROUTE = 'EN_ROUTE'             # Provider is on the way
    ARRIVING = 'ARRIVING'             # Provider is very close (< 500m)
    ARRIVED = 'ARRIVED'               # Provider has arrived
    IN_SERVICE = 'IN_SERVICE'         # Service in progress
    COMPLETED = 'COMPLETED'           # Service completed


class TrackingService:
    """
    Service for real-time assistance tracking.

    Features:
    - Calculate ETA based on distance and traffic conditions
    - Track provider location updates
    - Broadcast updates to connected clients
    - Provide tracking timeline/milestones
    """

    # Average speeds for ETA calculation (km/h)
    AVERAGE_SPEEDS = {
        'city': 25,        # Urban traffic
        'highway': 60,     # Highway/rural
        'congested': 15,   # Heavy traffic
    }

    # Distance thresholds (meters)
    ARRIVING_THRESHOLD = 500    # Show "arriving" when within 500m
    ARRIVED_THRESHOLD = 50      # Consider arrived when within 50m

    @classmethod
    def calculate_distance(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(float(lat1))
        lat2_rad = math.radians(float(lat2))
        delta_lat = math.radians(float(lat2) - float(lat1))
        delta_lon = math.radians(float(lon2) - float(lon1))

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @classmethod
    def calculate_eta(
        cls,
        provider_lat: float,
        provider_lon: float,
        destination_lat: float,
        destination_lon: float,
        traffic_condition: str = 'city'
    ) -> Dict[str, Any]:
        """
        Calculate estimated time of arrival using Google Maps API when available.

        Args:
            provider_lat/lon: Provider's current location
            destination_lat/lon: User's location
            traffic_condition: 'city', 'highway', or 'congested'

        Returns:
            Dictionary with ETA details
        """
        # Try Google Maps API first for accurate traffic-aware ETA
        if GOOGLE_MAPS_AVAILABLE and google_maps_eta:
            try:
                result = google_maps_eta(
                    (float(provider_lat), float(provider_lon)),
                    (float(destination_lat), float(destination_lon))
                )
                if result and result.get('source') != 'haversine_fallback':
                    eta_minutes = result.get('eta_minutes', 0)
                    distance_km = result.get('distance_km', 0)
                    arrival_time = timezone.now() + timedelta(minutes=eta_minutes)

                    return {
                        'distance_km': round(distance_km, 2),
                        'distance_m': int(distance_km * 1000),
                        'eta_minutes': eta_minutes,
                        'eta_range': {
                            'min': max(1, eta_minutes - 2),
                            'max': eta_minutes + 5
                        },
                        'estimated_arrival': arrival_time.isoformat(),
                        'traffic_condition': 'google_maps_live',
                        'source': 'google_maps'
                    }
            except Exception as e:
                logger.warning(f"Google Maps ETA failed, using fallback: {e}")

        # Fallback to haversine calculation
        distance_km = cls.calculate_distance(
            provider_lat, provider_lon,
            destination_lat, destination_lon
        )

        # Get speed based on traffic
        speed_kmh = cls.AVERAGE_SPEEDS.get(traffic_condition, cls.AVERAGE_SPEEDS['city'])

        # Calculate time in minutes
        if speed_kmh > 0:
            eta_hours = distance_km / speed_kmh
            eta_minutes = int(eta_hours * 60)
        else:
            eta_minutes = 0

        # Add buffer for Guatemala traffic unpredictability
        eta_minutes_with_buffer = int(eta_minutes * 1.2)  # 20% buffer

        # Calculate arrival time
        arrival_time = timezone.now() + timedelta(minutes=eta_minutes_with_buffer)

        return {
            'distance_km': round(distance_km, 2),
            'distance_m': int(distance_km * 1000),
            'eta_minutes': eta_minutes_with_buffer,
            'eta_range': {
                'min': max(1, eta_minutes),
                'max': eta_minutes_with_buffer + 5
            },
            'estimated_arrival': arrival_time.isoformat(),
            'traffic_condition': traffic_condition,
            'speed_kmh': speed_kmh,
            'source': 'haversine_fallback'
        }

    @classmethod
    def get_tracking_status(cls, request) -> str:
        """
        Determine current tracking status based on request state.

        Args:
            request: AssistanceRequest instance

        Returns:
            TrackingStatus value
        """
        if request.status == 'PENDING':
            return TrackingStatus.SEARCHING

        if request.status == 'ASSIGNED':
            # Check if provider is en route
            if request.provider and hasattr(request.provider, 'current_location'):
                location = request.provider.current_location
                if location and request.location_latitude:
                    distance = cls.calculate_distance(
                        location.latitude, location.longitude,
                        request.location_latitude, request.location_longitude
                    ) * 1000  # Convert to meters

                    if distance < cls.ARRIVED_THRESHOLD:
                        return TrackingStatus.ARRIVED
                    elif distance < cls.ARRIVING_THRESHOLD:
                        return TrackingStatus.ARRIVING
                    else:
                        return TrackingStatus.EN_ROUTE
            return TrackingStatus.PROVIDER_ASSIGNED

        if request.status == 'IN_PROGRESS':
            if request.actual_arrival_time:
                return TrackingStatus.IN_SERVICE
            return TrackingStatus.ARRIVED

        if request.status == 'COMPLETED':
            return TrackingStatus.COMPLETED

        return TrackingStatus.SEARCHING

    @classmethod
    def get_tracking_info(cls, request) -> Dict[str, Any]:
        """
        Get complete tracking information for a request.

        Args:
            request: AssistanceRequest instance

        Returns:
            Dictionary with full tracking details
        """
        from apps.providers.models import ProviderLocation

        tracking_status = cls.get_tracking_status(request)

        result = {
            'request_id': request.id,
            'request_number': request.request_number,
            'status': request.status,
            'tracking_status': tracking_status,
            'tracking_status_display': cls._get_status_display(tracking_status),
            'created_at': request.created_at.isoformat(),
            'user_location': {
                'address': request.location_address,
                'city': request.location_city,
                'latitude': float(request.location_latitude) if request.location_latitude else None,
                'longitude': float(request.location_longitude) if request.location_longitude else None,
            },
            'provider': None,
            'eta': None,
            'timeline': cls._build_timeline(request),
            'can_contact_provider': False,
            'can_cancel': request.status in ['PENDING', 'ASSIGNED'],
        }

        # Add provider info if assigned
        if request.provider:
            provider = request.provider
            result['provider'] = {
                'id': provider.id,
                'name': provider.company_name,
                'phone': provider.business_phone,
                'rating': float(provider.rating),
                'total_completed': provider.total_completed,
                'vehicle_info': None,  # Could be added for roadside
            }
            result['can_contact_provider'] = True

            # Get provider's current location
            try:
                location = ProviderLocation.objects.get(provider=provider)
                result['provider']['location'] = {
                    'latitude': float(location.latitude),
                    'longitude': float(location.longitude),
                    'heading': location.heading,
                    'speed': location.speed,
                    'last_updated': location.last_updated.isoformat(),
                    'is_online': location.is_online,
                }

                # Calculate ETA if we have both locations
                if request.location_latitude and request.location_longitude:
                    result['eta'] = cls.calculate_eta(
                        location.latitude, location.longitude,
                        request.location_latitude, request.location_longitude
                    )
            except ProviderLocation.DoesNotExist:
                pass

        # Add estimated arrival if set
        if request.estimated_arrival_time:
            result['estimated_arrival_time'] = request.estimated_arrival_time.isoformat()

        # Add actual arrival if set
        if request.actual_arrival_time:
            result['actual_arrival_time'] = request.actual_arrival_time.isoformat()

        return result

    @classmethod
    def _get_status_display(cls, tracking_status: str) -> Dict[str, str]:
        """Get user-friendly status display"""
        displays = {
            TrackingStatus.SEARCHING: {
                'title': 'Buscando proveedor',
                'description': 'Estamos buscando un proveedor disponible cerca de ti',
                'icon': 'search'
            },
            TrackingStatus.PROVIDER_ASSIGNED: {
                'title': 'Proveedor asignado',
                'description': 'Un proveedor ha aceptado tu solicitud y se está preparando',
                'icon': 'check-circle'
            },
            TrackingStatus.EN_ROUTE: {
                'title': 'En camino',
                'description': 'El proveedor está en camino hacia tu ubicación',
                'icon': 'navigation'
            },
            TrackingStatus.ARRIVING: {
                'title': 'Llegando',
                'description': 'El proveedor está muy cerca, prepárate para recibirlo',
                'icon': 'map-pin'
            },
            TrackingStatus.ARRIVED: {
                'title': 'Ha llegado',
                'description': 'El proveedor ha llegado a tu ubicación',
                'icon': 'flag'
            },
            TrackingStatus.IN_SERVICE: {
                'title': 'En servicio',
                'description': 'El servicio está en progreso',
                'icon': 'tool'
            },
            TrackingStatus.COMPLETED: {
                'title': 'Completado',
                'description': 'El servicio ha sido completado exitosamente',
                'icon': 'check-square'
            },
        }
        return displays.get(tracking_status, displays[TrackingStatus.SEARCHING])

    @classmethod
    def _build_timeline(cls, request) -> list:
        """Build timeline of events for the request"""
        timeline = []

        # Request created
        timeline.append({
            'event': 'request_created',
            'title': 'Solicitud creada',
            'timestamp': request.created_at.isoformat(),
            'completed': True,
        })

        # Provider assigned
        if request.provider:
            # Find when provider was assigned from updates
            from .models import RequestUpdate
            assignment = RequestUpdate.objects.filter(
                request=request,
                update_type='STATUS_CHANGE',
                message__icontains='asignado'
            ).first()

            timeline.append({
                'event': 'provider_assigned',
                'title': f'Proveedor asignado: {request.provider.company_name}',
                'timestamp': assignment.created_at.isoformat() if assignment else request.updated_at.isoformat(),
                'completed': True,
            })
        else:
            timeline.append({
                'event': 'provider_assigned',
                'title': 'Esperando proveedor',
                'timestamp': None,
                'completed': False,
            })

        # En route
        timeline.append({
            'event': 'en_route',
            'title': 'En camino',
            'timestamp': None,
            'completed': request.status in ['IN_PROGRESS', 'COMPLETED'] or
                        cls.get_tracking_status(request) in [
                            TrackingStatus.EN_ROUTE,
                            TrackingStatus.ARRIVING,
                            TrackingStatus.ARRIVED,
                            TrackingStatus.IN_SERVICE,
                            TrackingStatus.COMPLETED
                        ],
        })

        # Arrived
        timeline.append({
            'event': 'arrived',
            'title': 'Llegó al destino',
            'timestamp': request.actual_arrival_time.isoformat() if request.actual_arrival_time else None,
            'completed': request.actual_arrival_time is not None,
        })

        # Completed
        timeline.append({
            'event': 'completed',
            'title': 'Servicio completado',
            'timestamp': request.completion_time.isoformat() if request.completion_time else None,
            'completed': request.status == 'COMPLETED',
        })

        return timeline

    @classmethod
    def update_provider_location(
        cls,
        provider_id: int,
        latitude: float,
        longitude: float,
        heading: float = None,
        speed: float = None,
        accuracy: float = None,
        request_id: int = None
    ) -> Dict[str, Any]:
        """
        Update provider location and broadcast to subscribers.

        Args:
            provider_id: Provider's ID
            latitude/longitude: New coordinates
            heading: Direction of movement (degrees)
            speed: Current speed (km/h)
            accuracy: GPS accuracy (meters)
            request_id: Associated request ID (optional)

        Returns:
            Updated tracking info
        """
        from apps.providers.models import Provider, ProviderLocation, ProviderLocationHistory
        from .models import AssistanceRequest

        try:
            provider = Provider.objects.get(id=provider_id)
        except Provider.DoesNotExist:
            return {'error': 'Provider not found'}

        # Update or create current location
        location, created = ProviderLocation.objects.update_or_create(
            provider=provider,
            defaults={
                'latitude': latitude,
                'longitude': longitude,
                'heading': heading,
                'speed': speed,
                'accuracy': accuracy,
                'is_online': True,
                'last_updated': timezone.now()
            }
        )

        # Save to history if there's an active request
        if request_id:
            try:
                request = AssistanceRequest.objects.get(id=request_id)
                ProviderLocationHistory.objects.create(
                    provider=provider,
                    assistance_request=request,
                    latitude=latitude,
                    longitude=longitude,
                    heading=heading,
                    speed=speed
                )

                # Calculate ETA and broadcast
                if request.location_latitude and request.location_longitude:
                    eta_info = cls.calculate_eta(
                        latitude, longitude,
                        request.location_latitude, request.location_longitude
                    )

                    # Check if status should change
                    distance_m = eta_info['distance_m']
                    if distance_m < cls.ARRIVED_THRESHOLD and request.status == 'ASSIGNED':
                        # Auto-update to arrived
                        request.actual_arrival_time = timezone.now()
                        request.status = 'IN_PROGRESS'
                        request.save()

                    # Broadcast to request room
                    cls._broadcast_location_update(
                        request_id=request_id,
                        provider_id=provider_id,
                        latitude=latitude,
                        longitude=longitude,
                        heading=heading,
                        speed=speed,
                        eta=eta_info,
                        tracking_status=cls.get_tracking_status(request)
                    )

                    return {
                        'success': True,
                        'location': {
                            'latitude': latitude,
                            'longitude': longitude,
                            'heading': heading,
                            'speed': speed,
                        },
                        'eta': eta_info,
                        'tracking_status': cls.get_tracking_status(request)
                    }
            except AssistanceRequest.DoesNotExist:
                pass

        return {
            'success': True,
            'location': {
                'latitude': latitude,
                'longitude': longitude,
                'heading': heading,
                'speed': speed,
            }
        }

    @classmethod
    def _broadcast_location_update(
        cls,
        request_id: int,
        provider_id: int,
        latitude: float,
        longitude: float,
        heading: float,
        speed: float,
        eta: Dict,
        tracking_status: str
    ):
        """Broadcast location update via WebSocket"""
        channel_layer = get_channel_layer()

        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'tracking_request_{request_id}',
                {
                    'type': 'location_message',
                    'provider_id': provider_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'heading': heading,
                    'speed': speed,
                    'eta': eta,
                    'tracking_status': tracking_status,
                    'timestamp': timezone.now().isoformat()
                }
            )

    @classmethod
    def mark_provider_arrived(cls, request_id: int) -> Dict[str, Any]:
        """Mark that provider has arrived at location"""
        from .models import AssistanceRequest, RequestUpdate

        try:
            request = AssistanceRequest.objects.get(id=request_id)
        except AssistanceRequest.DoesNotExist:
            return {'error': 'Request not found'}

        request.actual_arrival_time = timezone.now()
        if request.status == 'ASSIGNED':
            request.status = 'IN_PROGRESS'
        request.save()

        # Create update
        RequestUpdate.objects.create(
            request=request,
            user=request.provider.user if request.provider else request.user,
            update_type='ARRIVAL_UPDATE',
            message='El proveedor ha llegado a tu ubicación'
        )

        # Broadcast arrival
        cls._broadcast_status_update(
            request_id=request_id,
            status=request.status,
            tracking_status=TrackingStatus.ARRIVED,
            message='El proveedor ha llegado'
        )

        return {'success': True, 'status': request.status}

    @classmethod
    def mark_service_completed(cls, request_id: int, actual_cost: Decimal = None) -> Dict[str, Any]:
        """Mark service as completed"""
        from .models import AssistanceRequest, RequestUpdate

        try:
            request = AssistanceRequest.objects.get(id=request_id)
        except AssistanceRequest.DoesNotExist:
            return {'error': 'Request not found'}

        request.status = 'COMPLETED'
        request.completion_time = timezone.now()
        if actual_cost:
            request.actual_cost = actual_cost
        request.save()

        # Update provider stats
        if request.provider:
            request.provider.total_completed += 1
            request.provider.save()

        # Create update
        RequestUpdate.objects.create(
            request=request,
            user=request.provider.user if request.provider else request.user,
            update_type='STATUS_CHANGE',
            message='Servicio completado exitosamente'
        )

        # Broadcast completion
        cls._broadcast_status_update(
            request_id=request_id,
            status='COMPLETED',
            tracking_status=TrackingStatus.COMPLETED,
            message='Servicio completado'
        )

        return {'success': True, 'status': 'COMPLETED'}

    @classmethod
    def _broadcast_status_update(
        cls,
        request_id: int,
        status: str,
        tracking_status: str,
        message: str
    ):
        """Broadcast status update via WebSocket"""
        channel_layer = get_channel_layer()

        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'tracking_request_{request_id}',
                {
                    'type': 'status_message',
                    'status': status,
                    'tracking_status': tracking_status,
                    'message': message,
                    'timestamp': timezone.now().isoformat()
                }
            )

            # Also send to assistance room
            async_to_sync(channel_layer.group_send)(
                f'assistance_{request_id}',
                {
                    'type': 'request_update',
                    'update_type': 'STATUS_CHANGE',
                    'data': {
                        'status': status,
                        'tracking_status': tracking_status,
                        'message': message
                    },
                    'timestamp': timezone.now().isoformat()
                }
            )
