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

            # Deactivate any card insurance category (not a MAWDY service)
            ServiceCategory.objects.filter(category_type='CARD_INSURANCE').update(is_active=False)

            self.stdout.write('  Created service categories')

            # Update or create plans (don't delete to preserve existing subscriptions)
            plans_data = [
                # ROADSIDE ASSISTANCE PLANS (MAWDY Plan Drive-1)
                {
                    'category': roadside_cat,
                    'name': 'Plan Drive-1 (Inclusion)',
                    'description': 'Asistencia vial completa incluida en tu plan MAWDY',
                    'price_monthly': 25.20,
                    'price_yearly': 302.40,
                    'duration_days': 30,
                    'features': [
                        'Servicio de Grua (3 veces al ano, limite Q1,200)',
                        'Entrega de Combustible',
                        'Cambio de Llanta',
                        'Arranque de Bateria',
                        'Servicio de Cerrajeria',
                        'Servicio de Ambulancia',
                        'Servicio de Chofer Profesional',
                        'Taxi al Aeropuerto',
                        'Asistencia Legal por Accidentes',
                        'Atencion en Sala de Emergencia (hasta Q8,000)',
                        'Radiografias (hasta Q2,400)',
                        'Descuentos en Red de Proveedores'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1200.00,
                    'is_active': True,
                    'is_featured': False
                },
                {
                    'category': roadside_cat,
                    'name': 'Plan Drive-1 (Opcional)',
                    'description': 'Asistencia vial premium con cobertura extendida',
                    'price_monthly': 30.00,
                    'price_yearly': 360.00,
                    'duration_days': 30,
                    'features': [
                        'Servicio de Grua (3 veces al ano, limite Q1,200)',
                        'Entrega de Combustible',
                        'Cambio de Llanta',
                        'Arranque de Bateria',
                        'Servicio de Cerrajeria',
                        'Servicio de Ambulancia',
                        'Servicio de Chofer Profesional',
                        'Taxi al Aeropuerto',
                        'Asistencia Legal por Accidentes',
                        'Atencion en Sala de Emergencia (hasta Q8,000)',
                        'Radiografias (hasta Q2,400)',
                        'Descuentos en Red de Proveedores'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1200.00,
                    'is_active': True,
                    'is_featured': True
                },

                # HEALTH ASSISTANCE PLANS (MAWDY Plan Health)
                {
                    'category': health_cat,
                    'name': 'Plan Health (Inclusion)',
                    'description': 'Asistencia medica completa incluida en tu plan MAWDY',
                    'price_monthly': 23.20,
                    'price_yearly': 278.40,
                    'duration_days': 30,
                    'features': [
                        'Orientacion Medica Telefonica 24/7',
                        'Red de Medicos Especialistas',
                        'Consultas Presenciales (3 al ano, hasta Q1,200)',
                        'Entrega de Medicamentos a Domicilio',
                        'Enfermeria Post-Operatoria',
                        'Articulos de Cuidado Personal',
                        'Examenes de Laboratorio',
                        'Consultas con Nutricionista',
                        'Consultas con Psicologo',
                        'Servicio de Mensajeria',
                        'Servicio de Taxi para Hospitalizacion',
                        'Traslado en Ambulancia'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1200.00,
                    'is_active': True,
                    'is_featured': False
                },
                {
                    'category': health_cat,
                    'name': 'Plan Health (Opcional)',
                    'description': 'Asistencia medica premium con cobertura extendida',
                    'price_monthly': 27.60,
                    'price_yearly': 331.20,
                    'duration_days': 30,
                    'features': [
                        'Orientacion Medica Telefonica 24/7',
                        'Red de Medicos Especialistas',
                        'Consultas Presenciales (3 al ano, hasta Q1,200)',
                        'Entrega de Medicamentos a Domicilio',
                        'Enfermeria Post-Operatoria',
                        'Articulos de Cuidado Personal',
                        'Examenes de Laboratorio',
                        'Consultas con Nutricionista',
                        'Consultas con Psicologo',
                        'Servicio de Mensajeria',
                        'Servicio de Taxi para Hospitalizacion',
                        'Traslado en Ambulancia'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1200.00,
                    'is_active': True,
                    'is_featured': True
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
