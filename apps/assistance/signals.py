"""
Signals for assistance requests
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import AssistanceRequest, RequestUpdate
from django.conf import settings
import logging
import math

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


def calculate_eta_minutes(distance_km):
    """
    Calculate ETA in minutes based on distance.
    Assumes average speed of 30 km/h in city traffic.
    """
    avg_speed_kmh = 30
    eta_hours = distance_km / avg_speed_kmh
    eta_minutes = int(eta_hours * 60)
    # Minimum 5 minutes, add 5 minutes buffer
    return max(5, eta_minutes + 5)


@receiver(post_save, sender=AssistanceRequest)
def smart_tech_assignment(sender, instance, created, **kwargs):
    """
    Smart tech assignment logic:
    - If requesting user's phone is 30082653 (test user): Always assign to Mawdy
    - Otherwise: Find closest available technician based on lat/long proximity
    """
    if not created:
        return

    # Only auto-assign if no technician is assigned yet
    if instance.assigned_tech is not None:
        return

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Check if this is the test user (configurable phone)
        requesting_user = instance.user
        user_phone = requesting_user.phone_number.replace(' ', '').replace('-', '').replace('+502', '')
        is_test_user = user_phone == getattr(settings, 'PAQ_TEST_PHONE', '30082653')

        if is_test_user:
            # TEST USER: Always assign to Mawdy
            try:
                mawdy_user = User.objects.get(email='mawdy@segurifai.gt', role='MAWDY_FIELD_TECH')
            except User.DoesNotExist:
                logger.warning('Mawdy field technician not found. Run create_mawdy_tech command.')
                return

            if not mawdy_user.is_active:
                logger.info('Mawdy is not active at the moment')
                return

            # Mawdy location: Zone 10, Guatemala City
            mawdy_lat = 14.6025
            mawdy_lng = -90.5191

            # Test user location: Zone 15, Guatemala City
            test_user_lat = 14.5892
            test_user_lng = -90.4885

            # Calculate realistic distance and ETA
            distance_km = haversine_distance(mawdy_lat, mawdy_lng, test_user_lat, test_user_lng)
            eta_minutes = calculate_eta_minutes(distance_km)

            # Auto-assign Mawdy to the request
            instance.assigned_tech = mawdy_user
            instance.status = AssistanceRequest.Status.ASSIGNED
            instance.assigned_at = timezone.now()
            instance.estimated_arrival_time = timezone.now() + timedelta(minutes=eta_minutes)

            # Save without triggering signal again
            instance.save(update_fields=['assigned_tech', 'status', 'assigned_at', 'estimated_arrival_time'])

            # Create an update message
            RequestUpdate.objects.create(
                request=instance,
                user=mawdy_user,
                update_type=RequestUpdate.UpdateType.STATUS_CHANGE,
                message=f'Tu solicitud ha sido asignada a {mawdy_user.get_full_name()}. El tecnico esta en camino y llegara en aproximadamente {eta_minutes} minutos.',
                metadata={
                    'tech_id': mawdy_user.id,
                    'tech_name': mawdy_user.get_full_name(),
                    'tech_location': {
                        'lat': mawdy_lat,
                        'lng': mawdy_lng,
                        'zone': 'Zona 10, Guatemala City'
                    },
                    'user_location': {
                        'lat': test_user_lat,
                        'lng': test_user_lng,
                        'zone': 'Zona 15, Guatemala City'
                    },
                    'distance_km': round(distance_km, 2),
                    'eta_minutes': eta_minutes,
                    'estimated_arrival': instance.estimated_arrival_time.isoformat(),
                    'auto_assigned': True,
                    'assignment_reason': 'test_user'
                }
            )

            logger.info(f'Test user: Auto-assigned request {instance.request_number} to Mawdy ({mawdy_user.email})')
        else:
            # REGULAR USER: Proximity-based assignment
            # Get all active MAWDY field technicians
            available_techs = User.objects.filter(
                role='MAWDY_FIELD_TECH',
                is_active=True
            )

            if not available_techs.exists():
                logger.warning('No active MAWDY field technicians available')
                return

            # If request has location coordinates, find closest tech
            if instance.location_latitude and instance.location_longitude:
                request_lat = float(instance.location_latitude)
                request_lng = float(instance.location_longitude)

                closest_tech = None
                min_distance = float('inf')

                for tech in available_techs:
                    # Check if tech has location in their profile or recent tracking
                    # For Mawdy (our main tech), use Zone 10 coordinates
                    if tech.email == 'mawdy@segurifai.gt':
                        tech_lat = 14.6025  # Zone 10, Guatemala City
                        tech_lng = -90.5191
                    else:
                        # Default tech locations (Guatemala City center) for future techs
                        tech_lat = 14.6349  # Default: Guatemala City center
                        tech_lng = -90.5069

                    # Calculate distance using Haversine formula
                    distance = haversine_distance(request_lat, request_lng, tech_lat, tech_lng)

                    if distance < min_distance:
                        min_distance = distance
                        closest_tech = tech

                if closest_tech:
                    # Calculate realistic ETA based on distance
                    eta_minutes = calculate_eta_minutes(min_distance)

                    # Get tech location for metadata
                    if closest_tech.email == 'mawdy@segurifai.gt':
                        tech_lat = 14.6025  # Zone 10
                        tech_lng = -90.5191
                    else:
                        tech_lat = 14.6349
                        tech_lng = -90.5069

                    # Assign closest tech
                    instance.assigned_tech = closest_tech
                    instance.status = AssistanceRequest.Status.ASSIGNED
                    instance.assigned_at = timezone.now()
                    instance.estimated_arrival_time = timezone.now() + timedelta(minutes=eta_minutes)

                    # Save without triggering signal again
                    instance.save(update_fields=['assigned_tech', 'status', 'assigned_at', 'estimated_arrival_time'])

                    # Create an update message
                    RequestUpdate.objects.create(
                        request=instance,
                        user=closest_tech,
                        update_type=RequestUpdate.UpdateType.STATUS_CHANGE,
                        message=f'Tu solicitud ha sido asignada a {closest_tech.get_full_name()}. El tecnico esta en camino y llegara en aproximadamente {eta_minutes} minutos.',
                        metadata={
                            'tech_id': closest_tech.id,
                            'tech_name': closest_tech.get_full_name(),
                            'tech_location': {
                                'lat': tech_lat,
                                'lng': tech_lng
                            },
                            'user_location': {
                                'lat': request_lat,
                                'lng': request_lng
                            },
                            'estimated_arrival': instance.estimated_arrival_time.isoformat(),
                            'distance_km': round(min_distance, 2),
                            'eta_minutes': eta_minutes,
                            'auto_assigned': True,
                            'assignment_reason': 'proximity'
                        }
                    )

                    logger.info(
                        f'Proximity-based: Auto-assigned request {instance.request_number} to '
                        f'{closest_tech.get_full_name()} ({closest_tech.email}) - '
                        f'Distance: {min_distance:.2f}km, ETA: {eta_minutes} min'
                    )
            else:
                # No location coordinates, assign to first available tech (fallback to Mawdy)
                try:
                    mawdy_user = User.objects.get(email='mawdy@segurifai.gt', role='MAWDY_FIELD_TECH')
                    if mawdy_user.is_active:
                        eta_minutes = 20  # Default ETA

                        instance.assigned_tech = mawdy_user
                        instance.status = AssistanceRequest.Status.ASSIGNED
                        instance.assigned_at = timezone.now()
                        instance.estimated_arrival_time = timezone.now() + timedelta(minutes=eta_minutes)

                        instance.save(update_fields=['assigned_tech', 'status', 'assigned_at', 'estimated_arrival_time'])

                        RequestUpdate.objects.create(
                            request=instance,
                            user=mawdy_user,
                            update_type=RequestUpdate.UpdateType.STATUS_CHANGE,
                            message=f'Tu solicitud ha sido asignada a {mawdy_user.get_full_name()}. El tecnico esta en camino y llegara en aproximadamente {eta_minutes} minutos.',
                            metadata={
                                'tech_id': mawdy_user.id,
                                'tech_name': mawdy_user.get_full_name(),
                                'estimated_arrival': instance.estimated_arrival_time.isoformat(),
                                'auto_assigned': True,
                                'assignment_reason': 'fallback_no_location'
                            }
                        )

                        logger.info(f'Fallback: Auto-assigned request {instance.request_number} to Mawdy (no location data)')
                except User.DoesNotExist:
                    logger.warning('Mawdy field technician not found for fallback assignment')

    except Exception as e:
        logger.error(f'Error in smart tech assignment: {str(e)}')
