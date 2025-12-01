"""
GPS Tracking Simulation Script
Simulates a technician driving towards the user's location.
Run this script to move the tech closer every 3 seconds.
"""
import os
import sys
import django
import time
from decimal import Decimal

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'segurifai_backend.settings')
django.setup()

from apps.providers.models import Provider, ProviderLocation
from apps.assistance.models import AssistanceRequest

# Get the active request (ASSIGNED or EN_ROUTE)
request = AssistanceRequest.objects.filter(
    status__in=['ASSIGNED', 'EN_ROUTE']
).order_by('-created_at').first()

if not request:
    print("No active ASSIGNED or EN_ROUTE request found!")
    print("Create a new request or assign a provider to an existing one.")
    exit(1)

print(f"Simulating tracking for request: {request.request_number}")
print(f"Provider: {request.provider.company_name if request.provider else 'None'}")
print(f"User location: {request.location_latitude}, {request.location_longitude}")

if not request.provider:
    print("No provider assigned!")
    exit(1)

# Get or create provider location
provider = request.provider
user_lat = float(request.location_latitude)
user_lng = float(request.location_longitude)

# Starting position (about 1.5km away)
tech_lat = 14.6200
tech_lng = -90.5150

# Calculate step sizes to reach user in about 20 steps (for longer demo)
num_steps = 20
lat_step = (user_lat - tech_lat) / num_steps
lng_step = (user_lng - tech_lng) / num_steps

print(f"\nStarting simulation...")
print(f"Tech starts at: {tech_lat}, {tech_lng}")
print(f"User is at: {user_lat}, {user_lng}")
print(f"Steps: lat={lat_step:.6f}, lng={lng_step:.6f}")
print(f"Total steps: {num_steps} (about {num_steps * 3} seconds)")
print("\nPress Ctrl+C to stop\n")

step = 0
try:
    while step < num_steps:
        # Update location
        tech_lat += lat_step
        tech_lng += lng_step

        # Calculate approximate distance
        dist_lat = abs(user_lat - tech_lat) * 111  # km per degree
        dist_lng = abs(user_lng - tech_lng) * 85   # approximate at this latitude
        distance = (dist_lat**2 + dist_lng**2)**0.5

        # Estimate ETA based on 40 km/h speed
        eta_minutes = int((distance / 40) * 60) + 1

        # Update provider location
        loc, _ = ProviderLocation.objects.update_or_create(
            provider=provider,
            defaults={
                'latitude': Decimal(str(tech_lat)),
                'longitude': Decimal(str(tech_lng)),
                'is_online': True,
                'heading': 0,
                'speed': 40,
                'accuracy': 5
            }
        )

        step += 1
        print(f"Step {step}/{num_steps}: Tech at ({tech_lat:.6f}, {tech_lng:.6f}) - {distance:.2f}km away - ETA: {eta_minutes} min")

        # Wait 3 seconds before next update (faster for testing)
        time.sleep(3)

except KeyboardInterrupt:
    print("\nSimulation stopped by user")

# Mark as arrived when close enough
if step >= num_steps:
    print("\nTech has arrived! Updating request status to ARRIVED...")
    request.status = 'ARRIVED'
    request.save()
    print(f"Request status: {request.status}")

print("\nDone!")
