"""
Management command to seed subscription plans
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import ServiceCategory, ServicePlan


class Command(BaseCommand):
    help = 'Seed subscription plans for testing'

    def handle(self, *args, **options):
        self.stdout.write('Seeding subscription plans...')

        with transaction.atomic():
            # Create service categories if they don't exist
            roadside_cat, _ = ServiceCategory.objects.get_or_create(
                category_type='ROADSIDE',
                defaults={
                    'name': 'Asistencia Vial',
                    'description': 'Servicio de asistencia en carretera 24/7',
                    'icon': 'truck',
                    'is_active': True
                }
            )

            health_cat, _ = ServiceCategory.objects.get_or_create(
                category_type='HEALTH',
                defaults={
                    'name': 'Asistencia Medica',
                    'description': 'Asistencia medica de emergencia',
                    'icon': 'heart',
                    'is_active': True
                }
            )

            # Create or get insurance category for base accident insurance
            insurance_cat, _ = ServiceCategory.objects.get_or_create(
                category_type='INSURANCE',
                defaults={
                    'name': 'Seguro de Accidentes',
                    'description': 'Seguro de accidentes personales MAPFRE',
                    'icon': 'shield',
                    'is_active': True
                }
            )

            # Deactivate any card insurance category (not a MAWDY service)
            ServiceCategory.objects.filter(category_type='CARD_INSURANCE').update(is_active=False)

            self.stdout.write('  Created service categories')

            # Deactivate old optional plans - keeping only standard pricing
            ServicePlan.objects.filter(name__icontains='Opcional').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='Inclusion').update(is_active=False)

            # Update or create plans (MAPFRE standard pricing)
            plans_data = [
                # ROADSIDE ASSISTANCE PLAN (MAPFRE AP Muerte Accidental + Asistencia Vial)
                {
                    'category': roadside_cat,
                    'name': 'Asistencia Vial MAPFRE',
                    'description': 'Plan de asistencia vial con seguro de muerte accidental y servicios MAWDY',
                    'price_monthly': 36.88,
                    'price_yearly': 442.56,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000.00',
                        'Grua del Vehiculo (3/ano, limite $150 USD)',
                        'Abasto de Combustible (3/ano, limite combinado $150)',
                        'Cambio de Neumaticos (3/ano, limite combinado $150)',
                        'Paso de Corriente (3/ano, limite combinado $150)',
                        'Emergencia de Cerrajeria (3/ano, limite combinado $150)',
                        'Servicio de Ambulancia por Accidente (1/ano, $100 USD)',
                        'Servicio de Conductor Profesional (1/ano, $60 USD)',
                        'Taxi al Aeropuerto (1/ano, $60 USD)',
                        'Asistencia Legal Telefonica (1/ano, $200 USD)',
                        'Apoyo Economico Sala Emergencia (1/ano, $1,000 USD)',
                        'Rayos X (1/ano, $300 USD)',
                        'Descuentos en Red de Proveedores (hasta 20%)',
                        'Asistente Telefonico Cotizacion Repuestos',
                        'Asistente Telefonico Referencias Medicas'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 2920.00,  # Sum of all USD limits
                    'is_active': True,
                    'is_featured': True
                },

                # HEALTH ASSISTANCE PLAN (MAPFRE AP Muerte Accidental + Asistencia Medica)
                {
                    'category': health_cat,
                    'name': 'Asistencia Medica MAPFRE',
                    'description': 'Plan de asistencia medica con seguro de muerte accidental y servicios MAWDY',
                    'price_monthly': 34.26,
                    'price_yearly': 411.12,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000.00',
                        'Orientacion Medica Telefonica (Ilimitado)',
                        'Conexion con Especialistas de la Red (Ilimitado)',
                        'Consulta Presencial Medico/Ginecologo/Pediatra (3/ano, $150 USD)',
                        'Coordinacion de Medicamentos a Domicilio (Ilimitado)',
                        'Cuidados Post Operatorios Enfermera (1/ano, $100 USD)',
                        'Envio Articulos Aseo por Hospitalizacion (1/ano, $100 USD)',
                        'Examenes Lab: Heces, Orina, Hematologia (2/ano, $100 USD)',
                        'Examenes: Papanicolau/Mamografia/Antigeno (2/ano, $100 USD)',
                        'Nutricionista Video Consulta (4/ano, $150 USD)',
                        'Psicologia Video Consulta (4/ano, $150 USD)',
                        'Servicio de Mensajeria por Hospitalizacion (2/ano, $60 USD)',
                        'Taxi Familiar por Hospitalizacion (2/ano, $100 USD)',
                        'Traslado en Ambulancia por Accidente (2/ano, $150 USD)',
                        'Taxi al Domicilio tras Alta (1/ano, $100 USD)'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1360.00,  # Sum of all USD limits
                    'is_active': True,
                    'is_featured': True
                },

                # BASE PERSONAL ACCIDENT INSURANCE (MAPFRE Seguro de Accidentes Personales)
                {
                    'category': insurance_cat,
                    'name': 'Seguro de Accidentes Personales',
                    'description': 'Seguro basico de accidentes personales MAPFRE con cobertura de muerte accidental',
                    'price_monthly': 4.12,
                    'price_yearly': 49.44,
                    'duration_days': 30,
                    'features': [
                        'Muerte Accidental Q3,000.00',
                        'Cobertura por explosiones y descargas electricas',
                        'Cobertura por quemaduras (fuego, vapor, acidos)',
                        'Cobertura por asfixia accidental',
                        'Cobertura por infecciones de accidentes cubiertos',
                        'Cobertura por mordeduras de animales',
                        'Cobertura por fenomenos naturales',
                        'Cobertura por intoxicacion alimentaria',
                        'Cobertura en legitima defensa',
                        'Cobertura en accidentes aereos comerciales',
                        'Edad de ingreso: 18-61 anos',
                        'Edad de terminacion: 70 anos'
                    ],
                    'max_requests_per_month': 1,
                    'coverage_amount': 3000.00,  # Q3,000 death benefit
                    'is_active': True,
                    'is_featured': False
                }
            ]

            # Create or update plans
            for plan_data in plans_data:
                plan, created = ServicePlan.objects.update_or_create(
                    category=plan_data['category'],
                    name=plan_data['name'],
                    defaults={k: v for k, v in plan_data.items() if k not in ['category', 'name']}
                )
                action = 'Created' if created else 'Updated'
                self.stdout.write(f'  {action} plan: {plan.name} - Q{plan.price_monthly}/mes')

        total_plans = ServicePlan.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created {total_plans} subscription plans!'
        ))
