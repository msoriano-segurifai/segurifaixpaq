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

            # Deactivate ALL old plans - only keep new Protege tu... plans
            ServicePlan.objects.filter(name__icontains='Opcional').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='Inclusion').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='Plan Asistencia').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='Plan Seguro').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='Drive').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='Health').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='Combo').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='SegurifAI Asistencia').update(is_active=False)
            ServicePlan.objects.filter(name__icontains='SegurifAI Seguro').update(is_active=False)
            self.stdout.write('  Deactivated old plans')

            # Terms and Conditions per PDF document
            TARJETA_TERMS = """PROTEGE TU TARJETA - TÉRMINOS Y CONDICIONES

A) TARJETAS PERDIDAS O ROBADAS:
La Aseguradora pagará al Tarjeta habiente por débitos realizados durante el Período de cobertura que Resulten directamente del uso de alguna Tarjeta Perdida o Robada, por alguna persona no autorizada para:
1. La obtención de Dinero o crédito ya sea con la autorización recibida del Emisor o de algún Cajero Automático.
2. La compra o arrendamiento de bienes o servicios, incluyendo compras por Internet.

Es el entendido de que los débitos fueron hechos dentro de las 48 horas Inmediatamente Anteriores a la Notificación de dicha pérdida o Robo de la Tarjeta.

B) CLONACIÓN:
• Falsificación y/o Adulteración de la tarjeta
• Falsificación y/o Adulteración de Banda Magnética

C) COBERTURA DIGITAL:
Cobertura contra riesgos cibernéticos y compras fraudulentas por internet:
1. Ingeniería Social
2. Phishing
3. Robo de identidad
4. Suplantación de identidad (Spoofing)
5. Vishing

EXCLUSIONES:
1. Fraudes que no se hayan realizado vía online (excepto Robo de Tarjeta física).
2. Daños consecuenciales como moral, pérdida de beneficios, lucro cesante.
3. Cuando el Asegurado, familiar, amigo o empleado de la Entidad Financiera sea autor o cómplice.
4. Cuando la tarjeta permanezca bajo custodia de la Entidad Financiera.
5. Fraudes originados después de 5 días hábiles de entrega del estado de cuenta.
6. Incumplimiento en pago de obligaciones del Asegurado.
7. Fraudes en situación de guerra, terrorismo, fenómenos naturales catastróficos.
8. Pérdidas cubiertas por otro seguro.
9. Daños en sistemas de la Entidad Financiera.
10. Ataques de Hackers a la plataforma de la Entidad Financiera.
11. Usurpación de identidad para adquirir nuevos productos.
12. Compras fraudulentas por negligencia del Asegurado (compartir credenciales, etc.)."""

            SALUD_TERMS = """PROTEGE TU SALUD - TÉRMINOS Y CONDICIONES

MUERTE ACCIDENTAL: Q3,000.00
Cobertura por fallecimiento accidental del titular.

SERVICIOS INCLUIDOS (Opción 2 - 30% Comisión):
• Orientación Médica Telefónica: Ilimitado
• Conexión con Especialistas de la Red: Ilimitado
• Consulta Presencial (Médico General, Ginecólogo o Pediatra) - Grupo Familiar: 3 al año, límite $150.00
• Coordinación de Medicamentos al Domicilio del Titular: Ilimitado
• Cuidados Post Operatorios de Enfermería para Titular: 1 al año, límite $100.00
• Envío de Artículos de Aseo Personal por Hospitalización: 1 al año, límite $100.00
• Exámenes de Laboratorio (Heces, Orina y Hematología Completa) - Grupo Familiar: 2 al año, límite $100.00
• Exámenes de Laboratorio (Papanicoláu o Mamografía o Antígeno Prostático) Titular: 2 al año, límite $100.00
• Nutricionista Video Consulta - Grupo Familiar: 4 al año, límite $150.00
• Psicología por Video Consulta - Núcleo Familiar: 4 al año, límite $150.00
• Servicio de Mensajería por Hospitalización por Emergencia: 2 al año, límite $60.00
• Taxi para un Familiar por Hospitalización del Titular (15 km Ciudad Capital): 2 al año, límite $100.00
• Traslado en Ambulancia por Accidente (Titular): 2 al año, límite $150.00
• Traslado en Taxi al Domicilio tras ser dado de alta (15 km Ciudad Capital): 1 al año, límite $100.00

Asistencias SegurifAI incluidas."""

            RUTA_TERMS = """PROTEGE TU RUTA - TÉRMINOS Y CONDICIONES

MUERTE ACCIDENTAL: Q3,000.00
Cobertura por fallecimiento accidental del titular.

SERVICIOS INCLUIDOS (Opción 2 - 30% Comisión):
• Grúa del Vehículo (Accidente o falla mecánica): 3 al año, límite $150.00
• Abasto de Combustible (1 galón, demostrar que no tiene suministro): 3 al año a elegir, límite $150.00
• Cambio de Neumáticos: Incluido en límite combinado
• Paso de Corriente: Incluido en límite combinado
• Emergencia de Cerrajería: Incluido en límite combinado
• Servicio de Ambulancia (por accidente): 1 al año, límite $100.00
• Servicio de Conductor Profesional (enfermedad o embriaguez, 5 horas anticipación): 1 al año, límite $60.00
• Taxi al Aeropuerto (por viaje del titular al extranjero): 1 al año, límite $60.00
• Asistencia Legal Telefónica: 1 al año, límite $200.00
• Apoyo Económico en Sala de Emergencia para Restablecimiento por Accidente Automovilístico: 1 al año, límite $1,000.00
• Rayos X: 1 al año, límite $300.00 (hasta 20% descuento)
• Descuentos en Red de Proveedores: Hasta 20% descuento
• Asistente Telefónico para Cotización de Repuestos y Referencias Mecánicas: Incluido
• Asistente Telefónico para Referencias Médicas por Motivo de Accidente Automovilístico: Incluido

Asistencias SegurifAI incluidas."""

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
                    'terms_and_conditions': TARJETA_TERMS,
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
                    'terms_and_conditions': SALUD_TERMS,
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
                    'terms_and_conditions': RUTA_TERMS,
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
