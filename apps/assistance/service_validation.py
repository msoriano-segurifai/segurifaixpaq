"""
Generic Service Validation with AI + Human Review
Supports all MAWDY service types: taxi, legal, health services, etc.
"""
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
import re

logger = logging.getLogger(__name__)


# Simple validation rules for each service type
SERVICE_VALIDATION_RULES = {
    'taxi': {
        'required_fields': ['pickup_location', 'destination'],
        'auto_approve': True,
    },
    'legal': {
        'required_fields': ['legal_issue_type', 'issue_description'],
        'auto_approve': False,
    },
    'generic': {
        'required_fields': ['service_details'],
        'auto_approve': True,
    },
    'vehicle': {
        'required_fields': [],
        'auto_approve': False,
    },
    'health': {
        'required_fields': [],
        'auto_approve': False,
    },
    'consultation': {
        'required_fields': ['specialty', 'reason'],
        'auto_approve': True,
    },
    'video_consultation': {
        'required_fields': ['specialty', 'symptoms'],
        'auto_approve': True,
    },
    'lab_exam': {
        'required_fields': ['exam_types'],
        'auto_approve': True,
    },
    'medication': {
        'required_fields': ['medications'],
        'auto_approve': False,
    },
    'delivery': {
        'required_fields': ['delivery_address', 'items'],
        'auto_approve': True,
    },
}


def validate_taxi_request(data):
    """Validate taxi service request"""
    taxi_info = data.get('taxi_info', {})

    if not taxi_info.get('pickup_location'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'La direccion de recogida es requerida',
        }

    if not taxi_info.get('destination'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'El destino es requerido',
        }

    # Auto-approve taxi requests
    return {
        'validation_status': 'APPROVED',
        'validation_message': f"Servicio de taxi confirmado: {taxi_info.get('pickup_location')} -> {taxi_info.get('destination')}",
        'auto_approved': True,
    }


def validate_legal_request(data):
    """Validate legal assistance request - requires human review"""
    legal_info = data.get('legal_info', {})

    if not legal_info.get('legal_issue_type'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'El tipo de asunto legal es requerido',
        }

    if not legal_info.get('issue_description'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'La descripcion del asunto es requerida',
        }

    # Legal issues always need human review
    urgency = legal_info.get('urgency', 'MEDIUM')
    related_to_accident = legal_info.get('related_to_accident', False)

    # Prioritize accident-related legal issues
    if related_to_accident:
        return {
            'validation_status': 'PENDING_REVIEW',
            'validation_message': 'Asunto legal relacionado con accidente. Un abogado de MAWDY te contactara prioritariamente.',
            'urgency_level': 'HIGH',
            'priority': True,
        }

    return {
        'validation_status': 'PENDING_REVIEW',
        'validation_message': 'Tu solicitud de asistencia legal ha sido recibida. Un abogado de MAWDY revisara tu caso.',
        'urgency_level': urgency,
    }


def validate_consultation_request(data):
    """Validate medical consultation request"""
    consultation_info = data.get('consultation_info', {})

    if not consultation_info.get('specialty'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'La especialidad medica es requerida',
        }

    if not consultation_info.get('reason'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'El motivo de la consulta es requerido',
        }

    specialty = consultation_info.get('specialty', '')
    preferred_date = consultation_info.get('preferred_date', 'Por confirmar')
    preferred_time = consultation_info.get('preferred_time', 'Por confirmar')

    return {
        'validation_status': 'APPROVED',
        'validation_message': f'Cita de {specialty} programada. Fecha: {preferred_date}, Horario: {preferred_time}. Te contactaremos para confirmar.',
        'auto_approved': True,
        'appointment_details': {
            'specialty': specialty,
            'date': preferred_date,
            'time': preferred_time,
        }
    }


def validate_video_consultation_request(data):
    """Validate video consultation request"""
    video_info = data.get('video_consultation_info', {})

    if not video_info.get('specialty'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'La especialidad medica es requerida',
        }

    if not video_info.get('symptoms'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'Por favor describe tus sintomas',
        }

    specialty = video_info.get('specialty', '')
    urgency = video_info.get('urgency', 'normal')

    # Priority for urgent cases
    if urgency == 'urgent':
        return {
            'validation_status': 'APPROVED',
            'validation_message': f'Video consulta urgente de {specialty} solicitada. Te enviaremos el enlace en los proximos 30 minutos.',
            'auto_approved': True,
            'priority': True,
        }

    return {
        'validation_status': 'APPROVED',
        'validation_message': f'Video consulta de {specialty} programada. Recibiras un enlace para conectarte.',
        'auto_approved': True,
    }


def validate_lab_exam_request(data):
    """Validate laboratory exam request"""
    lab_info = data.get('lab_exam_info', {})

    if not lab_info.get('exam_types'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'Selecciona al menos un tipo de examen',
        }

    exam_types = lab_info.get('exam_types', [])
    fasting_required = lab_info.get('fasting_required', False)
    preferred_date = lab_info.get('preferred_date', 'Por confirmar')
    home_service = lab_info.get('home_service', False)

    location_msg = 'Servicio a domicilio solicitado.' if home_service else 'Acude al laboratorio mas cercano.'
    fasting_msg = ' Recuerda estar en ayunas.' if fasting_required else ''

    return {
        'validation_status': 'APPROVED',
        'validation_message': f'Examenes solicitados: {", ".join(exam_types)}. {location_msg}{fasting_msg}',
        'auto_approved': True,
        'exam_details': {
            'types': exam_types,
            'date': preferred_date,
            'home_service': home_service,
            'fasting_required': fasting_required,
        }
    }


def validate_medication_request(data):
    """Validate medication delivery request - requires prescription review"""
    medication_info = data.get('medication_info', {})

    if not medication_info.get('medications'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'Indica los medicamentos que necesitas',
        }

    medications = medication_info.get('medications', '')
    has_prescription = medication_info.get('has_prescription', False)
    prescription_image = medication_info.get('prescription_image')

    # Controlled medications need prescription verification
    controlled_keywords = ['tramadol', 'codeina', 'diazepam', 'clonazepam', 'alprazolam', 'morfina']
    needs_verification = any(kw in medications.lower() for kw in controlled_keywords)

    if needs_verification and not has_prescription:
        return {
            'validation_status': 'PENDING_REVIEW',
            'validation_message': 'Los medicamentos solicitados requieren receta medica. Por favor adjunta tu receta o un agente te contactara.',
            'requires_prescription': True,
        }

    if has_prescription:
        return {
            'validation_status': 'APPROVED',
            'validation_message': 'Solicitud de medicamentos recibida. Verificaremos la receta y te enviaremos tu pedido.',
            'auto_approved': True,
        }

    return {
        'validation_status': 'APPROVED',
        'validation_message': 'Solicitud de medicamentos recibida. Te contactaremos para confirmar disponibilidad y entrega.',
        'auto_approved': True,
    }


def validate_delivery_request(data):
    """Validate general delivery request"""
    delivery_info = data.get('delivery_info', {})

    if not delivery_info.get('delivery_address'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'La direccion de entrega es requerida',
        }

    if not delivery_info.get('items'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'Indica que necesitas que te entreguemos',
        }

    items = delivery_info.get('items', '')
    address = delivery_info.get('delivery_address', '')
    urgent = delivery_info.get('urgent', False)

    if urgent:
        return {
            'validation_status': 'APPROVED',
            'validation_message': f'Entrega urgente solicitada a: {address}. Llegara en las proximas 2 horas.',
            'auto_approved': True,
            'priority': True,
        }

    return {
        'validation_status': 'APPROVED',
        'validation_message': f'Entrega programada a: {address}. Te notificaremos cuando el repartidor este en camino.',
        'auto_approved': True,
    }


def validate_generic_request(data):
    """Validate generic service request"""
    generic_info = data.get('generic_info', {})
    service_name = data.get('service_name', 'Servicio')

    if not generic_info.get('service_details'):
        return {
            'validation_status': 'FAILED',
            'validation_message': 'Por favor describe lo que necesitas',
        }

    # Check for potentially complex requests that need review
    details = generic_info.get('service_details', '').lower()
    needs_review_keywords = ['urgente', 'emergencia', 'grave', 'accidente', 'hospital']

    if any(keyword in details for keyword in needs_review_keywords):
        return {
            'validation_status': 'PENDING_REVIEW',
            'validation_message': f'Tu solicitud de {service_name} sera revisada prioritariamente por un agente MAWDY.',
            'urgency_level': 'HIGH',
        }

    # Auto-approve simple generic requests
    return {
        'validation_status': 'APPROVED',
        'validation_message': f'Solicitud de {service_name} confirmada. Te contactaremos pronto.',
        'auto_approved': True,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_service(request):
    """
    Generic service validation endpoint.
    Routes to specific validators based on form_type.
    """
    try:
        data = request.data
        service_id = data.get('service_id')
        service_name = data.get('service_name', 'Servicio')
        plan_type = data.get('plan_type')
        form_type = data.get('form_type', 'generic')

        logger.info(f"Validating service request: {service_id} ({form_type}) for user {request.user.id}")

        # Route to specific validator based on form_type
        validators = {
            'taxi': validate_taxi_request,
            'legal': validate_legal_request,
            'generic': validate_generic_request,
            'consultation': validate_consultation_request,
            'video_consultation': validate_video_consultation_request,
            'lab_exam': validate_lab_exam_request,
            'medication': validate_medication_request,
            'delivery': validate_delivery_request,
        }

        validator = validators.get(form_type)
        if validator:
            result = validator(data)
        else:
            # Default auto-approve for unknown types
            result = {
                'validation_status': 'APPROVED',
                'validation_message': f'Solicitud de {service_name} recibida.',
                'auto_approved': True,
            }

        # Add common fields
        result['service_id'] = service_id
        result['service_name'] = service_name
        result['plan_type'] = plan_type
        result['form_type'] = form_type

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Service validation error: {str(e)}")
        return Response({
            'validation_status': 'PENDING_REVIEW',
            'validation_message': 'Tu solicitud sera revisada por un agente MAWDY.',
            'error': str(e),
        }, status=status.HTTP_200_OK)
