"""
Health Emergency Validation with AI and Human Review Workflow
"""
import re
import json
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


class HealthValidation(models.Model):
    """Model to track health emergency validations"""

    class ValidationStatus(models.TextChoices):
        APPROVED = 'APPROVED', 'Approved'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Manual Review'
        REJECTED = 'REJECTED', 'Rejected'
        FAILED = 'FAILED', 'Validation Failed'

    class UrgencyLevel(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical - Immediate Response'
        HIGH = 'HIGH', 'High - Urgent'
        MEDIUM = 'MEDIUM', 'Medium - Soon'
        LOW = 'LOW', 'Low - Routine'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_validations')
    emergency_type = models.CharField(max_length=100)
    symptoms = models.TextField()
    patient_age = models.CharField(max_length=10)
    patient_gender = models.CharField(max_length=20)
    consciousness_level = models.CharField(max_length=20)
    breathing_difficulty = models.BooleanField(default=False)
    chest_pain = models.BooleanField(default=False)
    bleeding = models.BooleanField(default=False)
    pre_existing_conditions = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    people_affected = models.CharField(max_length=10, default='1')

    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING_REVIEW
    )
    urgency_level = models.CharField(
        max_length=20,
        choices=UrgencyLevel.choices,
        default=UrgencyLevel.MEDIUM
    )
    validation_message = models.TextField(blank=True)
    ai_confidence_score = models.FloatField(null=True, blank=True)
    ai_analysis = models.JSONField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_health_validations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'validation_status']),
            models.Index(fields=['urgency_level']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.emergency_type} - {self.user.email} ({self.urgency_level})"


def calculate_risk_score(
    consciousness_level: str,
    breathing_difficulty: bool,
    chest_pain: bool,
    bleeding: bool,
    patient_age: str,
    symptoms: str,
    emergency_type: str,
    pre_existing_conditions: str
) -> dict:
    """Calculate preliminary risk score based on clinical indicators"""
    risk_score = 0
    risk_factors = []

    # Age-based risk
    try:
        age = int(patient_age)
        if age < 2 or age > 65:
            risk_score += 15
            risk_factors.append(f"Edad de riesgo: {age} años")
    except:
        pass

    # Consciousness level (highest priority)
    if consciousness_level in ['UNCONSCIOUS', 'UNRESPONSIVE']:
        risk_score += 50
        risk_factors.append("Paciente inconsciente - CRÍTICO")
    elif consciousness_level in ['CONFUSED', 'DROWSY']:
        risk_score += 30
        risk_factors.append("Alteración del estado mental")

    # Critical symptoms (ABC - Airway, Breathing, Circulation)
    if breathing_difficulty:
        risk_score += 40
        risk_factors.append("Dificultad respiratoria")
    if chest_pain:
        risk_score += 35
        risk_factors.append("Dolor de pecho - posible evento cardíaco")
    if bleeding:
        risk_score += 30
        risk_factors.append("Sangrado activo")

    # Emergency type severity
    high_risk_emergencies = ['PROBLEMA_CARDIACO', 'DIFICULTAD_RESPIRATORIA', 'CONVULSIONES', 'STROKE']
    medium_risk_emergencies = ['ACCIDENTE', 'LESION', 'INTOXICACION']
    if emergency_type in high_risk_emergencies:
        risk_score += 25
    elif emergency_type in medium_risk_emergencies:
        risk_score += 15

    # High-risk symptoms
    critical_symptoms = ['convuls', 'inconsci', 'desmay', 'ahog', 'paral', 'infarto']
    symptoms_lower = symptoms.lower()
    for symptom in critical_symptoms:
        if symptom in symptoms_lower:
            risk_score += 20
            risk_factors.append(f"Síntoma crítico detectado: {symptom}")
            break

    # Comorbidities
    high_risk_conditions = ['diabetes', 'hipertens', 'cardio', 'cancer', 'inmuno']
    conditions_lower = pre_existing_conditions.lower()
    for condition in high_risk_conditions:
        if condition in conditions_lower:
            risk_score += 10
            risk_factors.append(f"Condición preexistente de alto riesgo")
            break

    # Determine severity category
    if risk_score >= 70:
        severity = 'CRITICAL'
    elif risk_score >= 45:
        severity = 'HIGH'
    elif risk_score >= 20:
        severity = 'MEDIUM'
    else:
        severity = 'LOW'

    return {
        'risk_score': min(risk_score, 100),
        'severity': severity,
        'risk_factors': risk_factors,
        'requires_immediate_review': risk_score >= 50
    }


def ai_validate_health(
    emergency_type: str,
    symptoms: str,
    patient_age: str,
    patient_gender: str,
    consciousness_level: str,
    breathing_difficulty: bool,
    chest_pain: bool,
    bleeding: bool,
    pre_existing_conditions: str = '',
    medications: str = '',
    people_affected: str = '1'
) -> dict:
    """
    Use Claude AI to validate health emergency information and determine urgency
    Includes pre-screening risk assessment for maximum safety
    Returns: {
        'valid': bool,
        'confidence': float (0-1),
        'status': 'APPROVED' | 'PENDING_REVIEW' | 'REJECTED',
        'urgency_level': 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW',
        'message': str,
        'analysis': dict
    }
    """
    try:
        # Step 1: Calculate preliminary risk score (safety net)
        risk_assessment = calculate_risk_score(
            consciousness_level, breathing_difficulty, chest_pain, bleeding,
            patient_age, symptoms, emergency_type, pre_existing_conditions
        )

        # Step 2: Auto-escalate CRITICAL cases immediately (bypass AI for safety)
        if risk_assessment['requires_immediate_review']:
            logger.critical(f"AUTO-ESCALATED: Risk score {risk_assessment['risk_score']} - {', '.join(risk_assessment['risk_factors'])}")
            return {
                'valid': True,
                'confidence': 1.0,
                'status': 'PENDING_REVIEW',
                'urgency_level': 'CRITICAL',
                'message': f"🚨 EMERGENCIA CRÍTICA DETECTADA. Un agente médico MAWDY ha sido notificado INMEDIATAMENTE. Factores de riesgo: {', '.join(risk_assessment['risk_factors'][:2])}.",
                'analysis': {
                    'risk_assessment': risk_assessment,
                    'auto_escalated': True,
                    'reason': 'Risk score exceeds critical threshold'
                }
            }

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""Eres un experto en triaje médico y evaluación de emergencias para servicios de asistencia médica en Guatemala.

CONTEXTO DEL SISTEMA:
- Pre-evaluación de riesgo: {risk_assessment['severity']} (Score: {risk_assessment['risk_score']}/100)
- Factores de riesgo detectados: {', '.join(risk_assessment['risk_factors']) if risk_assessment['risk_factors'] else 'Ninguno'}

TU MISIÓN CRÍTICA:
- Identificar emergencias de VIDA O MUERTE que requieren intervención humana inmediata
- Auto-aprobar casos RUTINARIOS de baja-media complejidad que pueden ser manejados por técnicos MAWDY
- Ser CONSERVADOR: cuando tengas duda o detectes inconsistencias, requiere revisión humana
- Validar que la información sea coherente y completa

Analiza la siguiente información de una emergencia médica y determina:
1. ¿Es una emergencia real que requiere asistencia médica?
2. ¿Cuál es el nivel de urgencia (CRITICAL, HIGH, MEDIUM, LOW)?
3. ¿La información proporcionada es coherente y suficiente?
4. ¿Se requiere respuesta inmediata de ambulancia?
5. ¿Requiere revisión de un profesional médico MAWDY antes de proceder?

INFORMACIÓN DEL PACIENTE:
Tipo de emergencia: {emergency_type}
Síntomas: {symptoms}
Edad: {patient_age} años
Género: {patient_gender}
Nivel de conciencia: {consciousness_level}
Dificultad para respirar: {'SÍ' if breathing_difficulty else 'NO'}
Dolor de pecho: {'SÍ' if chest_pain else 'NO'}
Sangrado severo: {'SÍ' if bleeding else 'NO'}
Condiciones preexistentes: {pre_existing_conditions or 'Ninguna reportada'}
Medicamentos actuales: {medications or 'Ninguno reportado'}
Personas afectadas: {people_affected}

CRITERIOS DE URGENCIA Y DECISIÓN (Basado en Triaje START/JumpSTART):

🚨 CRITICAL (Crítico) → SIEMPRE requires_human_review = true:
  • ABC comprometido: Vía aérea, Respiración, Circulación
  • Inconsciente o no responde (GCS < 8)
  • Dificultad respiratoria severa o apnea
  • Dolor de pecho con signos de infarto (sudoración, náuseas, dolor irradiado)
  • Sangrado masivo no controlado
  • Convulsiones activas o status epilepticus
  • Shock (palidez, sudoración fría, taquicardia)
  • Stroke/ACV (parálisis facial, debilidad unilateral, confusión súbita)
  DECISIÓN: Ambulancia + Revisión médica humana INMEDIATA

⚠️ HIGH (Alto) → requires_human_review = true SI hay factores de riesgo:
  • Dolor severo persistente (>7/10)
  • Fiebre alta (>39°C) con rigidez nucal o alteración mental
  • Trauma moderado-severo (caídas desde altura, accidentes vehiculares)
  • Fractura abierta o dislocación evidente
  • Quemaduras de 2do-3er grado >10% superficie corporal
  • Abdomen agudo (dolor abdominal severo + vómito/fiebre)
  • Deshidratación severa (vómito/diarrea persistente)
  • Paciente oncológico, diabético, o con enfermedad cardíaca previa
  • Múltiples síntomas de gravedad moderada
  • Embarazo con sangrado o dolor severo
  DECISIÓN: Si hay ≥2 factores de alto riesgo → requires_human_review = true

✓ MEDIUM (Medio) → AUTO-APROBAR si confianza >= 80%:
  • Síntomas molestos pero estables y sin progresión
  • Sin signos de peligro vital inmediato
  • Paciente consciente, alerta, y orientado
  • Situación claramente definida y coherente
  • Dolor moderado controlable (4-6/10)
  • Fiebre moderada (<39°C) sin signos de alarma
  • Lesiones menores (esguinces, contusiones leves)
  • Náuseas/vómito sin deshidratación
  DECISIÓN: AUTO-APROBAR con monitoreo. Técnico MAWDY puede manejar.

ℹ️ LOW (Bajo) → AUTO-APROBAR si confianza >= 70%:
  • Síntomas leves y estables
  • No requiere atención inmediata (puede esperar 24-48h)
  • Consulta de rutina o seguimiento
  • Dolor leve (<4/10)
  • Síntomas crónicos conocidos sin cambios
  DECISIÓN: AUTO-APROBAR. Orientación telefónica suficiente.

VALIDACIÓN DE COHERENCIA:
- Verifica que edad, género, síntomas, y tipo de emergencia sean coherentes
- Detecta información contradictoria o sospechosa
- Si hay inconsistencias significativas → requires_human_review = true

FACTORES DE MÚLTIPLES VÍCTIMAS:
- Si people_affected > 2 → aumentar urgencia en 1 nivel
- Si people_affected >= 4 → CRITICAL + revisión humana obligatoria

Responde SOLO en formato JSON (sin texto adicional):
{{
  "valid": true/false,
  "confidence": 0.0-1.0,
  "urgency_level": "CRITICAL"|"HIGH"|"MEDIUM"|"LOW",
  "requires_ambulance": true/false,
  "requires_human_review": true/false,
  "red_flags": ["lista de signos de alarma identificados"],
  "coherence_issues": ["lista de inconsistencias detectadas"],
  "recommended_action": "descripción breve de acción recomendada",
  "recommendations": ["recomendaciones para el paciente"],
  "reasoning": "explicación detallada de tu análisis",
  "estimated_response_time": "tiempo sugerido de respuesta (ej: 'inmediato', '15-30 min', '1-2 horas')"
}}

Si hay CUALQUIER signo de alarma (dificultad respiratoria, dolor de pecho, inconsciente, sangrado severo), marca como CRITICAL.
Si la información es insuficiente o incoherente, marca requires_human_review como true.
Si detectas que puede ser una situación de vida o muerte, marca urgency_level como CRITICAL."""

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
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            ai_result = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in AI response")

        # Step 3: Extract and analyze AI response
        confidence = ai_result.get('confidence', 0.0)
        valid = ai_result.get('valid', False)
        urgency_level = ai_result.get('urgency_level', 'MEDIUM')
        requires_human_review = ai_result.get('requires_human_review', False)
        requires_ambulance = ai_result.get('requires_ambulance', False)
        red_flags = ai_result.get('red_flags', [])
        coherence_issues = ai_result.get('coherence_issues', [])
        recommended_action = ai_result.get('recommended_action', '')
        recommendations = ai_result.get('recommendations', [])

        # Step 4: Multiple victims escalation (mass casualty protocol)
        try:
            num_affected = int(people_affected.replace('+', '')) if people_affected else 1
            if num_affected > 2:
                # Escalate urgency for mass casualty
                urgency_levels_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
                current_index = urgency_levels_order.index(urgency_level) if urgency_level in urgency_levels_order else 1
                new_index = min(current_index + 1, len(urgency_levels_order) - 1)
                urgency_level = urgency_levels_order[new_index]
                red_flags.append(f"Múltiples víctimas: {people_affected} personas afectadas")

            if num_affected >= 4:
                # Mass casualty - automatic critical escalation
                urgency_level = 'CRITICAL'
                requires_human_review = True
                requires_ambulance = True
                red_flags.append("INCIDENTE DE MÚLTIPLES VÍCTIMAS - Protocolos de emergencia masiva activados")
                logger.critical(f"MASS CASUALTY INCIDENT: {people_affected} people affected")
        except:
            pass

        # Step 5: Coherence validation
        has_coherence_issues = len(coherence_issues) > 0
        if has_coherence_issues:
            requires_human_review = True
            logger.warning(f"Coherence issues detected: {coherence_issues}")

        # Step 6: Safety checks for conservative evaluation
        has_red_flags = len(red_flags) > 0
        is_high_urgency = urgency_level in ['CRITICAL', 'HIGH']

        # ENHANCED DECISION TREE (Multi-layered safety approach):
        # Layer 1: CRITICAL cases (immediate escalation)
        # Layer 2: HIGH urgency cases (rapid human review)
        # Layer 3: MEDIUM/LOW with high confidence (auto-approve)
        # Layer 4: Everything else (default to human review)

        if urgency_level == 'CRITICAL' or requires_ambulance or (has_red_flags and is_high_urgency):
            # Layer 1: CRITICAL - Immediate human intervention
            validation_status = 'PENDING_REVIEW'
            urgency_level = 'CRITICAL'
            red_flags_str = '; '.join(red_flags[:3]) if red_flags else 'signos de emergencia críticos'
            message = f"🚨 EMERGENCIA CRÍTICA DETECTADA: {red_flags_str}. Un agente médico MAWDY ha sido notificado INMEDIATAMENTE para coordinar respuesta de emergencia."
            if recommended_action:
                message += f" Acción recomendada: {recommended_action}"
            logger.critical(f"CRITICAL health emergency: {emergency_type} - Risk: {risk_assessment['risk_score']} - Flags: {red_flags}")

        elif urgency_level == 'HIGH' or requires_human_review or confidence < 0.75 or has_coherence_issues:
            # Layer 2: HIGH - Needs rapid human review
            validation_status = 'PENDING_REVIEW'
            if has_coherence_issues:
                message = f"⚠️ Requiere revisión humana. Se detectaron inconsistencias en la información. Un agente MAWDY evaluará tu caso."
            else:
                message = f"⚠️ Nivel de urgencia {urgency_level}. Requiere evaluación de agente médico MAWDY."
                if recommendations:
                    message += f" Mientras esperas: {recommendations[0]}"
            logger.info(f"HIGH priority case - requires human review: {emergency_type}")

        elif not valid or confidence < 0.70:
            # Layer 3b: Invalid or very low confidence
            validation_status = 'PENDING_REVIEW'
            message = "La información proporcionada requiere validación adicional por un agente médico MAWDY para garantizar atención adecuada."

        elif valid and confidence >= 0.85 and urgency_level in ['MEDIUM', 'LOW']:
            # Layer 3: Auto-approve high confidence, stable cases
            validation_status = 'APPROVED'
            message = f"✓ Solicitud validada. Nivel de urgencia: {urgency_level}. Un técnico MAWDY será asignado pronto."
            if recommended_action:
                message += f" {recommended_action}"
            logger.info(f"AUTO-APPROVED: {emergency_type} - Confidence: {confidence:.2f}")

        elif valid and confidence >= 0.75 and urgency_level in ['MEDIUM', 'LOW']:
            # Layer 3a: Auto-approve medium-high confidence
            validation_status = 'APPROVED'
            message = f"✓ Información validada. Urgencia: {urgency_level}. Te contactaremos pronto."
            logger.info(f"APPROVED (medium confidence): {emergency_type} - Confidence: {confidence:.2f}")

        else:
            # Default: Send to human review (conservative approach)
            validation_status = 'PENDING_REVIEW'
            message = "Requiere revisión manual por un agente médico MAWDY para garantizar la mejor atención."

        # Step 7: Return enriched validation result
        return {
            'valid': valid,
            'confidence': confidence,
            'status': validation_status,
            'urgency_level': urgency_level,
            'message': message,
            'analysis': {
                **ai_result,  # Include full AI response
                'risk_assessment': risk_assessment,  # Include pre-screening risk assessment
                'decision_rationale': {
                    'has_red_flags': has_red_flags,
                    'has_coherence_issues': has_coherence_issues,
                    'requires_ambulance': requires_ambulance,
                    'final_confidence': confidence,
                    'automated_decision': validation_status == 'APPROVED'
                }
            },
            'red_flags': red_flags,  # Surface red flags for frontend display
            'recommendations': recommendations,  # Patient recommendations
            'recommended_action': recommended_action  # Immediate action needed
        }

    except json.JSONDecodeError as e:
        logger.error(f"AI health validation JSON parse error: {str(e)} - Response: {response_text[:200]}")
        # AI returned invalid JSON - send to human review
        return {
            'valid': False,
            'confidence': 0.0,
            'status': 'PENDING_REVIEW',
            'urgency_level': 'MEDIUM',
            'message': 'No se pudo validar automáticamente. Un agente MAWDY médico revisará tu solicitud de inmediato.',
            'analysis': {'error': 'JSON parse error', 'raw_response': response_text[:500]}
        }
    except Exception as e:
        logger.error(f"AI health validation error: {str(e)} - Emergency: {emergency_type}")
        logger.exception("Full health validation error traceback:")
        # If AI fails for ANY reason, send to manual review
        # SAFETY FIRST: When in doubt, get human expert involved
        return {
            'valid': False,
            'confidence': 0.0,
            'status': 'PENDING_REVIEW',
            'urgency_level': 'HIGH',  # Elevate to HIGH when AI fails
            'message': '🔔 La IA no pudo procesar tu solicitud. Un agente MAWDY médico revisará tu caso PRIORITARIAMENTE.',
            'analysis': {'error': str(e), 'error_type': type(e).__name__}
        }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_health(request):
    """
    API endpoint to validate health emergency information
    Uses AI validation with fallback to human review
    """
    emergency_type = request.data.get('emergency_type', '').strip()
    symptoms = request.data.get('symptoms', '').strip()
    patient_age = request.data.get('patient_age', '').strip()
    patient_gender = request.data.get('patient_gender', '').strip()
    consciousness_level = request.data.get('consciousness_level', 'CONSCIOUS').strip()
    breathing_difficulty = request.data.get('breathing_difficulty', False)
    chest_pain = request.data.get('chest_pain', False)
    bleeding = request.data.get('bleeding', False)
    pre_existing_conditions = request.data.get('pre_existing_conditions', '').strip()
    medications = request.data.get('medications', '').strip()
    people_affected = request.data.get('people_affected', '1').strip()

    # Basic validation
    if not emergency_type or not symptoms:
        return Response({
            'validation_status': 'FAILED',
            'validation_message': 'Tipo de emergencia y síntomas son requeridos',
            'errors': ['Información incompleta']
        }, status=status.HTTP_400_BAD_REQUEST)

    # AI validation
    ai_result = ai_validate_health(
        emergency_type=emergency_type,
        symptoms=symptoms,
        patient_age=patient_age,
        patient_gender=patient_gender,
        consciousness_level=consciousness_level,
        breathing_difficulty=breathing_difficulty,
        chest_pain=chest_pain,
        bleeding=bleeding,
        pre_existing_conditions=pre_existing_conditions,
        medications=medications,
        people_affected=people_affected
    )

    # Create validation record
    validation = HealthValidation.objects.create(
        user=request.user,
        emergency_type=emergency_type,
        symptoms=symptoms,
        patient_age=patient_age,
        patient_gender=patient_gender,
        consciousness_level=consciousness_level,
        breathing_difficulty=breathing_difficulty,
        chest_pain=chest_pain,
        bleeding=bleeding,
        pre_existing_conditions=pre_existing_conditions,
        medications=medications,
        people_affected=people_affected,
        validation_status=ai_result['status'],
        urgency_level=ai_result.get('urgency_level', 'MEDIUM'),
        validation_message=ai_result['message'],
        ai_confidence_score=ai_result['confidence'],
        ai_analysis=ai_result['analysis']
    )

    logger.info(
        f"Health validation created: {validation.id} - Status: {validation.validation_status} - "
        f"Urgency: {validation.urgency_level} - User: {request.user.email}"
    )

    # If CRITICAL, send immediate notification (can be extended with real notifications)
    if validation.urgency_level == 'CRITICAL':
        logger.critical(
            f"CRITICAL HEALTH EMERGENCY: {validation.id} - User: {request.user.email} - "
            f"Type: {emergency_type} - Symptoms: {symptoms}"
        )

    return Response({
        'id': validation.id,
        'validation_status': validation.validation_status,
        'urgency_level': validation.urgency_level,
        'validation_message': validation.validation_message,
        'confidence_score': ai_result['confidence'],
        'requires_review': validation.validation_status == 'PENDING_REVIEW',
        'health_info': {
            'emergency_type': emergency_type,
            'symptoms': symptoms,
            'patient_age': patient_age,
            'urgency_level': validation.urgency_level
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_health_validations(request):
    """
    Get all pending health validations (for MAWDY agents)
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Solo agentes MAWDY pueden acceder a esta información'},
            status=status.HTTP_403_FORBIDDEN
        )

    validations = HealthValidation.objects.filter(
        validation_status=HealthValidation.ValidationStatus.PENDING_REVIEW
    ).order_by('-urgency_level', '-created_at')  # Critical first

    data = [{
        'id': v.id,
        'user': v.user.email,
        'emergency_type': v.emergency_type,
        'symptoms': v.symptoms,
        'patient_age': v.patient_age,
        'patient_gender': v.patient_gender,
        'consciousness_level': v.consciousness_level,
        'urgency_level': v.urgency_level,
        'breathing_difficulty': v.breathing_difficulty,
        'chest_pain': v.chest_pain,
        'bleeding': v.bleeding,
        'ai_confidence': v.ai_confidence_score,
        'ai_analysis': v.ai_analysis,
        'created_at': v.created_at,
    } for v in validations]

    return Response({'validations': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_health_validation(request, validation_id):
    """
    Approve a health validation (MAWDY agents only)
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Solo agentes MAWDY pueden aprobar validaciones'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        validation = HealthValidation.objects.get(id=validation_id)
    except HealthValidation.DoesNotExist:
        return Response({'error': 'Validación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    notes = request.data.get('notes', '')
    urgency_override = request.data.get('urgency_level', validation.urgency_level)

    validation.validation_status = HealthValidation.ValidationStatus.APPROVED
    validation.urgency_level = urgency_override
    validation.reviewed_by = request.user
    validation.reviewed_at = timezone.now()
    validation.review_notes = notes
    validation.validation_message = 'Aprobado por agente MAWDY'
    validation.save()

    logger.info(f"Health validation {validation_id} approved by {request.user.email}")

    return Response({
        'success': True,
        'message': 'Validación aprobada exitosamente',
        'validation_id': validation_id,
        'urgency_level': urgency_override
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_health_validation(request, validation_id):
    """
    Reject a health validation (MAWDY agents only)
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Solo agentes MAWDY pueden rechazar validaciones'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        validation = HealthValidation.objects.get(id=validation_id)
    except HealthValidation.DoesNotExist:
        return Response({'error': 'Validación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    reason = request.data.get('reason', 'Información médica insuficiente o inválida')
    notes = request.data.get('notes', '')

    validation.validation_status = HealthValidation.ValidationStatus.REJECTED
    validation.reviewed_by = request.user
    validation.reviewed_at = timezone.now()
    validation.review_notes = notes
    validation.validation_message = reason
    validation.save()

    logger.info(f"Health validation {validation_id} rejected by {request.user.email}: {reason}")

    return Response({
        'success': True,
        'message': 'Validación rechazada',
        'validation_id': validation_id
    })
