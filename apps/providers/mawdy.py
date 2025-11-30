"""
MAWDY Integration for SegurifAI x PAQ

MAWDY is the assistance provider for PAQ Wallet offering:
- Plan Drive (Vial) - Roadside assistance
- Plan Health (Salud) - Health assistance

Contact: 8a. Av. 3-80 Zona 14, Edificio La Rambla II, 5to. Nivel, Guatemala
Phone: (502) 2285-5070
"""
from decimal import Decimal
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# MAWDY SERVICE DEFINITIONS (from PDF quotation)
# =============================================================================

class PlanType(str, Enum):
    DRIVE = 'DRIVE'  # Plan Vial
    HEALTH = 'HEALTH'  # Plan Salud


# Plan Drive (Vial) Services
PLAN_DRIVE_SERVICES = {
    'GRUA': {
        'name': 'Grúa del Vehículo',
        'description': 'Servicio de grúa por accidente o falla mecánica',
        'events_per_year': 3,
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': True,
    },
    'COMBUSTIBLE': {
        'name': 'Abasto de Combustible',
        'description': '1 galón de combustible - requiere imagen demostrando tanque vacío',
        'events_per_year': 3,  # Combined with tire/jump start
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': True,
    },
    'NEUMATICOS': {
        'name': 'Cambio de Neumáticos',
        'description': 'Servicio de cambio de neumático ponchado',
        'events_per_year': 3,
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': False,
    },
    'CORRIENTE': {
        'name': 'Paso de Corriente',
        'description': 'Servicio de paso de corriente para batería descargada',
        'events_per_year': 3,
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': False,
    },
    'CERRAJERIA': {
        'name': 'Emergencia de Cerrajería',
        'description': 'Servicio de cerrajería automotriz',
        'events_per_year': 3,
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': False,
    },
    'AMBULANCIA_ACCIDENTE': {
        'name': 'Servicio de Ambulancia',
        'description': 'Ambulancia por accidente automovilístico',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('100.00'),
        'requires_evidence': True,
    },
    'CONDUCTOR_PROFESIONAL': {
        'name': 'Conductor Profesional',
        'description': 'Por enfermedad o embriaguez - 5 horas anticipación, documentos en orden',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('60.00'),
        'requires_evidence': True,
    },
    'TAXI_AEROPUERTO': {
        'name': 'Taxi al Aeropuerto',
        'description': 'Por viaje del titular al extranjero',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('60.00'),
        'requires_evidence': True,
    },
    'ASISTENCIA_LEGAL': {
        'name': 'Asistencia Legal Telefónica',
        'description': 'Asesoría legal telefónica por accidente',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('200.00'),
        'requires_evidence': False,
    },
    'APOYO_EMERGENCIA': {
        'name': 'Apoyo Económico Emergencia',
        'description': 'Apoyo en sala de emergencia por accidente - pago directo al hospital',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('1000.00'),
        'requires_evidence': True,
    },
    'RAYOS_X': {
        'name': 'Rayos X',
        'description': 'Estudio de rayos X por accidente',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('300.00'),
        'requires_evidence': True,
    },
    'DESCUENTOS_RED': {
        'name': 'Descuentos en Red de Proveedores',
        'description': 'Hasta 20% de descuento en red de proveedores',
        'events_per_year': None,  # Unlimited
        'economic_limit_usd': None,
        'requires_evidence': False,
    },
    'ASISTENTE_REPUESTOS': {
        'name': 'Asistente Telefónico Repuestos',
        'description': 'Cotización de repuestos y referencias mecánicas',
        'events_per_year': None,
        'economic_limit_usd': None,
        'requires_evidence': False,
    },
    'ASISTENTE_MEDICO': {
        'name': 'Asistente Telefónico Médico',
        'description': 'Referencias médicas por accidente automovilístico',
        'events_per_year': None,
        'economic_limit_usd': None,
        'requires_evidence': False,
    },
}

# Plan Health (Salud) Services
PLAN_HEALTH_SERVICES = {
    'ORIENTACION_MEDICA': {
        'name': 'Orientación Médica Telefónica',
        'description': 'Orientación médica por teléfono 24/7',
        'events_per_year': None,
        'economic_limit_usd': None,
        'requires_evidence': False,
        'family_coverage': True,
    },
    'CONEXION_ESPECIALISTAS': {
        'name': 'Conexión con Especialistas',
        'description': 'Conexión con especialistas de la red médica',
        'events_per_year': None,
        'economic_limit_usd': None,
        'requires_evidence': False,
        'family_coverage': True,
    },
    'CONSULTA_PRESENCIAL': {
        'name': 'Consulta Presencial',
        'description': 'Médico general, ginecólogo o pediatra - grupo familiar',
        'events_per_year': 3,
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': False,
        'family_coverage': True,
    },
    'MEDICAMENTOS_DOMICILIO': {
        'name': 'Coordinación Medicamentos',
        'description': 'Coordinación de entrega de medicamentos al domicilio',
        'events_per_year': None,
        'economic_limit_usd': None,
        'requires_evidence': False,
        'family_coverage': False,
    },
    'CUIDADOS_POST_OP': {
        'name': 'Cuidados Post Operatorios',
        'description': 'Servicio de enfermera post operatorio',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('100.00'),
        'requires_evidence': True,
        'family_coverage': False,
    },
    'ARTICULOS_HOSPITALIZACION': {
        'name': 'Artículos de Aseo Personal',
        'description': 'Envío de artículos por hospitalización',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('100.00'),
        'requires_evidence': True,
        'family_coverage': False,
    },
    'LABORATORIO_BASICO': {
        'name': 'Exámenes de Laboratorio Básicos',
        'description': 'Heces, orina y hematología completa - grupo familiar',
        'events_per_year': 2,
        'economic_limit_usd': Decimal('100.00'),
        'requires_evidence': False,
        'family_coverage': True,
    },
    'LABORATORIO_ESPECIALIZADO': {
        'name': 'Exámenes Especializados',
        'description': 'Papanicolau, mamografía o antígeno prostático - titular',
        'events_per_year': 2,
        'economic_limit_usd': Decimal('100.00'),
        'requires_evidence': False,
        'family_coverage': False,
    },
    'NUTRICIONISTA': {
        'name': 'Nutricionista Video Consulta',
        'description': 'Consulta con nutricionista por video - grupo familiar',
        'events_per_year': 4,
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': False,
        'family_coverage': True,
    },
    'PSICOLOGIA': {
        'name': 'Psicología Video Consulta',
        'description': 'Consulta psicológica por video - núcleo familiar',
        'events_per_year': 4,
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': False,
        'family_coverage': True,
    },
    'MENSAJERIA_HOSPITALIZACION': {
        'name': 'Servicio de Mensajería',
        'description': 'Mensajería por hospitalización de emergencia',
        'events_per_year': 2,
        'economic_limit_usd': Decimal('60.00'),
        'requires_evidence': True,
        'family_coverage': False,
    },
    'TAXI_FAMILIAR': {
        'name': 'Taxi para Familiar',
        'description': 'Por hospitalización del titular - 15km perímetro capital',
        'events_per_year': 2,
        'economic_limit_usd': Decimal('100.00'),
        'requires_evidence': True,
        'family_coverage': False,
    },
    'AMBULANCIA_ACCIDENTE': {
        'name': 'Traslado en Ambulancia',
        'description': 'Por accidente del titular',
        'events_per_year': 2,
        'economic_limit_usd': Decimal('150.00'),
        'requires_evidence': True,
        'family_coverage': False,
    },
    'TAXI_ALTA': {
        'name': 'Taxi tras Alta Hospitalización',
        'description': 'Al domicilio tras alta - 15km perímetro capital',
        'events_per_year': 1,
        'economic_limit_usd': Decimal('100.00'),
        'requires_evidence': True,
        'family_coverage': False,
    },
}

# Exchange Rate (November 2025)
USD_TO_GTQ = Decimal('7.75')

# Pricing (USD - Net Commercial Price, no taxes)
PLAN_PRICING_USD = {
    'DRIVE': {
        'inclusion': {'monthly': Decimal('3.15'), 'annual': Decimal('37.80')},
        'optional': {'monthly': Decimal('3.75'), 'annual': Decimal('45.00')},
    },
    'HEALTH': {
        'inclusion': {'monthly': Decimal('2.90'), 'annual': Decimal('34.80')},
        'optional': {'monthly': Decimal('3.45'), 'annual': Decimal('41.40')},
    },
}

# Pricing (GTQ - Guatemalan Quetzales)
PLAN_PRICING_GTQ = {
    'DRIVE': {
        'inclusion': {'monthly': Decimal('24.41'), 'annual': Decimal('292.95')},  # 3.15 * 7.75
        'optional': {'monthly': Decimal('29.06'), 'annual': Decimal('348.75')},   # 3.75 * 7.75
    },
    'HEALTH': {
        'inclusion': {'monthly': Decimal('22.48'), 'annual': Decimal('269.70')},  # 2.90 * 7.75
        'optional': {'monthly': Decimal('26.74'), 'annual': Decimal('320.85')},   # 3.45 * 7.75
    },
}

# Combined pricing (backwards compatibility)
PLAN_PRICING = PLAN_PRICING_USD

# Business Rules
BUSINESS_RULES = {
    'vehicle_max_age_years': 20,
    'vehicle_max_weight_tons': 3.5,
    'vehicle_use': 'particular',  # Personal use only
    'geographic_area': 'Guatemala',
    'quote_validity_days': 45,
    'min_subscribers_drive': 500,  # Minimum for optional plan
    'min_subscribers_health': 350,
    'cost_review_frequency': 'semestral',
    'max_cost_ratio': 0.50,  # 50% - triggers price adjustment
    'no_reimbursements': True,
    'call_center_required': True,
}


# =============================================================================
# MAWDY SERVICE CLASS
# =============================================================================

class MAWDYService:
    """
    Service class for MAWDY integration.
    Handles service requests, eligibility checks, and usage tracking.
    """

    CONTACT_PHONE = '+502 2285-5070'
    ADDRESS = '8a. Av. 3-80 Zona 14, Edificio La Rambla II, 5to. Nivel Oficina 5-2, Guatemala'

    @classmethod
    def get_plan_services(cls, plan_type: str) -> Dict[str, Any]:
        """Get all services for a plan type."""
        if plan_type == 'DRIVE':
            return PLAN_DRIVE_SERVICES
        elif plan_type == 'HEALTH':
            return PLAN_HEALTH_SERVICES
        return {}

    @classmethod
    def get_plan_pricing(cls, plan_type: str, tier: str = 'optional', currency: str = 'USD') -> Dict[str, Decimal]:
        """Get pricing for a plan in specified currency."""
        pricing = PLAN_PRICING_GTQ if currency.upper() == 'GTQ' else PLAN_PRICING_USD
        return pricing.get(plan_type, {}).get(tier, {})

    @classmethod
    def get_all_pricing(cls, plan_type: str) -> Dict[str, Any]:
        """Get pricing in both USD and GTQ for a plan."""
        return {
            'USD': {
                'inclusion': {k: float(v) for k, v in PLAN_PRICING_USD[plan_type]['inclusion'].items()},
                'optional': {k: float(v) for k, v in PLAN_PRICING_USD[plan_type]['optional'].items()},
            },
            'GTQ': {
                'inclusion': {k: float(v) for k, v in PLAN_PRICING_GTQ[plan_type]['inclusion'].items()},
                'optional': {k: float(v) for k, v in PLAN_PRICING_GTQ[plan_type]['optional'].items()},
            },
            'exchange_rate': float(USD_TO_GTQ),
        }

    @classmethod
    def check_vehicle_eligibility(cls, vehicle_age_years: int, weight_tons: float, use_type: str) -> Dict[str, Any]:
        """Check if a vehicle is eligible for Plan Drive."""
        eligible = True
        reasons = []

        if vehicle_age_years > BUSINESS_RULES['vehicle_max_age_years']:
            eligible = False
            reasons.append(f'Vehículo excede {BUSINESS_RULES["vehicle_max_age_years"]} años de antigüedad')

        if weight_tons > BUSINESS_RULES['vehicle_max_weight_tons']:
            eligible = False
            reasons.append(f'Vehículo excede {BUSINESS_RULES["vehicle_max_weight_tons"]} toneladas')

        if use_type != 'particular':
            eligible = False
            reasons.append('Solo vehículos de uso particular')

        return {
            'eligible': eligible,
            'reasons': reasons if not eligible else ['Vehículo elegible para Plan Drive']
        }

    @classmethod
    def check_service_availability(
        cls,
        user_id: int,
        plan_type: str,
        service_code: str,
        year: int
    ) -> Dict[str, Any]:
        """
        Check if a user can request a specific service based on usage limits.

        Args:
            user_id: User ID
            plan_type: DRIVE or HEALTH
            service_code: Service code from the service definitions
            year: Year to check usage for

        Returns:
            Dictionary with availability status
        """
        services = cls.get_plan_services(plan_type)
        service = services.get(service_code)

        if not service:
            return {
                'available': False,
                'reason': 'Servicio no encontrado'
            }

        events_limit = service.get('events_per_year')

        if events_limit is None:
            # Unlimited service
            return {
                'available': True,
                'remaining_events': 'Ilimitado',
                'economic_limit': service.get('economic_limit_usd')
            }

        # Check user's usage for this year
        from apps.assistance.models import AssistanceRequest
        usage_count = AssistanceRequest.objects.filter(
            user_id=user_id,
            service_category__category_type=service_code,
            created_at__year=year,
            status__in=['COMPLETED', 'IN_PROGRESS', 'ASSIGNED']
        ).count()

        remaining = events_limit - usage_count

        return {
            'available': remaining > 0,
            'events_used': usage_count,
            'events_limit': events_limit,
            'remaining_events': max(0, remaining),
            'economic_limit': service.get('economic_limit_usd'),
            'reason': None if remaining > 0 else f'Límite de {events_limit} eventos anuales alcanzado'
        }

    @classmethod
    def create_service_request(
        cls,
        user,
        plan_type: str,
        service_code: str,
        location: Dict[str, Any],
        description: str,
        evidence_files: List = None
    ) -> Dict[str, Any]:
        """
        Create a new service request to MAWDY.

        In production, this would integrate with MAWDY's call center system.
        Currently, it creates a request that can be managed through the admin.
        """
        from django.utils import timezone
        from apps.assistance.models import AssistanceRequest

        services = cls.get_plan_services(plan_type)
        service = services.get(service_code)

        if not service:
            return {'success': False, 'error': 'Servicio no válido'}

        # Check availability
        availability = cls.check_service_availability(
            user.id, plan_type, service_code, timezone.now().year
        )

        if not availability['available']:
            return {
                'success': False,
                'error': availability['reason']
            }

        # Check evidence requirement
        if service.get('requires_evidence') and not evidence_files:
            return {
                'success': False,
                'error': 'Este servicio requiere evidencia fotográfica'
            }

        # Create request - use incident_type to store service info
        # Get or create MAWDY service category (Asistencia Vial = id 1)
        from apps.services.models import ServiceCategory
        try:
            service_cat = ServiceCategory.objects.get(id=1)  # Asistencia Vial
        except ServiceCategory.DoesNotExist:
            service_cat = ServiceCategory.objects.create(
                id=1,
                name='Asistencia Vial',
                description='Servicios de asistencia vial MAWDY'
            )

        request = AssistanceRequest.objects.create(
            user=user,
            service_category=service_cat,
            title=service['name'],
            description=f"[{plan_type}:{service_code}] {description}",
            incident_type=f"MAWDY_{service_code}",
            location_address=location.get('address', ''),
            location_city=location.get('city', 'Guatemala'),
            location_state=location.get('state', 'Guatemala'),
            location_latitude=location.get('latitude'),
            location_longitude=location.get('longitude'),
            status='PENDING',
            estimated_cost=service.get('economic_limit_usd'),
        )

        logger.info(f'MAWDY service request created: {request.request_number} - {service_code}')

        return {
            'success': True,
            'request_id': request.id,
            'request_number': request.request_number,
            'service': service['name'],
            'economic_limit': str(service.get('economic_limit_usd', 'N/A')),
            'contact_phone': cls.CONTACT_PHONE,
            'message': 'Solicitud creada. Un agente de MAWDY se comunicará contigo pronto.'
        }

    @classmethod
    def get_user_usage_summary(cls, user_id: int, plan_type: str, year: int) -> List[Dict[str, Any]]:
        """Get summary of user's service usage for the year."""
        services = cls.get_plan_services(plan_type)
        summary = []

        for code, service in services.items():
            availability = cls.check_service_availability(user_id, plan_type, code, year)
            summary.append({
                'service_code': code,
                'service_name': service['name'],
                'description': service['description'],
                'events_limit': service.get('events_per_year', 'Ilimitado'),
                'events_used': availability.get('events_used', 0),
                'remaining': availability.get('remaining_events', 'Ilimitado'),
                'economic_limit_usd': str(service.get('economic_limit_usd', 'N/A')),
                'available': availability['available'],
            })

        return summary
