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
                # ROADSIDE ASSISTANCE PLANS (MAPFRE Plan Asistencia Vial)
                {
                    'category': roadside_cat,
                    'name': 'Asistencia Vial (Inclusion)',
                    'description': 'Plan de asistencia vial MAPFRE con precio preferencial para usuarios PAQ',
                    'price_monthly': 36.88,
                    'price_yearly': 442.56,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000',
                        'Servicio de Grua (3/ano, limite $150 USD)',
                        'Abasto de Combustible (3/ano, limite combinado $150)',
                        'Cambio de Neumaticos (3/ano, limite combinado $150)',
                        'Paso de Corriente (3/ano, limite combinado $150)',
                        'Cerrajeria Vehicular (3/ano, limite combinado $150)',
                        'Ambulancia por Accidente (1/ano, $100 USD)',
                        'Conductor Profesional (1/ano, $60 USD)',
                        'Taxi al Aeropuerto (1/ano, $60 USD)',
                        'Asistencia Legal Telefonica (1/ano, $200 USD)',
                        'Apoyo Emergencia Hospital (1/ano, $1,000 USD)',
                        'Rayos X (1/ano, $300 USD)',
                        'Descuentos en Red de Proveedores (hasta 20%)',
                        'Asistentes Telefonicos Incluidos'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1163.00,
                    'is_active': True,
                    'is_featured': False
                },
                {
                    'category': roadside_cat,
                    'name': 'Asistencia Vial (Opcional)',
                    'description': 'Plan de asistencia vial MAPFRE independiente sin requisitos',
                    'price_monthly': 38.93,
                    'price_yearly': 467.16,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000',
                        'Servicio de Grua (3/ano, limite $150 USD)',
                        'Abasto de Combustible (3/ano, limite combinado $150)',
                        'Cambio de Neumaticos (3/ano, limite combinado $150)',
                        'Paso de Corriente (3/ano, limite combinado $150)',
                        'Cerrajeria Vehicular (3/ano, limite combinado $150)',
                        'Ambulancia por Accidente (1/ano, $100 USD)',
                        'Conductor Profesional (1/ano, $60 USD)',
                        'Taxi al Aeropuerto (1/ano, $60 USD)',
                        'Asistencia Legal Telefonica (1/ano, $200 USD)',
                        'Apoyo Emergencia Hospital (1/ano, $1,000 USD)',
                        'Rayos X (1/ano, $300 USD)',
                        'Descuentos en Red de Proveedores (hasta 20%)',
                        'Asistentes Telefonicos Incluidos'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1163.00,
                    'is_active': True,
                    'is_featured': True
                },

                # HEALTH ASSISTANCE PLANS (MAPFRE Plan Asistencia Medica)
                {
                    'category': health_cat,
                    'name': 'Asistencia Medica (Inclusion)',
                    'description': 'Plan de asistencia medica MAPFRE con precio preferencial para usuarios PAQ',
                    'price_monthly': 34.26,
                    'price_yearly': 411.12,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000',
                        'Orientacion Medica Telefonica 24/7 (Ilimitado)',
                        'Conexion con Especialistas (Ilimitado)',
                        'Coordinacion Medicamentos a Domicilio (Ilimitado)',
                        'Consulta Presencial (3/ano, $150 USD)',
                        'Cuidados Post-Op Enfermera (1/ano, $100 USD)',
                        'Articulos de Aseo Hospitalizacion (1/ano, $100 USD)',
                        'Examenes Lab Basicos (2/ano, $100 USD)',
                        'Examenes Especializados (2/ano, $100 USD)',
                        'Nutricionista Video (4/ano, $150 USD)',
                        'Psicologia Video (4/ano, $150 USD)',
                        'Mensajeria Hospitalizacion (2/ano, $60 USD)',
                        'Taxi Familiar Hospitalizacion (2/ano, $100 USD)',
                        'Ambulancia Accidente (2/ano, $150 USD)',
                        'Taxi Post-Alta (1/ano, $100 USD)'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1163.00,
                    'is_active': True,
                    'is_featured': False
                },
                {
                    'category': health_cat,
                    'name': 'Asistencia Medica (Opcional)',
                    'description': 'Plan de asistencia medica MAPFRE independiente sin requisitos',
                    'price_monthly': 36.31,
                    'price_yearly': 435.72,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000',
                        'Orientacion Medica Telefonica 24/7 (Ilimitado)',
                        'Conexion con Especialistas (Ilimitado)',
                        'Coordinacion Medicamentos a Domicilio (Ilimitado)',
                        'Consulta Presencial (3/ano, $150 USD)',
                        'Cuidados Post-Op Enfermera (1/ano, $100 USD)',
                        'Articulos de Aseo Hospitalizacion (1/ano, $100 USD)',
                        'Examenes Lab Basicos (2/ano, $100 USD)',
                        'Examenes Especializados (2/ano, $100 USD)',
                        'Nutricionista Video (4/ano, $150 USD)',
                        'Psicologia Video (4/ano, $150 USD)',
                        'Mensajeria Hospitalizacion (2/ano, $60 USD)',
                        'Taxi Familiar Hospitalizacion (2/ano, $100 USD)',
                        'Ambulancia Accidente (2/ano, $150 USD)',
                        'Taxi Post-Alta (1/ano, $100 USD)'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1163.00,
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
