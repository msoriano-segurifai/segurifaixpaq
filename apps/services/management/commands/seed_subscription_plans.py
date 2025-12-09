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
                    'description': 'Seguro de accidentes personales SegurifAI',
                    'icon': 'shield',
                    'is_active': True
                }
            )

            # Create or get card insurance category for Protege tu Tarjeta
            card_cat, _ = ServiceCategory.objects.get_or_create(
                category_type='CARD_INSURANCE',
                defaults={
                    'name': 'Protección de Tarjeta',
                    'description': 'Protección contra fraude y robo de tarjetas',
                    'icon': 'credit-card',
                    'is_active': True
                }
            )
            # Ensure card category is active
            ServiceCategory.objects.filter(category_type='CARD_INSURANCE').update(is_active=True)

            self.stdout.write('  Created service categories')

            # Deactivate old optional plans - keeping only standard pricing
            ServicePlan.objects.filter(name__icontains='Opcional').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='Inclusion').update(is_active=False)

            # Update or create plans (SegurifAI pricing - Dec 2025)
            plans_data = [
                # PROTEGE TU TARJETA (PRF - Card Protection) - Q34.99
                {
                    'category': card_cat,
                    'name': 'Protege tu Tarjeta',
                    'description': 'Protección contra fraude, clonación y robo de tarjetas',
                    'price_monthly': 34.99,
                    'price_yearly': 419.88,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000.00',
                        'Tarjetas Perdidas o Robadas (48hrs para notificar)',
                        'Protección contra Clonación de Tarjeta',
                        'Protección contra Falsificación de Banda Magnética',
                        'Cobertura Digital: Ingeniería Social',
                        'Cobertura Digital: Phishing',
                        'Cobertura Digital: Robo de Identidad',
                        'Cobertura Digital: Suplantación (Spoofing)',
                        'Cobertura Digital: Vishing',
                        'Cobertura compras fraudulentas por internet',
                        'Asistencias SegurifAI incluidas'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 3000.00,
                    'is_active': True,
                    'is_featured': False
                },

                # PROTEGE TU SALUD (Asistencia Médica) - Q34.99
                {
                    'category': health_cat,
                    'name': 'Protege tu Salud',
                    'description': 'Asistencia médica completa con seguro de muerte accidental',
                    'price_monthly': 34.99,
                    'price_yearly': 419.88,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000.00',
                        'Orientación Médica Telefónica (Ilimitado)',
                        'Conexión con Especialistas de la Red (Ilimitado)',
                        'Consulta Presencial Médico/Ginecólogo/Pediatra (3/año, $150 USD)',
                        'Coordinación de Medicamentos a Domicilio (Ilimitado)',
                        'Cuidados Post Operatorios Enfermera (1/año, $100 USD)',
                        'Envío Artículos Aseo por Hospitalización (1/año, $100 USD)',
                        'Exámenes Lab: Heces, Orina, Hematología (2/año, $100 USD)',
                        'Exámenes: Papanicoláu/Mamografía/Antígeno (2/año, $100 USD)',
                        'Nutricionista Video Consulta Familiar (4/año, $150 USD)',
                        'Psicología Video Consulta Familiar (4/año, $150 USD)',
                        'Servicio de Mensajería por Hospitalización (2/año, $60 USD)',
                        'Taxi Familiar por Hospitalización (2/año, $100 USD)',
                        'Traslado en Ambulancia por Accidente (2/año, $150 USD)',
                        'Taxi al Domicilio tras Alta (1/año, $100 USD)',
                        'Asistencias SegurifAI incluidas'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 1360.00,
                    'is_active': True,
                    'is_featured': True
                },

                # PROTEGE TU RUTA (Asistencia Vial) - Q39.99
                {
                    'category': roadside_cat,
                    'name': 'Protege tu Ruta',
                    'description': 'Asistencia vial completa con seguro de muerte accidental',
                    'price_monthly': 39.99,
                    'price_yearly': 479.88,
                    'duration_days': 30,
                    'features': [
                        'Seguro Muerte Accidental Q3,000.00',
                        'Grúa del Vehículo (3/año, $150 USD)',
                        'Abasto de Combustible 1 galón (3/año, $150 USD combinado)',
                        'Cambio de Neumáticos (3/año, $150 USD combinado)',
                        'Paso de Corriente (3/año, $150 USD combinado)',
                        'Emergencia de Cerrajería (3/año, $150 USD combinado)',
                        'Servicio de Ambulancia por Accidente (1/año, $100 USD)',
                        'Servicio de Conductor Profesional (1/año, $60 USD)',
                        'Taxi al Aeropuerto (1/año, $60 USD)',
                        'Asistencia Legal Telefónica (1/año, $200 USD)',
                        'Apoyo Económico Sala Emergencia (1/año, $1,000 USD)',
                        'Rayos X (1/año, $300 USD, hasta 20% descuento)',
                        'Descuentos en Red de Proveedores (hasta 20%)',
                        'Asistente Telefónico Cotización Repuestos',
                        'Asistente Telefónico Referencias Médicas por Accidente',
                        'Asistencias SegurifAI incluidas'
                    ],
                    'max_requests_per_month': 3,
                    'coverage_amount': 2920.00,
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
