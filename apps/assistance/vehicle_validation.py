"""
Vehicle Validation with AI and Human Review Workflow
"""
import re
import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import anthropic
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class VehicleValidation(models.Model):
    """Model to track vehicle validations"""

    class ValidationStatus(models.TextChoices):
        APPROVED = 'APPROVED', 'Approved'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Manual Review'
        REJECTED = 'REJECTED', 'Rejected'
        FAILED = 'FAILED', 'Validation Failed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_validations')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.CharField(max_length=4)
    plate = models.CharField(max_length=20)
    color = models.CharField(max_length=50, blank=True)
    vin = models.CharField(max_length=17, blank=True)

    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING_REVIEW
    )
    validation_message = models.TextField(blank=True)
    ai_confidence_score = models.FloatField(null=True, blank=True)
    ai_analysis = models.JSONField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_validations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'validation_status']),
            models.Index(fields=['plate']),
        ]

    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.plate}"


def validate_vehicle_format(make: str, model: str, year: str, plate: str) -> dict:
    """
    Basic format validation before AI processing
    """
    errors = []

    # Validate year
    if not year.isdigit() or len(year) != 4:
        errors.append("Año debe ser 4 dígitos")
    else:
        year_int = int(year)
        if year_int < 1900 or year_int > 2026:
            errors.append("Año inválido (debe estar entre 1900-2025)")

    # Validate plate format (Guatemala typical formats)
    # Examples: P-123ABC, 123-ABC, P123ABC
    plate_clean = plate.upper().replace('-', '').replace(' ', '')
    if len(plate_clean) < 5 or len(plate_clean) > 8:
        errors.append("Formato de placa inválido")

    # Validate make and model
    if len(make.strip()) < 2:
        errors.append("Marca inválida")
    if len(model.strip()) < 2:
        errors.append("Modelo inválido")

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def ai_validate_vehicle(make: str, model: str, year: str, plate: str, color: str = '', vin: str = '') -> dict:
    """
    Use Claude AI to validate vehicle information
    Returns: {
        'valid': bool,
        'confidence': float (0-1),
        'status': 'APPROVED' | 'PENDING_REVIEW' | 'REJECTED',
        'message': str,
        'analysis': dict
    }
    """
    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""Eres un experto en validación de información vehicular para Guatemala.

Analiza la siguiente información de un vehículo y determina si es válida y coherente:

Marca: {make}
Modelo: {model}
Año: {year}
Placa: {plate}
Color: {color or 'No especificado'}
VIN: {vin or 'No especificado'}

Valida:
1. ¿La marca existe y está correctamente escrita?
2. ¿El modelo corresponde a esa marca?
3. ¿El año es coherente con ese modelo? (algunos modelos solo existen en ciertos años)
4. ¿La placa tiene un formato válido para Guatemala?
5. ¿El VIN (si se proporcionó) tiene formato válido (17 caracteres)?

Responde en formato JSON con:
{{
  "valid": true/false,
  "confidence": 0.0-1.0,
  "issues": ["lista de problemas encontrados"],
  "recommendations": ["recomendaciones si no puedes validar completamente"],
  "marca_valida": true/false,
  "modelo_coherente": true/false,
  "anio_coherente": true/false,
  "placa_formato_ok": true/false,
  "vin_valido": true/false/null (null si no se proporcionó),
  "reasoning": "breve explicación de tu análisis"
}}

Si hay dudas moderadas pero la información parece generalmente correcta, marca valid como false y añade recomendaciones.
Si la información es claramente inventada o incoherente, marca valid como false.
Si todo parece correcto, marca valid como true con confianza alta."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Extract JSON from response
        response_text = message.content[0].text

        # Try to parse JSON from the response
        import json
        # Find JSON in the response (it might be wrapped in markdown code blocks)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            ai_result = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in AI response")

        # Determine validation status based on AI analysis
        confidence = ai_result.get('confidence', 0.0)
        valid = ai_result.get('valid', False)
        has_issues = len(ai_result.get('issues', [])) > 0

        if valid and confidence >= 0.85:
            validation_status = 'APPROVED'
            message = "Vehículo validado exitosamente por IA"
        elif valid and confidence >= 0.65:
            validation_status = 'APPROVED'
            message = "Vehículo validado. Información parece correcta."
        elif has_issues:
            validation_status = 'PENDING_REVIEW'
            issues_str = ', '.join(ai_result.get('issues', []))
            message = f"Requiere revisión manual. Posibles problemas: {issues_str}"
        else:
            validation_status = 'PENDING_REVIEW'
            message = "Requiere revisión manual por baja confianza de validación automática"

        return {
            'valid': valid,
            'confidence': confidence,
            'status': validation_status,
            'message': message,
            'analysis': ai_result
        }

    except Exception as e:
        logger.error(f"AI vehicle validation error: {str(e)}")
        # If AI fails, send to manual review
        return {
            'valid': False,
            'confidence': 0.0,
            'status': 'PENDING_REVIEW',
            'message': 'No se pudo validar automáticamente. Un agente MAWDY revisará la información.',
            'analysis': {'error': str(e)}
        }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_vehicle(request):
    """
    API endpoint to validate vehicle information
    Uses AI validation with fallback to human review
    """
    make = request.data.get('make', '').strip()
    model = request.data.get('model', '').strip()
    year = request.data.get('year', '').strip()
    plate = request.data.get('plate', '').strip()
    color = request.data.get('color', '').strip()
    vin = request.data.get('vin', '').strip()

    # Basic format validation
    format_validation = validate_vehicle_format(make, model, year, plate)
    if not format_validation['valid']:
        return Response({
            'validation_status': 'FAILED',
            'validation_message': 'Errores de formato: ' + ', '.join(format_validation['errors']),
            'errors': format_validation['errors']
        }, status=status.HTTP_400_BAD_REQUEST)

    # AI validation
    ai_result = ai_validate_vehicle(make, model, year, plate, color, vin)

    # Create validation record
    validation = VehicleValidation.objects.create(
        user=request.user,
        make=make,
        model=model,
        year=year,
        plate=plate,
        color=color,
        vin=vin,
        validation_status=ai_result['status'],
        validation_message=ai_result['message'],
        ai_confidence_score=ai_result['confidence'],
        ai_analysis=ai_result['analysis']
    )

    logger.info(
        f"Vehicle validation created: {validation.id} - Status: {validation.validation_status} - "
        f"User: {request.user.email} - Vehicle: {year} {make} {model}"
    )

    return Response({
        'id': validation.id,
        'validation_status': validation.validation_status,
        'validation_message': validation.validation_message,
        'confidence_score': ai_result['confidence'],
        'requires_review': validation.validation_status == 'PENDING_REVIEW',
        'vehicle_info': {
            'make': make,
            'model': model,
            'year': year,
            'plate': plate,
            'color': color,
            'vin': vin
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_validations(request):
    """
    Get all pending vehicle validations (for MAWDY agents)
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Solo agentes MAWDY pueden acceder a esta información'},
            status=status.HTTP_403_FORBIDDEN
        )

    validations = VehicleValidation.objects.filter(
        validation_status=VehicleValidation.ValidationStatus.PENDING_REVIEW
    )

    data = [{
        'id': v.id,
        'user': v.user.email,
        'vehicle': f"{v.year} {v.make} {v.model}",
        'plate': v.plate,
        'color': v.color,
        'vin': v.vin,
        'ai_confidence': v.ai_confidence_score,
        'ai_analysis': v.ai_analysis,
        'created_at': v.created_at,
    } for v in validations]

    return Response({'validations': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_validation(request, validation_id):
    """
    Approve a vehicle validation (MAWDY agents only)
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Solo agentes MAWDY pueden aprobar validaciones'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        validation = VehicleValidation.objects.get(id=validation_id)
    except VehicleValidation.DoesNotExist:
        return Response({'error': 'Validación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    notes = request.data.get('notes', '')

    validation.validation_status = VehicleValidation.ValidationStatus.APPROVED
    validation.reviewed_by = request.user
    validation.reviewed_at = timezone.now()
    validation.review_notes = notes
    validation.validation_message = 'Aprobado por agente MAWDY'
    validation.save()

    logger.info(f"Vehicle validation {validation_id} approved by {request.user.email}")

    return Response({
        'success': True,
        'message': 'Validación aprobada exitosamente',
        'validation_id': validation_id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_validation(request, validation_id):
    """
    Reject a vehicle validation (MAWDY agents only)
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Solo agentes MAWDY pueden rechazar validaciones'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        validation = VehicleValidation.objects.get(id=validation_id)
    except VehicleValidation.DoesNotExist:
        return Response({'error': 'Validación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    reason = request.data.get('reason', 'Información vehicular inválida')
    notes = request.data.get('notes', '')

    validation.validation_status = VehicleValidation.ValidationStatus.REJECTED
    validation.reviewed_by = request.user
    validation.reviewed_at = timezone.now()
    validation.review_notes = notes
    validation.validation_message = reason
    validation.save()

    logger.info(f"Vehicle validation {validation_id} rejected by {request.user.email}: {reason}")

    return Response({
        'success': True,
        'message': 'Validación rechazada',
        'validation_id': validation_id
    })
