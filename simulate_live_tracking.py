"""
Live GPS Tracking Simulation - Uber Eats Style
Simulates a technician driving towards the user with continuous updates.
Creates a new request if needed, assigns a provider, and moves the tech.

IMPORTANT: This simulation ONLY works for test user 30082653.
For all production users, real-time tracking is provided by MAPFRE
field technicians through the integrated dispatch system.
"""
import os
import django
import time
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'segurifai_backend.settings')
django.setup()

from apps.providers.models import Provider, ProviderLocation
from apps.assistance.models import AssistanceRequest
from apps.services.models import ServiceCategory, UserService
from apps.users.models import User
from django.utils import timezone
from datetime import timedelta

def create_test_request():
    """Create a new test assistance request for user 30082653"""
    user = User.objects.filter(phone_number__icontains='30082653').first()
    if not user:
        print("Test user 30082653 not found!")
        return None

    user_sub = UserService.objects.filter(
        user=user,
        status='ACTIVE',
        plan__category__category_type='ROADSIDE'
    ).first()

    if not user_sub:
        print("No active ROADSIDE subscription for user!")
        return None

    roadside_cat = ServiceCategory.objects.filter(category_type='ROADSIDE').first()
    roadside_provider = Provider.objects.filter(
        service_categories__category_type='ROADSIDE',
        status='ACTIVE'
    ).first()

    if not roadside_provider:
        print("No active ROADSIDE provider found!")
        return None

    # User location in Guatemala City
    user_lat = Decimal('14.6349')
    user_lng = Decimal('-90.5069')

    # Create request
    import string
    req_num = 'REQ-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    request = AssistanceRequest.objects.create(
        user=user,
        user_service=user_sub,
        service_category=roadside_cat,
        provider=roadside_provider,
        title='Prueba GPS Tracking - Grua',
        description='Simulacion de tracking en vivo',
        request_number=req_num,
        priority='HIGH',
        location_address='Zona 10, Ciudad de Guatemala',
        location_city='Guatemala City',
        location_state='Guatemala',
        location_latitude=user_lat,
        location_longitude=user_lng,
        vehicle_make='Toyota',
        vehicle_model='Corolla',
        vehicle_year=2020,
        vehicle_plate='P-TEST123',
        incident_type='TOWING',
        status='ASSIGNED',
        assigned_at=timezone.now(),
        estimated_arrival_time=timezone.now() + timedelta(minutes=10)
    )

    print(f"Created new request: {request.request_number} (ID: {request.id})")
    return request

def simulate_movement(request, total_duration_seconds=120, update_interval=3):
    """
    Simulate tech movement towards user location.

    Args:
        request: AssistanceRequest object
        total_duration_seconds: Total time to reach user (default 2 minutes)
        update_interval: Seconds between location updates (default 3s)
    """
    if not request or not request.provider:
        print("No valid request/provider!")
        return

    provider = request.provider
    user_lat = float(request.location_latitude)
    user_lng = float(request.location_longitude)

    # Tech starts about 2km away (south-west of user)
    tech_lat = user_lat - 0.018  # About 2km south
    tech_lng = user_lng - 0.012  # About 1km west

    # Calculate steps
    num_steps = total_duration_seconds // update_interval
    lat_step = (user_lat - tech_lat) / num_steps
    lng_step = (user_lng - tech_lng) / num_steps

    print(f"\n{'='*60}")
    print(f"SIMULACION DE TRACKING GPS EN VIVO")
    print(f"{'='*60}")
    print(f"Request: {request.request_number}")
    print(f"Provider: {provider.company_name}")
    print(f"User location: {user_lat:.6f}, {user_lng:.6f}")
    print(f"Tech start: {tech_lat:.6f}, {tech_lng:.6f}")
    print(f"Total steps: {num_steps}, Update interval: {update_interval}s")
    print(f"{'='*60}")
    print("\nPress Ctrl+C to stop\n")

    # Update request status to EN_ROUTE
    request.status = 'EN_ROUTE'
    request.save()

    step = 0
    try:
        while step < num_steps:
            # Update location
            tech_lat += lat_step
            tech_lng += lng_step

            # Add some random variation for realism
            tech_lat += random.uniform(-0.0002, 0.0002)
            tech_lng += random.uniform(-0.0002, 0.0002)

            # Calculate distance
            dist_lat = abs(user_lat - tech_lat) * 111  # km per degree lat
            dist_lng = abs(user_lng - tech_lng) * 85   # approximate at this latitude
            distance = (dist_lat**2 + dist_lng**2)**0.5

            # Estimate ETA
            speed = random.uniform(25, 45)  # Variable speed
            eta_minutes = max(1, int((distance / speed) * 60))

            # Update provider location
            ProviderLocation.objects.update_or_create(
                provider=provider,
                defaults={
                    'latitude': Decimal(str(round(tech_lat, 6))),
                    'longitude': Decimal(str(round(tech_lng, 6))),
                    'is_online': True,
                    'heading': random.randint(0, 360),
                    'speed': Decimal(str(round(speed, 1))),
                    'accuracy': Decimal('5.0'),
                    'last_updated': timezone.now()
                }
            )

            step += 1
            status_bar = '>' * (step * 30 // num_steps) + '-' * (30 - step * 30 // num_steps)
            print(f"\r[{status_bar}] Step {step}/{num_steps} | {distance:.2f}km | ETA: {eta_minutes}min | Speed: {speed:.0f}km/h", end='', flush=True)

            time.sleep(update_interval)

    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user")
        return

    # Mark as arrived
    print(f"\n\n{'='*60}")
    print("TECNICO HA LLEGADO!")
    print(f"{'='*60}")

    request.status = 'ARRIVED'
    request.actual_arrival_time = timezone.now()
    request.save()

    # Update location to exact user location
    ProviderLocation.objects.update_or_create(
        provider=provider,
        defaults={
            'latitude': request.location_latitude,
            'longitude': request.location_longitude,
            'is_online': True,
            'heading': 0,
            'speed': Decimal('0'),
            'accuracy': Decimal('5.0'),
            'last_updated': timezone.now()
        }
    )

    print(f"Request {request.request_number} status: {request.status}")
    print("\nView tracking in the app at: http://localhost:5173/app/requests")

def main():
    print("\n" + "="*60)
    print("SEGURIFAI - SIMULADOR DE TRACKING GPS")
    print("="*60 + "\n")

    # Check for existing active request
    request = AssistanceRequest.objects.filter(
        status__in=['PENDING', 'ASSIGNED', 'EN_ROUTE'],
        user__phone_number__icontains='30082653'
    ).order_by('-created_at').first()

    if request:
        print(f"Found existing active request: {request.request_number}")
        choice = input("Use existing request? (y/n): ").strip().lower()
        if choice != 'y':
            request = create_test_request()
    else:
        print("No active request found.")
        request = create_test_request()

    if request:
        try:
            duration = int(input("\nTracking duration in seconds (default 60): ").strip() or "60")
        except ValueError:
            duration = 60

        try:
            interval = int(input("Update interval in seconds (default 3): ").strip() or "3")
        except ValueError:
            interval = 3

        simulate_movement(request, duration, interval)
    else:
        print("Could not create or find a valid request.")

if __name__ == '__main__':
    main()
