"""
AI Vision Document Review Service

Uses Claude Vision API for intelligent document analysis.
Also provides form-based evidence collection as alternative to photos.
"""
import base64
import logging
import httpx
from typing import Dict, Any, List, Optional
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .documents import AssistanceDocument, REQUIRED_DOCUMENTS

logger = logging.getLogger(__name__)

# Get Anthropic API key from settings
ANTHROPIC_API_KEY = getattr(settings, 'ANTHROPIC_API_KEY', None)


# =============================================================================
# Form-Based Evidence Model (Alternative to Photos)
# =============================================================================

class EvidenceForm(models.Model):
    """
    Form-based evidence submission when photos are not available.
    Captures detailed information about the incident/situation.
    """
    class FormType(models.TextChoices):
        VEHICLE_DAMAGE = 'VEHICLE_DAMAGE', _('Dano al Vehiculo')
        ROADSIDE_ISSUE = 'ROADSIDE_ISSUE', _('Problema en Carretera')
        HEALTH_INCIDENT = 'HEALTH_INCIDENT', _('Incidente de Salud')
        GENERAL = 'GENERAL', _('Formulario General')

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Borrador')
        SUBMITTED = 'SUBMITTED', _('Enviado')
        REVIEWING = 'REVIEWING', _('En Revision')
        APPROVED = 'APPROVED', _('Aprobado')
        REJECTED = 'REJECTED', _('Rechazado')
        NEEDS_INFO = 'NEEDS_INFO', _('Requiere Mas Informacion')

    request = models.ForeignKey(
        'assistance.AssistanceRequest',
        on_delete=models.CASCADE,
        related_name='evidence_forms'
    )

    form_type = models.CharField(
        max_length=30,
        choices=FormType.choices,
        default=FormType.GENERAL
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    # Common fields for all form types
    incident_date = models.DateTimeField(_('fecha del incidente'))
    incident_description = models.TextField(_('descripcion del incidente'))
    location_description = models.TextField(_('descripcion de la ubicacion'))

    # Vehicle-specific fields
    vehicle_make = models.CharField(_('marca del vehiculo'), max_length=100, blank=True)
    vehicle_model = models.CharField(_('modelo del vehiculo'), max_length=100, blank=True)
    vehicle_year = models.IntegerField(_('ano del vehiculo'), null=True, blank=True)
    vehicle_color = models.CharField(_('color del vehiculo'), max_length=50, blank=True)
    vehicle_plate = models.CharField(_('placa del vehiculo'), max_length=20, blank=True)
    damage_description = models.TextField(_('descripcion del dano'), blank=True)
    damage_location = models.CharField(
        _('ubicacion del dano'),
        max_length=100,
        blank=True,
        help_text='ej: frente, trasero, lado izquierdo'
    )

    # Health-specific fields
    symptoms_description = models.TextField(_('descripcion de sintomas'), blank=True)
    medical_history = models.TextField(_('historial medico relevante'), blank=True)
    current_medications = models.TextField(_('medicamentos actuales'), blank=True)
    allergies = models.TextField(_('alergias conocidas'), blank=True)

    # Roadside-specific fields
    issue_type = models.CharField(
        _('tipo de problema'),
        max_length=100,
        blank=True,
        help_text='ej: llanta ponchada, sin combustible, bateria'
    )
    attempted_solutions = models.TextField(_('soluciones intentadas'), blank=True)

    # Witness information (optional)
    witness_name = models.CharField(_('nombre del testigo'), max_length=200, blank=True)
    witness_phone = models.CharField(_('telefono del testigo'), max_length=20, blank=True)

    # Declaration
    declaration_accepted = models.BooleanField(
        _('declaracion aceptada'),
        default=False,
        help_text='Declaro que la informacion proporcionada es veridica'
    )
    declaration_timestamp = models.DateTimeField(null=True, blank=True)

    # Review fields
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_evidence_forms'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(_('notas de revision'), blank=True)
    rejection_reason = models.TextField(_('razon de rechazo'), blank=True)

    # AI Analysis
    ai_analysis = models.JSONField(_('analisis de IA'), default=dict, blank=True)
    ai_confidence_score = models.FloatField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'assistance'
        verbose_name = _('formulario de evidencia')
        verbose_name_plural = _('formularios de evidencia')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_form_type_display()} - {self.request.request_number}'

    def submit(self):
        """Submit the form for review"""
        if not self.declaration_accepted:
            raise ValueError('Debe aceptar la declaracion antes de enviar')

        self.status = self.Status.SUBMITTED
        self.submitted_at = timezone.now()
        self.declaration_timestamp = timezone.now()
        self.save()

    def approve(self, reviewer):
        """Approve the evidence form"""
        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, reviewer, reason):
        """Reject the evidence form"""
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()


# =============================================================================
# Claude Vision AI Review Service
# =============================================================================

class ClaudeVisionReviewService:
    """
    AI-powered document review using Claude Vision API.
    Analyzes uploaded images for document verification.
    """

    # Prompts for different document types
    REVIEW_PROMPTS = {
        'PHOTO_VEHICLE': """Analyze this vehicle photo and verify:
1. Is a vehicle clearly visible in the image?
2. Is the image quality good enough (not blurry, well-lit)?
3. Can the vehicle type/model be identified?
4. Are there any visible issues or damage?

Respond in JSON format:
{
    "vehicle_visible": true/false,
    "image_quality": "good/fair/poor",
    "vehicle_type": "car/truck/motorcycle/unknown",
    "damage_visible": true/false,
    "damage_description": "description if visible",
    "confidence": 0.0-1.0,
    "issues": ["list of any issues"],
    "recommendation": "APPROVE/REJECT/NEEDS_RESUBMIT"
}""",

        'PHOTO_DAMAGE': """Analyze this damage photo and verify:
1. Is damage clearly visible in the image?
2. What type of damage is shown (dent, scratch, broken, etc.)?
3. Is the photo clear enough to assess the damage?
4. Does the damage appear recent?

Respond in JSON format:
{
    "damage_visible": true/false,
    "damage_type": "description of damage type",
    "severity": "minor/moderate/severe",
    "appears_recent": true/false,
    "image_quality": "good/fair/poor",
    "confidence": 0.0-1.0,
    "issues": ["list of any issues"],
    "recommendation": "APPROVE/REJECT/NEEDS_RESUBMIT"
}""",

        'LICENSE_PLATE': """Analyze this license plate photo and verify:
1. Is a license plate visible?
2. Is the plate number readable?
3. What is the plate number (if readable)?
4. Is this a valid Guatemala plate format?

Respond in JSON format:
{
    "plate_visible": true/false,
    "plate_readable": true/false,
    "plate_number": "plate number if readable or null",
    "valid_format": true/false,
    "country": "Guatemala/other",
    "confidence": 0.0-1.0,
    "issues": ["list of any issues"],
    "recommendation": "APPROVE/REJECT/NEEDS_RESUBMIT"
}""",

        'DRIVER_LICENSE': """Analyze this driver's license and verify:
1. Is this a valid driver's license document?
2. Is the photo on the license visible?
3. Is the name readable?
4. Is there an expiration date visible?
5. Does it appear valid (not expired)?

Respond in JSON format:
{
    "is_valid_license": true/false,
    "photo_visible": true/false,
    "name_readable": true/false,
    "expiration_visible": true/false,
    "appears_valid": true/false,
    "confidence": 0.0-1.0,
    "issues": ["list of any issues"],
    "recommendation": "APPROVE/REJECT/NEEDS_RESUBMIT"
}""",

        'INSURANCE_CARD': """Analyze this insurance card and verify:
1. Is this a valid insurance document?
2. Is the policy holder name visible?
3. Is there a policy number visible?
4. Is coverage information visible?
5. Does it appear current (not expired)?

Respond in JSON format:
{
    "is_valid_insurance": true/false,
    "holder_name_visible": true/false,
    "policy_number_visible": true/false,
    "coverage_visible": true/false,
    "appears_current": true/false,
    "confidence": 0.0-1.0,
    "issues": ["list of any issues"],
    "recommendation": "APPROVE/REJECT/NEEDS_RESUBMIT"
}""",

        'DEFAULT': """Analyze this document and verify:
1. Is the document clearly visible?
2. Is the image quality adequate?
3. Can any relevant information be extracted?

Respond in JSON format:
{
    "document_visible": true/false,
    "image_quality": "good/fair/poor",
    "information_extractable": true/false,
    "confidence": 0.0-1.0,
    "issues": ["list of any issues"],
    "recommendation": "APPROVE/REJECT/NEEDS_RESUBMIT"
}"""
    }

    @classmethod
    def _encode_image(cls, file_path: str) -> str:
        """Encode image file to base64"""
        with open(file_path, 'rb') as f:
            return base64.standard_b64encode(f.read()).decode('utf-8')

    @classmethod
    def _get_media_type(cls, filename: str) -> str:
        """Get media type from filename"""
        ext = filename.lower().split('.')[-1]
        media_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
        }
        return media_types.get(ext, 'image/jpeg')

    @classmethod
    async def review_document_async(cls, document: AssistanceDocument) -> Dict[str, Any]:
        """
        Perform AI vision review of document using Claude API.
        """
        if not ANTHROPIC_API_KEY:
            logger.warning('ANTHROPIC_API_KEY not configured, using basic review')
            return cls._basic_review(document)

        try:
            # Get the prompt for this document type
            prompt = cls.REVIEW_PROMPTS.get(
                document.document_type,
                cls.REVIEW_PROMPTS['DEFAULT']
            )

            # Encode the image
            image_data = cls._encode_image(document.file.path)
            media_type = cls._get_media_type(document.original_filename)

            # Call Claude Vision API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': ANTHROPIC_API_KEY,
                        'anthropic-version': '2023-06-01',
                        'content-type': 'application/json',
                    },
                    json={
                        'model': 'claude-sonnet-4-20250514',
                        'max_tokens': 1024,
                        'messages': [
                            {
                                'role': 'user',
                                'content': [
                                    {
                                        'type': 'image',
                                        'source': {
                                            'type': 'base64',
                                            'media_type': media_type,
                                            'data': image_data,
                                        }
                                    },
                                    {
                                        'type': 'text',
                                        'text': prompt
                                    }
                                ]
                            }
                        ]
                    },
                    timeout=30.0
                )

            if response.status_code == 200:
                result = response.json()
                content = result.get('content', [{}])[0].get('text', '{}')

                # Parse JSON response from Claude
                import json
                try:
                    analysis = json.loads(content)
                except json.JSONDecodeError:
                    analysis = {'raw_response': content}

                return cls._process_ai_response(document, analysis)
            else:
                logger.error(f'Claude API error: {response.status_code} - {response.text}')
                return cls._basic_review(document)

        except Exception as e:
            logger.error(f'AI review error: {e}')
            return cls._basic_review(document)

    @classmethod
    def review_document(cls, document: AssistanceDocument) -> Dict[str, Any]:
        """
        Synchronous version of review_document.
        Uses basic review if async is not available.
        """
        if not ANTHROPIC_API_KEY:
            return cls._basic_review(document)

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(cls.review_document_async(document))
        except RuntimeError:
            # No event loop, use basic review
            return cls._basic_review(document)

    @classmethod
    def _process_ai_response(cls, document: AssistanceDocument, analysis: Dict) -> Dict[str, Any]:
        """Process Claude's analysis response"""
        confidence = analysis.get('confidence', 0.7)
        issues = analysis.get('issues', [])
        recommendation = analysis.get('recommendation', 'NEEDS_RESUBMIT')

        # Map recommendation to status
        status_map = {
            'APPROVE': AssistanceDocument.ReviewStatus.APPROVED,
            'REJECT': AssistanceDocument.ReviewStatus.REJECTED,
            'NEEDS_RESUBMIT': AssistanceDocument.ReviewStatus.NEEDS_RESUBMIT,
        }
        status = status_map.get(recommendation, AssistanceDocument.ReviewStatus.NEEDS_RESUBMIT)

        # Generate notes
        notes = cls._generate_ai_notes(document, analysis)

        return {
            'status': status,
            'confidence': confidence,
            'issues': [{'code': 'AI_DETECTED', 'message': issue, 'severity': 'warning'} for issue in issues],
            'notes': notes,
            'ai_analysis': analysis
        }

    @classmethod
    def _generate_ai_notes(cls, document: AssistanceDocument, analysis: Dict) -> str:
        """Generate human-readable notes from AI analysis"""
        doc_type = document.get_document_type_display()
        recommendation = analysis.get('recommendation', 'PENDIENTE')
        confidence = analysis.get('confidence', 0)

        notes = f"Analisis IA de {doc_type}:\n"
        notes += f"- Recomendacion: {recommendation}\n"
        notes += f"- Confianza: {confidence * 100:.0f}%\n"

        issues = analysis.get('issues', [])
        if issues:
            notes += "- Problemas detectados:\n"
            for issue in issues:
                notes += f"  * {issue}\n"

        return notes

    @classmethod
    def _basic_review(cls, document: AssistanceDocument) -> Dict[str, Any]:
        """
        Basic review without AI (fallback).
        Validates file format and size only.
        """
        from .documents import DocumentReviewService
        return DocumentReviewService.review_document(document)


# =============================================================================
# Evidence Form Review Service
# =============================================================================

class EvidenceFormReviewService:
    """
    Review service for form-based evidence submissions.
    Uses AI to analyze the narrative for consistency and completeness.

    BUSINESS RULES:
    - HEALTH: Form-only (no photos) → AI validation → MAWDY admin fallback
    - ROAD: AI photos first → Form fallback → MAWDY admin fallback
    - If AI form analysis fails or info is wrong → escalate to MAWDY admin
    """

    # AI prompts for form content analysis
    FORM_ANALYSIS_PROMPTS = {
        'VEHICLE_DAMAGE': """Analyze this vehicle damage report for consistency and completeness:

Vehicle Information:
- Make: {vehicle_make}
- Model: {vehicle_model}
- Year: {vehicle_year}
- Color: {vehicle_color}
- Plate: {vehicle_plate}

Damage Details:
- Location on vehicle: {damage_location}
- Description: {damage_description}

Incident Details:
- Date: {incident_date}
- Description: {incident_description}
- Location: {location_description}

Evaluate:
1. Is the information consistent (no contradictions)?
2. Is the description detailed enough to process a claim?
3. Does the damage description match the incident description?
4. Are there any red flags or suspicious inconsistencies?

Respond in JSON:
{{
    "is_consistent": true/false,
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "issues": ["list of issues found"],
    "recommendation": "APPROVE/ESCALATE_TO_ADMIN/NEEDS_INFO",
    "reason": "explanation"
}}""",

        'ROADSIDE_ISSUE': """Analyze this roadside assistance request for validity:

Problem Type: {issue_type}
Attempted Solutions: {attempted_solutions}

Vehicle:
- Make: {vehicle_make}
- Model: {vehicle_model}
- Plate: {vehicle_plate}

Location: {location_description}
Additional Info: {incident_description}

Evaluate:
1. Is the problem type valid for roadside assistance?
2. Is the location description specific enough for dispatch?
3. Does the information make sense together?
4. Are there any inconsistencies?

Respond in JSON:
{{
    "is_valid_request": true/false,
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "issues": ["list of issues found"],
    "recommendation": "APPROVE/ESCALATE_TO_ADMIN/NEEDS_INFO",
    "reason": "explanation"
}}""",

        'HEALTH_INCIDENT': """Analyze this health assistance request for completeness:

Symptoms: {symptoms_description}
Onset: {incident_date}

Medical History: {medical_history}
Current Medications: {current_medications}
Allergies: {allergies}

Location: {location_description}
Additional Info: {incident_description}

Evaluate:
1. Are the symptoms described clearly enough for triage?
2. Is the location clear for ambulance dispatch?
3. Is critical medical info (allergies, conditions) provided?
4. Does the request appear urgent?

Respond in JSON:
{{
    "is_valid_request": true/false,
    "is_complete": true/false,
    "urgency": "low/medium/high/critical",
    "confidence": 0.0-1.0,
    "issues": ["list of issues found"],
    "recommendation": "APPROVE/ESCALATE_TO_ADMIN/NEEDS_INFO",
    "reason": "explanation"
}}"""
    }

    @classmethod
    async def ai_analyze_form_async(cls, form: EvidenceForm) -> Dict[str, Any]:
        """
        Use Claude AI to analyze form content for validity and consistency.
        If AI cannot process or confidence is low, escalates to MAWDY admin.
        """
        if not ANTHROPIC_API_KEY:
            logger.warning('ANTHROPIC_API_KEY not configured, using basic analysis')
            return cls._basic_form_analysis(form)

        try:
            # Get the appropriate prompt
            prompt_template = cls.FORM_ANALYSIS_PROMPTS.get(
                form.form_type,
                cls.FORM_ANALYSIS_PROMPTS['ROADSIDE_ISSUE']
            )

            # Fill in form data
            prompt = prompt_template.format(
                vehicle_make=form.vehicle_make or 'N/A',
                vehicle_model=form.vehicle_model or 'N/A',
                vehicle_year=form.vehicle_year or 'N/A',
                vehicle_color=form.vehicle_color or 'N/A',
                vehicle_plate=form.vehicle_plate or 'N/A',
                damage_location=form.damage_location or 'N/A',
                damage_description=form.damage_description or 'N/A',
                incident_date=str(form.incident_date) if form.incident_date else 'N/A',
                incident_description=form.incident_description or 'N/A',
                location_description=form.location_description or 'N/A',
                issue_type=form.issue_type or 'N/A',
                attempted_solutions=form.attempted_solutions or 'N/A',
                symptoms_description=form.symptoms_description or 'N/A',
                medical_history=form.medical_history or 'N/A',
                current_medications=form.current_medications or 'N/A',
                allergies=form.allergies or 'N/A',
            )

            # Call Claude API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': ANTHROPIC_API_KEY,
                        'anthropic-version': '2023-06-01',
                        'content-type': 'application/json',
                    },
                    json={
                        'model': 'claude-sonnet-4-20250514',
                        'max_tokens': 1024,
                        'messages': [
                            {
                                'role': 'user',
                                'content': prompt
                            }
                        ]
                    },
                    timeout=30.0
                )

            if response.status_code == 200:
                result = response.json()
                content = result.get('content', [{}])[0].get('text', '{}')

                import json
                try:
                    analysis = json.loads(content)
                except json.JSONDecodeError:
                    # AI returned non-JSON, escalate to admin
                    return cls._escalate_to_admin(form, "AI analysis returned invalid format")

                return cls._process_form_analysis(form, analysis)
            else:
                logger.error(f'Claude API error: {response.status_code}')
                return cls._escalate_to_admin(form, "AI service temporarily unavailable")

        except Exception as e:
            logger.error(f'AI form analysis error: {e}')
            return cls._escalate_to_admin(form, f"AI analysis error: {str(e)}")

    @classmethod
    def ai_analyze_form(cls, form: EvidenceForm) -> Dict[str, Any]:
        """Synchronous version of AI form analysis."""
        if not ANTHROPIC_API_KEY:
            return cls._basic_form_analysis(form)

        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # Already in async context, can't use run_until_complete
                return cls._basic_form_analysis(form)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(cls.ai_analyze_form_async(form))
                finally:
                    loop.close()
        except Exception as e:
            logger.error(f'Sync AI analysis error: {e}')
            return cls._escalate_to_admin(form, str(e))

    @classmethod
    def _process_form_analysis(cls, form: EvidenceForm, analysis: Dict) -> Dict[str, Any]:
        """Process AI analysis result and determine next action."""
        confidence = analysis.get('confidence', 0.5)
        recommendation = analysis.get('recommendation', 'ESCALATE_TO_ADMIN')
        issues = analysis.get('issues', [])

        # Low confidence = escalate to MAWDY admin
        if confidence < 0.7:
            return cls._escalate_to_admin(
                form,
                f"AI confidence too low ({confidence:.0%}). Issues: {', '.join(issues)}"
            )

        # Map recommendation to result
        if recommendation == 'APPROVE':
            return {
                'status': 'approved',
                'action': 'auto_approve',
                'confidence': confidence,
                'message': 'Formulario aprobado automaticamente',
                'issues': issues,
                'ai_analysis': analysis,
                'needs_admin_review': False
            }
        elif recommendation == 'NEEDS_INFO':
            return {
                'status': 'needs_info',
                'action': 'request_more_info',
                'confidence': confidence,
                'message': 'Se requiere informacion adicional',
                'issues': issues,
                'ai_analysis': analysis,
                'needs_admin_review': False,
                'missing_info': analysis.get('reason', 'Informacion incompleta')
            }
        else:  # ESCALATE_TO_ADMIN or unknown
            return cls._escalate_to_admin(form, analysis.get('reason', 'Requiere revision manual'))

    @classmethod
    def _escalate_to_admin(cls, form: EvidenceForm, reason: str) -> Dict[str, Any]:
        """Escalate form to MAWDY admin for manual review."""
        return {
            'status': 'pending_admin_review',
            'action': 'escalate_to_mawdy_admin',
            'confidence': 0,
            'message': 'Formulario enviado para revision por agente MAWDY',
            'issues': [{'severity': 'info', 'message': reason}],
            'needs_admin_review': True,
            'escalation_reason': reason
        }

    @classmethod
    def _basic_form_analysis(cls, form: EvidenceForm) -> Dict[str, Any]:
        """Basic form analysis without AI - always escalates to admin."""
        basic_result = cls.analyze_form(form)

        # If basic validation passes, still escalate for human review when no AI
        if basic_result['score'] >= 80 and basic_result['can_submit']:
            return {
                'status': 'pending_admin_review',
                'action': 'escalate_to_mawdy_admin',
                'confidence': 0,
                'message': 'Formulario enviado para revision (AI no disponible)',
                'issues': basic_result['issues'],
                'needs_admin_review': True,
                'escalation_reason': 'AI service not configured'
            }
        else:
            return {
                'status': 'needs_info',
                'action': 'request_more_info',
                'confidence': 0,
                'message': 'Se requiere corregir la informacion',
                'issues': basic_result['issues'],
                'needs_admin_review': False,
                'score': basic_result['score']
            }

    @classmethod
    def analyze_form(cls, form: EvidenceForm) -> Dict[str, Any]:
        """
        Analyze evidence form for completeness and consistency.
        """
        issues = []
        score = 100

        # Check required fields based on form type
        # Fields with min_length requirement (description fields need detail)
        long_text_fields = []
        short_text_fields = []  # Fields that just need to be non-empty

        if form.form_type == EvidenceForm.FormType.VEHICLE_DAMAGE:
            short_text_fields = [
                ('vehicle_make', 'Marca del vehiculo'),
                ('vehicle_model', 'Modelo del vehiculo'),
                ('vehicle_plate', 'Placa del vehiculo'),
            ]
            long_text_fields = [
                ('damage_description', 'Descripcion del dano'),
            ]
        elif form.form_type == EvidenceForm.FormType.HEALTH_INCIDENT:
            long_text_fields = [
                ('symptoms_description', 'Descripcion de sintomas'),
            ]
        elif form.form_type == EvidenceForm.FormType.ROADSIDE_ISSUE:
            short_text_fields = [
                ('issue_type', 'Tipo de problema'),
            ]

        # Common required fields (long text)
        long_text_fields.extend([
            ('incident_description', 'Descripcion del incidente'),
            ('location_description', 'Descripcion de ubicacion'),
        ])

        # Check short text fields (just need to be non-empty)
        for field, label in short_text_fields:
            value = getattr(form, field, '')
            if not value or len(str(value).strip()) < 2:
                issues.append({
                    'field': field,
                    'message': f'{label} es requerido',
                    'severity': 'error'
                })
                score -= 15

        # Check long text fields (need at least 10 characters)
        for field, label in long_text_fields:
            value = getattr(form, field, '')
            if not value or len(str(value).strip()) < 10:
                issues.append({
                    'field': field,
                    'message': f'{label} es requerido y debe tener al menos 10 caracteres',
                    'severity': 'error'
                })
                score -= 15

        # Check description length
        if len(form.incident_description) < 50:
            issues.append({
                'field': 'incident_description',
                'message': 'La descripcion del incidente debe ser mas detallada (minimo 50 caracteres)',
                'severity': 'warning'
            })
            score -= 10

        # Note: Declaration is checked during submission, not validation
        # This allows users to save drafts without accepting yet

        # Determine status
        has_errors = any(i['severity'] == 'error' for i in issues)
        if has_errors or score < 60:
            status = EvidenceForm.Status.NEEDS_INFO
        elif score >= 80:
            status = EvidenceForm.Status.REVIEWING
        else:
            status = EvidenceForm.Status.REVIEWING

        return {
            'score': max(0, score),
            'status': status,
            'issues': issues,
            'can_submit': not has_errors,
        }

    @classmethod
    def get_form_template(cls, form_type: str) -> Dict[str, Any]:
        """Get the form template/schema for a form type"""
        templates = {
            'VEHICLE_DAMAGE': {
                'title': 'Formulario de Dano al Vehiculo',
                'description': 'Complete este formulario si no puede proporcionar fotos del dano',
                'sections': [
                    {
                        'name': 'Informacion del Vehiculo',
                        'fields': [
                            {'name': 'vehicle_make', 'label': 'Marca', 'type': 'text', 'required': True},
                            {'name': 'vehicle_model', 'label': 'Modelo', 'type': 'text', 'required': True},
                            {'name': 'vehicle_year', 'label': 'Ano', 'type': 'number', 'required': False},
                            {'name': 'vehicle_color', 'label': 'Color', 'type': 'text', 'required': False},
                            {'name': 'vehicle_plate', 'label': 'Placa', 'type': 'text', 'required': True},
                        ]
                    },
                    {
                        'name': 'Descripcion del Dano',
                        'fields': [
                            {'name': 'damage_location', 'label': 'Ubicacion del dano en el vehiculo', 'type': 'select',
                             'options': ['Frente', 'Trasero', 'Lado izquierdo', 'Lado derecho', 'Techo', 'Interior']},
                            {'name': 'damage_description', 'label': 'Descripcion detallada del dano', 'type': 'textarea', 'required': True},
                        ]
                    },
                    {
                        'name': 'Detalles del Incidente',
                        'fields': [
                            {'name': 'incident_date', 'label': 'Fecha y hora del incidente', 'type': 'datetime', 'required': True},
                            {'name': 'incident_description', 'label': 'Que paso?', 'type': 'textarea', 'required': True},
                            {'name': 'location_description', 'label': 'Donde ocurrio?', 'type': 'textarea', 'required': True},
                        ]
                    }
                ]
            },
            'ROADSIDE_ISSUE': {
                'title': 'Formulario de Problema en Carretera',
                'description': 'Complete este formulario para reportar su problema',
                'sections': [
                    {
                        'name': 'Tipo de Problema',
                        'fields': [
                            {'name': 'issue_type', 'label': 'Tipo de problema', 'type': 'select', 'required': True,
                             'options': ['Llanta ponchada', 'Sin combustible', 'Bateria descargada', 'Llaves encerradas', 'Motor no enciende', 'Otro']},
                            {'name': 'attempted_solutions', 'label': 'Que ha intentado?', 'type': 'textarea', 'required': False},
                        ]
                    },
                    {
                        'name': 'Informacion del Vehiculo',
                        'fields': [
                            {'name': 'vehicle_make', 'label': 'Marca', 'type': 'text', 'required': True},
                            {'name': 'vehicle_model', 'label': 'Modelo', 'type': 'text', 'required': True},
                            {'name': 'vehicle_plate', 'label': 'Placa', 'type': 'text', 'required': True},
                        ]
                    },
                    {
                        'name': 'Ubicacion',
                        'fields': [
                            {'name': 'location_description', 'label': 'Donde esta usted? (sea lo mas especifico posible)', 'type': 'textarea', 'required': True},
                            {'name': 'incident_description', 'label': 'Descripcion adicional', 'type': 'textarea', 'required': True},
                        ]
                    }
                ]
            },
            'HEALTH_INCIDENT': {
                'title': 'Formulario de Incidente de Salud',
                'description': 'Complete este formulario para solicitar asistencia medica',
                'sections': [
                    {
                        'name': 'Sintomas Actuales',
                        'fields': [
                            {'name': 'symptoms_description', 'label': 'Describa sus sintomas', 'type': 'textarea', 'required': True},
                            {'name': 'incident_date', 'label': 'Cuando comenzaron los sintomas?', 'type': 'datetime', 'required': True},
                        ]
                    },
                    {
                        'name': 'Historial Medico',
                        'fields': [
                            {'name': 'medical_history', 'label': 'Condiciones medicas previas', 'type': 'textarea', 'required': False},
                            {'name': 'current_medications', 'label': 'Medicamentos actuales', 'type': 'textarea', 'required': False},
                            {'name': 'allergies', 'label': 'Alergias conocidas', 'type': 'textarea', 'required': False},
                        ]
                    },
                    {
                        'name': 'Ubicacion',
                        'fields': [
                            {'name': 'location_description', 'label': 'Donde se encuentra?', 'type': 'textarea', 'required': True},
                            {'name': 'incident_description', 'label': 'Informacion adicional', 'type': 'textarea', 'required': True},
                        ]
                    }
                ]
            }
        }

        return templates.get(form_type, templates.get('ROADSIDE_ISSUE'))
