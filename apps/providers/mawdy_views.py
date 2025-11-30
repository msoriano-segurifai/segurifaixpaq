"""
MAWDY API Views for SegurifAI x PAQ

Endpoints for interacting with MAWDY assistance services.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .mawdy import (
    MAWDYService,
    PLAN_DRIVE_SERVICES,
    PLAN_HEALTH_SERVICES,
    PLAN_PRICING_USD,
    PLAN_PRICING_GTQ,
    USD_TO_GTQ,
    BUSINESS_RULES,
)
from apps.users.permissions import IsAdmin


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mawdy_plans(request):
    """
    Get available MAWDY plans and pricing.

    GET /api/providers/mawdy/plans/
    """
    plans = []

    for plan_type in ['DRIVE', 'HEALTH']:
        services = MAWDYService.get_plan_services(plan_type)
        service_count = len([s for s in services.values() if s.get('events_per_year') is not None])
        unlimited_count = len([s for s in services.values() if s.get('events_per_year') is None])
        pricing_usd = PLAN_PRICING_USD[plan_type]
        pricing_gtq = PLAN_PRICING_GTQ[plan_type]

        plans.append({
            'plan_type': plan_type,
            'name': 'Plan Drive' if plan_type == 'DRIVE' else 'Plan Health',
            'description': 'Asistencia Vial' if plan_type == 'DRIVE' else 'Asistencia de Salud',
            'pricing': {
                'USD': {
                    'inclusion': {
                        'monthly': float(pricing_usd['inclusion']['monthly']),
                        'annual': float(pricing_usd['inclusion']['annual']),
                    },
                    'optional': {
                        'monthly': float(pricing_usd['optional']['monthly']),
                        'annual': float(pricing_usd['optional']['annual']),
                    }
                },
                'GTQ': {
                    'inclusion': {
                        'monthly': float(pricing_gtq['inclusion']['monthly']),
                        'annual': float(pricing_gtq['inclusion']['annual']),
                    },
                    'optional': {
                        'monthly': float(pricing_gtq['optional']['monthly']),
                        'annual': float(pricing_gtq['optional']['annual']),
                    }
                },
                'exchange_rate': float(USD_TO_GTQ),
            },
            'services_with_limit': service_count,
            'unlimited_services': unlimited_count,
            'total_services': len(services),
        })

    return Response({
        'provider': 'MAWDY',
        'contact_phone': MAWDYService.CONTACT_PHONE,
        'address': MAWDYService.ADDRESS,
        'plans': plans,
        'business_rules': {
            'geographic_area': BUSINESS_RULES['geographic_area'],
            'vehicle_max_age_years': BUSINESS_RULES['vehicle_max_age_years'],
            'vehicle_max_weight_tons': BUSINESS_RULES['vehicle_max_weight_tons'],
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_plan_services(request, plan_type):
    """
    Get all services for a specific plan.

    GET /api/providers/mawdy/plans/<plan_type>/services/
    """
    plan_type = plan_type.upper()

    if plan_type not in ['DRIVE', 'HEALTH']:
        return Response(
            {'error': 'Plan no válido. Use DRIVE o HEALTH'},
            status=status.HTTP_400_BAD_REQUEST
        )

    services = MAWDYService.get_plan_services(plan_type)

    services_list = []
    for code, service in services.items():
        services_list.append({
            'service_code': code,
            'name': service['name'],
            'description': service['description'],
            'events_per_year': service.get('events_per_year', 'Ilimitado'),
            'economic_limit_usd': float(service['economic_limit_usd']) if service.get('economic_limit_usd') else None,
            'requires_evidence': service.get('requires_evidence', False),
            'family_coverage': service.get('family_coverage', False),
        })

    return Response({
        'plan_type': plan_type,
        'plan_name': 'Plan Drive' if plan_type == 'DRIVE' else 'Plan Health',
        'services': services_list,
        'total': len(services_list)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_usage(request, plan_type):
    """
    Get current user's service usage for a plan.

    GET /api/providers/mawdy/plans/<plan_type>/my-usage/
    """
    plan_type = plan_type.upper()

    if plan_type not in ['DRIVE', 'HEALTH']:
        return Response(
            {'error': 'Plan no válido. Use DRIVE o HEALTH'},
            status=status.HTTP_400_BAD_REQUEST
        )

    year = timezone.now().year
    summary = MAWDYService.get_user_usage_summary(request.user.id, plan_type, year)

    return Response({
        'user_id': request.user.id,
        'plan_type': plan_type,
        'year': year,
        'services': summary
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_vehicle_eligibility(request):
    """
    Check if a vehicle is eligible for Plan Drive.

    POST /api/providers/mawdy/check-vehicle/

    Body:
    {
        "vehicle_age_years": 5,
        "weight_tons": 2.5,
        "use_type": "particular"
    }
    """
    vehicle_age = request.data.get('vehicle_age_years', 0)
    weight_tons = request.data.get('weight_tons', 1.5)
    use_type = request.data.get('use_type', 'particular')

    result = MAWDYService.check_vehicle_eligibility(
        int(vehicle_age),
        float(weight_tons),
        use_type
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_service_availability(request):
    """
    Check if a specific service is available for the user.

    POST /api/providers/mawdy/check-service/

    Body:
    {
        "plan_type": "DRIVE",
        "service_code": "GRUA"
    }
    """
    plan_type = request.data.get('plan_type', '').upper()
    service_code = request.data.get('service_code', '').upper()

    if not plan_type or not service_code:
        return Response(
            {'error': 'plan_type y service_code son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    year = timezone.now().year
    result = MAWDYService.check_service_availability(
        request.user.id,
        plan_type,
        service_code,
        year
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_service(request):
    """
    Request a MAWDY service.

    POST /api/providers/mawdy/request-service/

    Body:
    {
        "plan_type": "DRIVE",
        "service_code": "GRUA",
        "location": {
            "address": "Zona 10, Ciudad de Guatemala",
            "city": "Guatemala",
            "latitude": 14.6349,
            "longitude": -90.5069
        },
        "description": "Mi auto no enciende, necesito grúa"
    }
    """
    plan_type = request.data.get('plan_type', '').upper()
    service_code = request.data.get('service_code', '').upper()
    location = request.data.get('location', {})
    description = request.data.get('description', '')

    if not plan_type or not service_code:
        return Response(
            {'error': 'plan_type y service_code son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not location.get('address'):
        return Response(
            {'error': 'location.address es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = MAWDYService.create_service_request(
        user=request.user,
        plan_type=plan_type,
        service_code=service_code,
        location=location,
        description=description
    )

    if result['success']:
        return Response(result, status=status.HTTP_201_CREATED)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contact_info(request):
    """
    Get MAWDY contact information.

    GET /api/providers/mawdy/contact/
    """
    return Response({
        'provider': 'MAWDY',
        'phone': MAWDYService.CONTACT_PHONE,
        'address': MAWDYService.ADDRESS,
        'service_hours': '24/7',
        'geographic_coverage': 'Guatemala',
        'emergency_line': '+502 2285-5070',
        'instructions': [
            'Todos los servicios deben solicitarse a través de la central telefónica',
            'No se operan reembolsos',
            'Tenga a mano su número de póliza y documentos del vehículo',
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_business_rules(request):
    """
    Get MAWDY business rules (admin only).

    GET /api/providers/mawdy/business-rules/
    """
    return Response({
        'business_rules': BUSINESS_RULES,
        'pricing': {
            'USD': {
                plan: {
                    tier: {k: float(v) for k, v in prices.items()}
                    for tier, prices in tiers.items()
                }
                for plan, tiers in PLAN_PRICING_USD.items()
            },
            'GTQ': {
                plan: {
                    tier: {k: float(v) for k, v in prices.items()}
                    for tier, prices in tiers.items()
                }
                for plan, tiers in PLAN_PRICING_GTQ.items()
            },
            'exchange_rate': float(USD_TO_GTQ),
        }
    })
