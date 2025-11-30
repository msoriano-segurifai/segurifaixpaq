"""
Management command to create Mawdy test field technician
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.providers.models import Provider, ProviderLocation
from apps.services.models import ServiceCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Create Mawdy test field technician for auto-accepting requests'

    def handle(self, *args, **options):
        self.stdout.write('Creating Mawdy field technician...')

        with transaction.atomic():
            # Check if Mawdy already exists
            if User.objects.filter(email='mawdy@segurifai.com').exists():
                self.stdout.write(self.style.WARNING('Mawdy already exists, updating...'))
                user = User.objects.get(email='mawdy@segurifai.com')
                provider = user.provider_profile
            else:
                # Create user account for Mawdy
                user = User.objects.create_user(
                    email='mawdy@segurifai.com',
                    password='mawdy2024',
                    first_name='Mawdy',
                    last_name='Technician',
                    phone='+50212345678',
                    role='PROVIDER',
                    is_verified=True
                )
                self.stdout.write(f'  Created user: {user.email}')

                # Create provider profile
                provider = Provider.objects.create(
                    user=user,
                    company_name='Mawdy Field Services',
                    business_license='MAWDY-001',
                    tax_id='123456789',
                    business_phone='+50212345678',
                    business_email='mawdy@segurifai.com',
                    address='Zona 10, Ciudad de Guatemala',
                    city='Guatemala City',
                    state='Guatemala',
                    postal_code='01010',
                    country='Guatemala',
                    latitude=14.5995,  # Guatemala City center
                    longitude=-90.5187,
                    service_radius_km=100,
                    service_areas=['Guatemala City', 'Mixco', 'Villa Nueva', 'San Miguel Petapa', 'Zona 1-25'],
                    is_available=True,
                    working_hours={
                        'monday': {'start': '00:00', 'end': '23:59'},
                        'tuesday': {'start': '00:00', 'end': '23:59'},
                        'wednesday': {'start': '00:00', 'end': '23:59'},
                        'thursday': {'start': '00:00', 'end': '23:59'},
                        'friday': {'start': '00:00', 'end': '23:59'},
                        'saturday': {'start': '00:00', 'end': '23:59'},
                        'sunday': {'start': '00:00', 'end': '23:59'}
                    },
                    rating=4.95,
                    total_reviews=247,
                    total_completed=532,
                    status='ACTIVE',
                    verification_notes='Test field technician for auto-accepting requests'
                )
                self.stdout.write(f'  Created provider: {provider.company_name}')

            # Add all service categories to provider
            all_categories = ServiceCategory.objects.filter(is_active=True)
            provider.service_categories.set(all_categories)
            self.stdout.write(f'  Added {all_categories.count()} service categories')

            # Create or update current location
            location, created = ProviderLocation.objects.update_or_create(
                provider=provider,
                defaults={
                    'latitude': 14.5995,
                    'longitude': -90.5187,
                    'heading': 0.0,
                    'speed': 0.0,
                    'accuracy': 10.0,
                    'is_online': True
                }
            )
            self.stdout.write(f'  {"Created" if created else "Updated"} location')

        self.stdout.write(self.style.SUCCESS(
            f'\nMawdy field technician ready!'
        ))
        self.stdout.write(f'  Email: mawdy@segurifai.com')
        self.stdout.write(f'  Password: mawdy2024')
        self.stdout.write(f'  Provider ID: {provider.id}')
        self.stdout.write(f'  Status: {provider.status}')
        self.stdout.write(f'  Available: {provider.is_available}')
