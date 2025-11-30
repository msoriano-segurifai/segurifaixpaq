"""
Seed Data Management Command for SegurifAI x PAQ

Creates test data for development and Postman testing.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear  # Clear existing data first
"""
import random
from decimal import Decimal
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with test data for development and Postman testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting database seeding...'))

        with transaction.atomic():
            if options['clear']:
                self.clear_data()

            self.create_users()
            self.create_service_categories()
            self.create_providers()
            self.create_mawdy_assistants()
            self.create_educational_modules()
            self.create_promo_codes()
            self.create_sample_requests()
            self.create_dispatch_ready_requests()
            self.create_analytics_data()

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.print_credentials()

    def clear_data(self):
        """Clear existing test data"""
        self.stdout.write('Clearing existing data...')
        # Clear in proper order due to foreign key constraints
        from apps.assistance.models import AssistanceRequest
        from apps.services.models import UserService
        from apps.gamification.models import UserPoints, UserAchievement, UserProgress
        from apps.promotions.models import PromoCodeUsage

        # Clear related data first
        try:
            AssistanceRequest.objects.all().delete()
            UserService.objects.all().delete()
            UserPoints.objects.all().delete()
            UserAchievement.objects.all().delete()
            UserProgress.objects.all().delete()
            PromoCodeUsage.objects.all().delete()
        except Exception as e:
            self.stdout.write(f'  Warning clearing related data: {e}')

        # Don't delete superusers
        User.objects.filter(is_superuser=False).delete()

    def create_users(self):
        """Create test users"""
        self.stdout.write('Creating users...')

        # SegurifAI Admin - Platform owner with full analytics
        self.admin_user, created = User.objects.get_or_create(
            email='admin@segurifai.gt',
            defaults={
                'first_name': 'Admin',
                'last_name': 'SegurifAI',
                'phone_number': '+50212340001',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            self.admin_user.set_password('AdminPass123!')
            self.admin_user.save()
            self.stdout.write(f'  Created SegurifAI admin: {self.admin_user.email}')

        # MAWDY Admin - Provider admin with provider analytics
        self.mawdy_admin, created = User.objects.get_or_create(
            email='admin@mawdy.gt',
            defaults={
                'first_name': 'Admin',
                'last_name': 'MAWDY',
                'phone_number': '+50222850001',
                'role': 'ADMIN',
                'is_staff': True,
                'is_active': True,
            }
        )
        if created:
            self.mawdy_admin.set_password('MawdyAdmin123!')
            self.mawdy_admin.save()
            self.stdout.write(f'  Created MAWDY admin: {self.mawdy_admin.email}')

        # Regular test user - Use phone 3008 2653 for PAQ token testing
        self.test_user, created = User.objects.get_or_create(
            email='test@segurifai.gt',
            defaults={
                'first_name': 'Juan',
                'last_name': 'Perez',
                'phone_number': '+50230082653',  # 3008 2653 for PAQ token testing
                'role': 'USER',
                'paq_wallet_id': 'PAQ-3008-2653',
                'is_active': True,
            }
        )
        if created:
            self.test_user.set_password('TestPass123!')
            self.test_user.save()
            self.stdout.write(f'  Created user: {self.test_user.email} (Phone: 3008 2653 for PAQ testing)')

        # MAWDY Provider user (company account)
        self.provider_user, created = User.objects.get_or_create(
            email='soporte@mawdy.gt',
            defaults={
                'first_name': 'MAWDY',
                'last_name': 'Guatemala',
                'phone_number': '+50223456789',
                'role': 'PROVIDER',
                'is_active': True,
            }
        )
        if created:
            self.provider_user.set_password('MawdyPass123!')
            self.provider_user.save()
            self.stdout.write(f'  Created MAWDY provider user: {self.provider_user.email}')

        # Additional test users for leaderboard
        test_users_data = [
            ('maria@test.gt', 'Maria', 'Garcia'),
            ('pedro@test.gt', 'Pedro', 'Lopez'),
            ('ana@test.gt', 'Ana', 'Martinez'),
        ]
        for email, first_name, last_name in test_users_data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone_number': f'+5027{hash(email) % 10000000:07d}',
                    'role': 'USER',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('TestPass123!')
                user.save()

    def create_service_categories(self):
        """Create service categories"""
        self.stdout.write('Creating service categories...')

        from apps.services.models import ServiceCategory, ServicePlan

        categories_data = [
            {
                'name': 'Asistencia Vehicular',
                'category_type': 'ROADSIDE',
                'description': 'Servicios de asistencia para vehiculos',
                'icon': 'car',
            },
            {
                'name': 'Asistencia en Salud',
                'category_type': 'HEALTH',
                'description': 'Servicios de asistencia medica',
                'icon': 'health',
            },
            {
                'name': 'Seguro de Tarjeta',
                'category_type': 'CARD_INSURANCE',
                'description': 'Seguro para tarjetas de credito/debito',
                'icon': 'credit-card',
            },
        ]

        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                category_type=cat_data['category_type'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'  Created category: {category.name}')

            # Create plans for this category
            if cat_data['category_type'] == 'ROADSIDE':
                self.vehicular_category = category
                plans = [
                    {
                        'name': 'MAWDY Drive Inclusion',
                        'price_monthly': Decimal('24.41'),
                        'price_yearly': Decimal('292.95'),
                        'description': 'Plan basico de asistencia vehicular',
                        'features': ['Grua hasta 50km', 'Paso de corriente', 'Cambio de llanta', 'Cerrajeria'],
                    },
                    {
                        'name': 'MAWDY Drive Optional',
                        'price_monthly': Decimal('29.06'),
                        'price_yearly': Decimal('348.75'),
                        'description': 'Plan completo de asistencia vehicular',
                        'features': ['Grua hasta 100km', 'Paso de corriente', 'Cambio de llanta', 'Cerrajeria', 'Combustible', 'Hotel por averia'],
                        'is_featured': True,
                    },
                ]
                for plan_data in plans:
                    plan, created = ServicePlan.objects.get_or_create(
                        category=category,
                        name=plan_data['name'],
                        defaults={
                            'price_monthly': plan_data['price_monthly'],
                            'price_yearly': plan_data['price_yearly'],
                            'description': plan_data['description'],
                            'features': plan_data.get('features', []),
                            'is_active': True,
                            'is_featured': plan_data.get('is_featured', False),
                        }
                    )

    def create_providers(self):
        """Create MAWDY as the only provider"""
        self.stdout.write('Creating MAWDY provider...')

        from apps.providers.models import Provider, ProviderLocation

        # Use provider_user for MAWDY
        self.provider, created = Provider.objects.get_or_create(
            user=self.provider_user,
            defaults={
                'company_name': 'MAWDY Guatemala',
                'business_license': 'MAWDY-GT-001',
                'tax_id': 'MAWDY-NIT-001',
                'business_phone': '+50223456789',
                'business_email': 'soporte@mawdy.gt',
                'address': 'Zona 13, Guatemala City',
                'city': 'Guatemala City',
                'state': 'Guatemala',
                'postal_code': '01013',
                'status': 'ACTIVE',
                'rating': Decimal('4.9'),
                'total_completed': 5000,
            }
        )
        if created:
            self.stdout.write(f'  Created provider: {self.provider.company_name}')

            # Create location for MAWDY
            ProviderLocation.objects.create(
                provider=self.provider,
                latitude=Decimal('14.6200'),
                longitude=Decimal('-90.5100'),
                is_online=True,
            )

    def create_mawdy_assistants(self):
        """Create MAWDY field assistants (like delivery drivers)"""
        self.stdout.write('Creating MAWDY assistants...')

        from apps.providers.models import Provider, ProviderLocation

        # MAWDY Assistants - Field technicians who respond to requests
        # Each assistant gets their own provider profile to use the dispatch system
        assistants_data = [
            {
                'email': 'grua1@mawdy.gt',
                'first_name': 'Carlos',
                'last_name': 'Mendez',
                'phone': '+50222851001',
                'specialty': 'Grua',
                'company_name': 'MAWDY Grua #1',
                'license': 'MAWDY-GRUA-001',
            },
            {
                'email': 'grua2@mawdy.gt',
                'first_name': 'Roberto',
                'last_name': 'Gonzalez',
                'phone': '+50222851002',
                'specialty': 'Grua',
                'company_name': 'MAWDY Grua #2',
                'license': 'MAWDY-GRUA-002',
            },
            {
                'email': 'mecanico1@mawdy.gt',
                'first_name': 'Luis',
                'last_name': 'Ramirez',
                'phone': '+50222851003',
                'specialty': 'Mecanica',
                'company_name': 'MAWDY Mecanico #1',
                'license': 'MAWDY-MEC-001',
            },
            {
                'email': 'ambulancia1@mawdy.gt',
                'first_name': 'Miguel',
                'last_name': 'Torres',
                'phone': '+50222851004',
                'specialty': 'Ambulancia',
                'company_name': 'MAWDY Ambulancia #1',
                'license': 'MAWDY-AMB-001',
            },
        ]

        self.mawdy_assistants = []
        for assistant in assistants_data:
            user, created = User.objects.get_or_create(
                email=assistant['email'],
                defaults={
                    'first_name': assistant['first_name'],
                    'last_name': assistant['last_name'],
                    'phone_number': assistant['phone'],
                    'role': 'PROVIDER',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('Asistente123!')
                user.save()
                self.stdout.write(f'  Created MAWDY assistant: {user.email} ({assistant["specialty"]})')

            # Create provider profile for this assistant
            provider, prov_created = Provider.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': assistant['company_name'],
                    'business_license': assistant['license'],
                    'business_phone': assistant['phone'],
                    'business_email': assistant['email'],
                    'address': 'Zona 13, Guatemala City (MAWDY HQ)',
                    'city': 'Guatemala City',
                    'state': 'Guatemala',
                    'postal_code': '01013',
                    'latitude': Decimal('14.6200'),
                    'longitude': Decimal('-90.5100'),
                    'status': 'ACTIVE',
                    'rating': Decimal('4.8'),
                    'total_completed': random.randint(100, 500),
                }
            )
            if prov_created:
                # Create location for tracking
                ProviderLocation.objects.create(
                    provider=provider,
                    latitude=Decimal('14.6200'),
                    longitude=Decimal('-90.5100'),
                    is_online=True,
                )
                self.stdout.write(f'    -> Provider profile created: {provider.company_name}')

            self.mawdy_assistants.append({'user': user, 'provider': provider})

    def create_educational_modules(self):
        """Create educational modules for gamification"""
        self.stdout.write('Creating educational modules...')

        from apps.gamification.models import (
            EducationalModule, QuizQuestion,
            Achievement, UserPoints
        )

        modules_data = [
            {
                'titulo': 'Introduccion a SegurifAI',
                'descripcion': 'Aprende como funciona la plataforma y sus beneficios',
                'categoria': 'PREVENCION',
                'dificultad': 'PRINCIPIANTE',
                'orden': 1,
                'puntos_completar': 50,
                'duracion_minutos': 5,
                'contenido': '# Bienvenido a SegurifAI\n\nSegurifAI es tu plataforma de asistencia integral.\n\n## Servicios\n- Asistencia Vehicular con MAWDY\n- Pagos con PAQ Wallet',
                'questions': [
                    {'pregunta': 'Que tipo de asistencia ofrece SegurifAI?', 'opcion_a': 'Solo vehicular', 'opcion_b': 'Solo salud', 'opcion_c': 'Vehicular y salud', 'opcion_d': 'Solo hogar', 'respuesta_correcta': 'C'},
                    {'pregunta': 'Con que billetera digital trabaja SegurifAI?', 'opcion_a': 'PayPal', 'opcion_b': 'PAQ Wallet', 'opcion_c': 'Venmo', 'opcion_d': 'Zelle', 'respuesta_correcta': 'B'},
                ]
            },
            {
                'titulo': 'Asistencia Vehicular con MAWDY',
                'descripcion': 'Todo sobre los servicios de asistencia vehicular MAWDY',
                'categoria': 'SEGURIDAD_VIAL',
                'dificultad': 'PRINCIPIANTE',
                'orden': 2,
                'puntos_completar': 75,
                'duracion_minutos': 10,
                'contenido': '# MAWDY Drive\n\n## Servicios Incluidos\n- Grua hasta 50/100 km\n- Paso de corriente\n- Cambio de llanta\n- Cerrajeria',
                'questions': [
                    {'pregunta': 'Cual es el limite de kilometros para grua en MAWDY Drive basico?', 'opcion_a': '25 km', 'opcion_b': '50 km', 'opcion_c': '100 km', 'opcion_d': 'Ilimitado', 'respuesta_correcta': 'B'},
                    {'pregunta': 'Que servicio NO esta incluido en MAWDY Drive basico?', 'opcion_a': 'Grua', 'opcion_b': 'Cerrajeria', 'opcion_c': 'Hotel por averia', 'opcion_d': 'Paso de corriente', 'respuesta_correcta': 'C'},
                ]
            },
            {
                'titulo': 'Seguridad Vial en Guatemala',
                'descripcion': 'Consejos de seguridad para conducir en Guatemala',
                'categoria': 'SEGURIDAD_VIAL',
                'dificultad': 'INTERMEDIO',
                'orden': 3,
                'puntos_completar': 100,
                'duracion_minutos': 15,
                'contenido': '# Seguridad Vial\n\n## Numeros de Emergencia\n- 911: Emergencias\n- 1551: Bomberos\n\n## Documentos Obligatorios\n- Licencia\n- Tarjeta de circulacion\n- Seguro',
                'questions': [
                    {'pregunta': 'Cual es el numero de emergencias en Guatemala?', 'opcion_a': '911', 'opcion_b': '110', 'opcion_c': '123', 'opcion_d': '100', 'respuesta_correcta': 'A'},
                    {'pregunta': 'Que debes hacer primero en un accidente?', 'opcion_a': 'Mover el vehiculo', 'opcion_b': 'Tomar fotos', 'opcion_c': 'Verificar si hay heridos', 'opcion_d': 'Llamar al seguro', 'respuesta_correcta': 'C'},
                ]
            },
        ]

        for mod_data in modules_data:
            questions = mod_data.pop('questions')
            module, created = EducationalModule.objects.get_or_create(
                titulo=mod_data['titulo'],
                defaults=mod_data
            )
            if created:
                self.stdout.write(f'  Created module: {module.titulo}')

                # Create questions
                for i, q_data in enumerate(questions):
                    QuizQuestion.objects.create(
                        modulo=module,
                        orden=i + 1,
                        **q_data
                    )

        # Create achievements
        achievements_data = [
            {'nombre': 'Primer Paso', 'descripcion': 'Completa tu primer modulo', 'condicion': 'modulos_completados >= 1', 'icono': 'star', 'puntos_bonus': 25},
            {'nombre': 'Estudiante Dedicado', 'descripcion': 'Completa 3 modulos', 'condicion': 'modulos_completados >= 3', 'icono': 'book', 'puntos_bonus': 50},
            {'nombre': 'Quiz Master', 'descripcion': 'Obtén 100% en un quiz', 'condicion': 'quiz_perfecto == True', 'icono': 'trophy', 'puntos_bonus': 30},
            {'nombre': 'Racha de 7 dias', 'descripcion': 'Aprende 7 dias seguidos', 'condicion': 'racha_dias >= 7', 'icono': 'fire', 'puntos_bonus': 75},
        ]

        for ach_data in achievements_data:
            Achievement.objects.get_or_create(
                nombre=ach_data['nombre'],
                defaults=ach_data
            )

        # Create user points for test users
        UserPoints.objects.get_or_create(
            user=self.test_user,
            defaults={
                'puntos_totales': 125,
                'nivel': 'APRENDIZ',
                'racha_dias': 3,
            }
        )

    def create_promo_codes(self):
        """Create promotional codes"""
        self.stdout.write('Creating promo codes...')

        from apps.promotions.models import PromoCode

        now = timezone.now()
        # NOTE: Promo codes are ONLY granted through gamification rewards
        # No public welcome codes - users earn discounts by advancing in education
        codes_data = [
            # Gamification reward: Awarded at 100 points (APRENDIZ level)
            {
                'code': 'APRENDIZ5',
                'name': 'Recompensa Nivel Aprendiz',
                'description': 'Q5 de descuento por alcanzar nivel Aprendiz (100 puntos)',
                'discount_type': 'FIXED_AMOUNT',
                'discount_value': Decimal('5.00'),
                'max_uses': None,  # Unlimited, controlled by gamification system
                'max_uses_per_user': 1,
                'valid_from': now,
                'valid_until': now + timedelta(days=365),
                'status': 'ACTIVE',
            },
            # Gamification reward: Awarded at 250 points (CONOCEDOR level)
            {
                'code': 'CONOCEDOR10',
                'name': 'Recompensa Nivel Conocedor',
                'description': '10% de descuento por alcanzar nivel Conocedor (250 puntos)',
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('10.00'),
                'max_discount_amount': Decimal('25.00'),
                'max_uses': None,
                'max_uses_per_user': 1,
                'valid_from': now,
                'valid_until': now + timedelta(days=365),
                'status': 'ACTIVE',
            },
            # Gamification reward: Awarded at 500 points (EXPERTO level)
            {
                'code': 'EXPERTO15',
                'name': 'Recompensa Nivel Experto',
                'description': '15% de descuento por alcanzar nivel Experto (500 puntos)',
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('15.00'),
                'max_discount_amount': Decimal('50.00'),
                'max_uses': None,
                'max_uses_per_user': 1,
                'valid_from': now,
                'valid_until': now + timedelta(days=365),
                'status': 'ACTIVE',
            },
            # Gamification reward: Awarded at 1000 points (MAESTRO level)
            {
                'code': 'MAESTRO25',
                'name': 'Recompensa Nivel Maestro',
                'description': 'Q25 de descuento por alcanzar nivel Maestro (1000 puntos)',
                'discount_type': 'FIXED_AMOUNT',
                'discount_value': Decimal('25.00'),
                'max_uses': None,
                'max_uses_per_user': 1,
                'valid_from': now,
                'valid_until': now + timedelta(days=365),
                'status': 'ACTIVE',
            },
        ]

        for code_data in codes_data:
            code, created = PromoCode.objects.get_or_create(
                code=code_data['code'],
                defaults=code_data
            )
            if created:
                self.stdout.write(f'  Created promo code: {code.code}')

    def create_sample_requests(self):
        """Create sample subscription and assistance request"""
        self.stdout.write('Creating sample subscription and request...')

        from apps.assistance.models import AssistanceRequest
        from apps.services.models import ServicePlan, UserService
        from datetime import date

        # First create a subscription for test user
        try:
            plan = ServicePlan.objects.filter(category=self.vehicular_category).first()
            if plan:
                subscription, sub_created = UserService.objects.get_or_create(
                    user=self.test_user,
                    plan=plan,
                    status='ACTIVE',
                    defaults={
                        'start_date': date.today(),
                        'auto_renew': True,
                    }
                )
                if sub_created:
                    self.stdout.write(f'  Created subscription: {subscription.plan.name}')

                # Create a sample request
                request, req_created = AssistanceRequest.objects.get_or_create(
                    user=self.test_user,
                    title='Necesito grua - Prueba',
                    defaults={
                        'user_service': subscription,
                        'service_category': self.vehicular_category,
                        'description': 'Solicitud de prueba para testing de API',
                        'location_latitude': Decimal('14.6349'),
                        'location_longitude': Decimal('-90.5069'),
                        'location_address': 'Zona 10, Ciudad de Guatemala',
                        'priority': 'MEDIUM',
                        'status': 'PENDING',
                    }
                )
                if req_created:
                    self.stdout.write(f'  Created request: {request.request_number}')
        except Exception as e:
            self.stdout.write(f'  Skipping sample request: {e}')

    def create_dispatch_ready_requests(self):
        """Create ASSIGNED requests for dispatch testing"""
        self.stdout.write('Creating dispatch-ready requests...')

        from apps.assistance.models import AssistanceRequest
        from apps.services.models import UserService

        zones = [
            ('Zona 1 - Centro Historico', Decimal('14.6407'), Decimal('-90.5133')),
            ('Zona 10 - Zona Viva', Decimal('14.6349'), Decimal('-90.5069')),
            ('Zona 14 - Vista Hermosa', Decimal('14.6000'), Decimal('-90.5000')),
            ('Mixco - San Cristobal', Decimal('14.6333'), Decimal('-90.6064')),
        ]

        titles = [
            'Vehiculo no enciende - Necesito grua',
            'Llanta ponchada en carretera',
            'Bateria descargada',
            'Cerrajeria - Llaves dentro del carro',
        ]

        try:
            subscription = UserService.objects.filter(user=self.test_user).first()

            # Get first assistant's provider for assignment
            if self.mawdy_assistants:
                assistant_provider = self.mawdy_assistants[0]['provider']

                for i, (zone_name, lat, lng) in enumerate(zones):
                    request, created = AssistanceRequest.objects.get_or_create(
                        user=self.test_user,
                        title=titles[i],
                        status='ASSIGNED',
                        defaults={
                            'user_service': subscription,
                            'service_category': self.vehicular_category,
                            'description': f'Solicitud de prueba para dispatch testing - {zone_name}',
                            'location_latitude': lat,
                            'location_longitude': lng,
                            'location_address': zone_name,
                            'location_city': 'Guatemala City',
                            'priority': 'HIGH' if i == 0 else 'MEDIUM',
                            'provider': assistant_provider,
                        }
                    )
                    if created:
                        self.stdout.write(f'  Created dispatch request: {request.request_number} -> {zone_name}')

        except Exception as e:
            self.stdout.write(f'  Dispatch requests skipped: {e}')

    def create_analytics_data(self):
        """Create analytics data for admin dashboards"""
        self.stdout.write('Creating analytics data...')

        from apps.assistance.models import AssistanceRequest
        from apps.services.models import ServicePlan, UserService

        now = timezone.now()

        # Create more users for realistic analytics
        extra_users = []
        for i in range(20):
            user, created = User.objects.get_or_create(
                email=f'user{i+1}@test.gt',
                defaults={
                    'first_name': f'Usuario{i+1}',
                    'last_name': 'Test',
                    'phone_number': f'+5025{i:07d}',
                    'role': 'USER',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('TestPass123!')
                user.save()
            extra_users.append(user)

        # Create subscriptions for these users
        try:
            plan = ServicePlan.objects.filter(category=self.vehicular_category).first()
            if plan:
                for i, user in enumerate(extra_users[:15]):  # 15 active subscriptions
                    start_date = date.today() - timedelta(days=random.randint(1, 180))
                    UserService.objects.get_or_create(
                        user=user,
                        plan=plan,
                        defaults={
                            'status': 'ACTIVE' if i < 12 else 'EXPIRED',
                            'start_date': start_date,
                            'auto_renew': random.choice([True, False]),
                        }
                    )
        except Exception as e:
            self.stdout.write(f'  Subscription analytics skipped: {e}')

        # Create historical assistance requests for analytics
        try:
            statuses = ['COMPLETED', 'COMPLETED', 'COMPLETED', 'CANCELLED', 'PENDING']
            priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
            zones = [
                ('Zona 1, Ciudad de Guatemala', Decimal('14.6407'), Decimal('-90.5133')),
                ('Zona 4, Ciudad de Guatemala', Decimal('14.6250'), Decimal('-90.5180')),
                ('Zona 9, Ciudad de Guatemala', Decimal('14.6100'), Decimal('-90.5100')),
                ('Zona 10, Ciudad de Guatemala', Decimal('14.6349'), Decimal('-90.5069')),
                ('Zona 13, Ciudad de Guatemala', Decimal('14.6200'), Decimal('-90.5300')),
                ('Zona 14, Ciudad de Guatemala', Decimal('14.6000'), Decimal('-90.5000')),
                ('Mixco, Guatemala', Decimal('14.6333'), Decimal('-90.6064')),
                ('Villa Nueva, Guatemala', Decimal('14.5258'), Decimal('-90.5900')),
            ]

            subscription = UserService.objects.filter(user=self.test_user).first()
            if subscription:
                for i in range(50):  # Create 50 historical requests
                    user = random.choice(extra_users + [self.test_user])
                    zone = random.choice(zones)
                    created_at = now - timedelta(days=random.randint(1, 90))
                    status = random.choice(statuses)

                    request, created = AssistanceRequest.objects.get_or_create(
                        user=user,
                        title=f'Solicitud historica #{i+1}',
                        created_at=created_at,
                        defaults={
                            'user_service': subscription,
                            'service_category': self.vehicular_category,
                            'description': f'Solicitud de prueba para analytics #{i+1}',
                            'location_latitude': zone[1],
                            'location_longitude': zone[2],
                            'location_address': zone[0],
                            'priority': random.choice(priorities),
                            'status': status,
                        }
                    )
                    if created and status == 'COMPLETED':
                        request.actual_arrival_time = created_at + timedelta(minutes=random.randint(10, 45))
                        request.completed_at = created_at + timedelta(minutes=random.randint(45, 120))
                        request.save()

                self.stdout.write(f'  Created historical requests for analytics')

        except Exception as e:
            self.stdout.write(f'  Request analytics skipped: {e}')

        # Create gamification points for leaderboard
        try:
            from apps.gamification.models import UserPoints
            levels = ['NOVATO', 'APRENDIZ', 'CONOCEDOR', 'EXPERTO', 'MAESTRO']
            for user in extra_users[:10]:
                points = random.randint(50, 500)
                level_idx = min(points // 100, len(levels) - 1)
                UserPoints.objects.get_or_create(
                    user=user,
                    defaults={
                        'puntos_totales': points,
                        'nivel': levels[level_idx],
                        'racha_dias': random.randint(0, 14),
                    }
                )
            self.stdout.write(f'  Created gamification data for leaderboard')
        except Exception as e:
            self.stdout.write(f'  Gamification analytics skipped: {e}')

        self.stdout.write(self.style.SUCCESS('  Analytics data created!'))

    def print_credentials(self):
        """Print test credentials"""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('TEST CREDENTIALS'))
        self.stdout.write('=' * 70)

        self.stdout.write(self.style.WARNING('\n--- SEGURIFAI ADMIN (Platform Owner - Full Analytics) ---'))
        self.stdout.write('  Email: admin@segurifai.gt')
        self.stdout.write('  Password: AdminPass123!')
        self.stdout.write('  Access: Full platform analytics, all users, all providers')

        self.stdout.write(self.style.WARNING('\n--- MAWDY ADMIN (Provider Admin) ---'))
        self.stdout.write('  Email: admin@mawdy.gt')
        self.stdout.write('  Password: MawdyAdmin123!')
        self.stdout.write('  Access: MAWDY provider analytics, assistants management')

        self.stdout.write(self.style.WARNING('\n--- MAWDY PROVIDER (Company Account) ---'))
        self.stdout.write('  Email: soporte@mawdy.gt')
        self.stdout.write('  Password: MawdyPass123!')
        self.stdout.write('  Access: Provider operations, service requests')

        self.stdout.write(self.style.WARNING('\n--- MAWDY ASSISTANTS (Field Technicians) ---'))
        self.stdout.write('  grua1@mawdy.gt / Asistente123! (Carlos - Grua)')
        self.stdout.write('  grua2@mawdy.gt / Asistente123! (Roberto - Grua)')
        self.stdout.write('  mecanico1@mawdy.gt / Asistente123! (Luis - Mecanica)')
        self.stdout.write('  ambulancia1@mawdy.gt / Asistente123! (Miguel - Ambulancia)')
        self.stdout.write('  Access: Tracking updates, mark arrived/completed')

        self.stdout.write(self.style.WARNING('\n--- TEST USER (PAQ Token Testing - Phone: 3008 2653) ---'))
        self.stdout.write('  Email: test@segurifai.gt')
        self.stdout.write('  Password: TestPass123!')
        self.stdout.write('  Phone: +502 3008 2653')
        self.stdout.write('  PAQ Wallet ID: PAQ-3008-2653')
        self.stdout.write('  ** Use this phone number to test PAQ token flow **')

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('POSTMAN ENVIRONMENT VARIABLES'))
        self.stdout.write('=' * 70)
        self.stdout.write('  test_user_email: test@segurifai.gt')
        self.stdout.write('  test_admin_email: admin@segurifai.gt')
        self.stdout.write('  mawdy_admin_email: admin@mawdy.gt')
        self.stdout.write('  test_provider_email: soporte@mawdy.gt')
        self.stdout.write('  test_assistant_email: grua1@mawdy.gt')
        self.stdout.write('=' * 70 + '\n')
