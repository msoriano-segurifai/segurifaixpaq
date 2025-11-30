"""
Management command to clear test data and setup MAPFRE as the only provider
For Guatemala market with GTQ currency
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.providers.models import Provider, ProviderReview
from apps.assistance.models import AssistanceRequest, RequestUpdate, RequestDocument
from apps.services.models import ServiceCategory, ServicePlan, UserService
from apps.paq_wallet.models import WalletTransaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Clear all test data and setup MAPFRE as the only provider for Guatemala'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all test data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will DELETE ALL existing data including users, providers, '
                    'requests, and transactions.\n'
                    'Run with --confirm to proceed.'
                )
            )
            return

        self.stdout.write(self.style.WARNING('Starting data cleanup...'))

        with transaction.atomic():
            # Delete all data
            self.stdout.write('Deleting request documents...')
            RequestDocument.objects.all().delete()

            self.stdout.write('Deleting request updates...')
            RequestUpdate.objects.all().delete()

            self.stdout.write('Deleting assistance requests...')
            AssistanceRequest.objects.all().delete()

            self.stdout.write('Deleting wallet transactions...')
            WalletTransaction.objects.all().delete()

            self.stdout.write('Deleting user services (subscriptions)...')
            UserService.objects.all().delete()

            self.stdout.write('Deleting provider reviews...')
            ProviderReview.objects.all().delete()

            self.stdout.write('Deleting providers...')
            Provider.objects.all().delete()

            self.stdout.write('Deleting service plans...')
            ServicePlan.objects.all().delete()

            self.stdout.write('Deleting service categories...')
            ServiceCategory.objects.all().delete()

            # Delete all users
            self.stdout.write('Deleting all users...')
            User.objects.all().delete()

            # Create admin user
            self.stdout.write('Creating admin user...')
            admin = User.objects.create_superuser(
                email='admin@segurifai.com',
                password='Admin123!',
                first_name='Admin',
                last_name='SegurifAI',
                phone_number='+502 2222 2222',
                role='ADMIN'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin: {admin.email}'))

            # Create service categories
            self.stdout.write('Creating service categories...')

            roadside_cat = ServiceCategory.objects.create(
                name='Asistencia Vial',
                category_type='ROADSIDE',
                description='Asistencia en carretera para vehículos en Guatemala',
                icon='car',
                is_active=True
            )

            health_cat = ServiceCategory.objects.create(
                name='Asistencia Médica',
                category_type='HEALTH',
                description='Asistencia médica de emergencia en Guatemala',
                icon='medical',
                is_active=True
            )

            card_cat = ServiceCategory.objects.create(
                name='Seguro de Tarjeta',
                category_type='CARD_INSURANCE',
                description='Protección contra fraude y robo de tarjetas en Guatemala',
                icon='credit_card',
                is_active=True
            )

            self.stdout.write('Creating service plans (GTQ)...')

            # Create service plans (prices in GTQ - Guatemalan Quetzales)
            plans_data = [
                {
                    'category': roadside_cat,
                    'name': 'MAPFRE Asistencia Vial Básica',
                    'description': 'Asistencia vial básica 24/7 con cobertura nacional en Guatemala',
                    'price_monthly': 150.00,
                    'price_yearly': 1500.00,
                    'features': {
                        'grua': True,
                        'cambio_llanta': True,
                        'paso_corriente': True,
                        'suministro_gasolina': True,
                        'cerrajeria': True,
                        'servicio_24_7': True
                    },
                    'max_requests_per_month': 3,
                    'is_featured': False
                },
                {
                    'category': roadside_cat,
                    'name': 'MAPFRE Asistencia Vial Premium',
                    'description': 'Asistencia vial premium con cobertura extendida en Guatemala',
                    'price_monthly': 300.00,
                    'price_yearly': 3000.00,
                    'features': {
                        'grua': True,
                        'cambio_llanta': True,
                        'paso_corriente': True,
                        'suministro_gasolina': True,
                        'cerrajeria': True,
                        'servicio_24_7': True,
                        'auto_sustituto': True,
                        'hospedaje': True
                    },
                    'max_requests_per_month': 6,
                    'is_featured': True
                },
                {
                    'category': health_cat,
                    'name': 'MAPFRE Asistencia Médica Básica',
                    'description': 'Asistencia médica de emergencia 24/7 en Guatemala',
                    'price_monthly': 225.00,
                    'price_yearly': 2250.00,
                    'features': {
                        'ambulancia': True,
                        'consulta_telefonica': True,
                        'servicio_24_7': True
                    },
                    'max_requests_per_month': 2,
                    'is_featured': False
                },
                {
                    'category': health_cat,
                    'name': 'MAPFRE Asistencia Médica Premium',
                    'description': 'Asistencia médica completa con cobertura extendida en Guatemala',
                    'price_monthly': 450.00,
                    'price_yearly': 4500.00,
                    'features': {
                        'ambulancia': True,
                        'consulta_telefonica': True,
                        'servicio_24_7': True,
                        'medico_domicilio': True,
                        'medicamentos': True,
                        'analisis_clinicos': True
                    },
                    'max_requests_per_month': 5,
                    'is_featured': True
                },
                {
                    'category': card_cat,
                    'name': 'MAPFRE Seguro de Tarjeta Básico',
                    'description': 'Protección contra fraude y robo de tarjetas en Guatemala',
                    'price_monthly': 75.00,
                    'price_yearly': 750.00,
                    'features': {
                        'proteccion_fraude': True,
                        'reposicion_tarjeta': True,
                        'asesoria_legal': True
                    },
                    'max_requests_per_month': 2,
                    'is_featured': False
                },
                {
                    'category': card_cat,
                    'name': 'MAPFRE Seguro de Tarjeta Premium',
                    'description': 'Protección completa contra fraude con cobertura extendida en Guatemala',
                    'price_monthly': 150.00,
                    'price_yearly': 1500.00,
                    'features': {
                        'proteccion_fraude': True,
                        'reposicion_tarjeta': True,
                        'asesoria_legal': True,
                        'monitoreo_credito': True,
                        'seguro_compras': True
                    },
                    'max_requests_per_month': 5,
                    'is_featured': True
                }
            ]

            for plan_data in plans_data:
                plan = ServicePlan.objects.create(**plan_data)
                self.stdout.write(f'  Created plan: {plan.name}')

            # Create MAPFRE provider
            self.stdout.write('Creating MAPFRE Guatemala provider...')
            mapfre = Provider.objects.create(
                user=admin,
                company_name='MAPFRE Guatemala',
                business_license='MAPFRE-GT-2024',
                tax_id='12345678-9',
                business_phone='+502 2328 0000',
                business_email='asistencia@mapfre.com.gt',
                website='https://www.mapfre.com.gt',
                address='7a Avenida 5-10, Zona 4, Edificio Centro Financiero',
                city='Ciudad de Guatemala',
                state='Guatemala',
                postal_code='01004',
                country='Guatemala',
                latitude=14.6349,
                longitude=-90.5069,
                service_radius_km=150,  # 150 km radius - covers most of Guatemala
                service_areas=['Ciudad de Guatemala', 'Antigua Guatemala', 'Quetzaltenango', 'Escuintla', 'Mixco', 'Villa Nueva'],
                is_available=True,
                status='ACTIVE',
                verification_notes='MAPFRE es una aseguradora global con más de 85 años de experiencia. '
                    'En Guatemala, ofrecemos servicios de asistencia vial, médica y protección '
                    'de tarjetas con cobertura nacional 24/7.'
            )

            # Set working hours (24/7)
            mapfre.working_hours = {
                'monday': {'start': '00:00', 'end': '23:59'},
                'tuesday': {'start': '00:00', 'end': '23:59'},
                'wednesday': {'start': '00:00', 'end': '23:59'},
                'thursday': {'start': '00:00', 'end': '23:59'},
                'friday': {'start': '00:00', 'end': '23:59'},
                'saturday': {'start': '00:00', 'end': '23:59'},
                'sunday': {'start': '00:00', 'end': '23:59'}
            }
            mapfre.save()

            # Add all service categories to provider
            mapfre.service_categories.add(roadside_cat, health_cat, card_cat)

            self.stdout.write(self.style.SUCCESS(f'Created provider: {mapfre.company_name}'))

            self.stdout.write(
                self.style.SUCCESS(
                    '\n========================================\n'
                    'Guatemala Production Data Setup Complete!\n'
                    '========================================\n\n'
                    'Admin credentials:\n'
                    '  Email: admin@segurifai.com\n'
                    '  Password: Admin123!\n\n'
                    'Provider:\n'
                    f'  Company: {mapfre.company_name}\n'
                    f'  Status: {mapfre.status}\n'
                    f'  Location: Ciudad de Guatemala, Guatemala\n'
                    f'  Available: {mapfre.is_available}\n\n'
                    f'Service Categories: {ServiceCategory.objects.count()}\n'
                    f'Service Plans: {ServicePlan.objects.count()} plans created (GTQ)\n\n'
                    'PAQ Wallet Integration: Configured\n'
                    '  ID Code: 89E3AF\n'
                    '  Currency: GTQ (Guatemalan Quetzal)\n'
                )
            )
