"""
Unified Evidence Flow Service

Handles evidence submission with proper automation and fallback chain:

HEALTH ASSISTANCE:
1. Form-based submission (NO pictures)
2. Automated form validation
3. If automated fails -> MAWDY admin review

ROAD ASSISTANCE:
1. AI Vision analysis of photos (primary)
2. If AI fails -> Form-based submission
3. If form can't be processed -> MAWDY admin review
"""
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction

from .models import AssistanceRequest
from .documents import AssistanceDocument, REQUIRED_DOCUMENTS
from .ai_review import (
    EvidenceForm,
    ClaudeVisionReviewService,
    EvidenceFormReviewService,
)

logger = logging.getLogger(__name__)


class EvidenceFlowService:
    """
    Unified service for handling evidence submission with automation and fallback.
    """

    # Define which assistance types use which flow
    FLOW_CONFIG = {
        'HEALTH': {
            'allow_photos': False,  # Health uses form-only
            'primary': 'form',
            'fallback': 'admin_review',
            'form_type': 'HEALTH_INCIDENT',
        },
        'ROADSIDE': {
            'allow_photos': True,  # Roadside uses photos first
            'primary': 'ai_vision',
            'fallback': 'form',
            'final_fallback': 'admin_review',
            'form_type': 'ROADSIDE_ISSUE',
        },
        'VEHICLE_DAMAGE': {
            'allow_photos': True,
            'primary': 'ai_vision',
            'fallback': 'form',
            'final_fallback': 'admin_review',
            'form_type': 'VEHICLE_DAMAGE',
        },
    }

    @classmethod
    def get_flow_config(cls, assistance_type: str) -> Dict[str, Any]:
        """Get the flow configuration for an assistance type"""
        # Normalize the type
        if 'HEALTH' in assistance_type.upper():
            return cls.FLOW_CONFIG['HEALTH']
        elif 'MAWDY' in assistance_type.upper():
            return cls.FLOW_CONFIG['ROADSIDE']
        else:
            return cls.FLOW_CONFIG.get(
                assistance_type.upper(),
                cls.FLOW_CONFIG['ROADSIDE']
            )

    @classmethod
    def get_evidence_options(cls, request: AssistanceRequest) -> Dict[str, Any]:
        """
        Get available evidence submission options for a request.
        Returns what options are available based on assistance type.
        """
        # Determine assistance type from incident_type
        incident_type = request.incident_type or ''
        config = cls.get_flow_config(incident_type)

        options = {
            'request_id': request.id,
            'request_number': request.request_number,
            'assistance_type': incident_type,
            'evidence_options': []
        }

        if config['allow_photos']:
            options['evidence_options'].append({
                'type': 'photo',
                'name': 'Subir Fotos',
                'description': 'Suba fotos del vehiculo, dano y ubicacion',
                'primary': config['primary'] == 'ai_vision',
                'automated': True,
                'required_documents': REQUIRED_DOCUMENTS.get('ROADSIDE', [])
            })

        options['evidence_options'].append({
            'type': 'form',
            'name': 'Llenar Formulario',
            'description': 'Complete un formulario detallado',
            'primary': config['primary'] == 'form',
            'automated': True,
            'form_type': config['form_type']
        })

        options['fallback'] = {
            'type': 'admin_review',
            'name': 'Revision Manual',
            'description': 'Un agente de MAWDY revisara su solicitud',
            'when': 'Si la revision automatizada no es exitosa'
        }

        return options

    @classmethod
    def process_photo_evidence(cls, document: AssistanceDocument) -> Dict[str, Any]:
        """
        Process photo evidence with AI Vision.
        Returns result with status and whether fallback is needed.
        """
        # Check if photos are allowed for this type
        request = document.request
        config = cls.get_flow_config(request.incident_type or '')

        if not config['allow_photos']:
            return {
                'success': False,
                'error': 'Este tipo de asistencia no acepta fotos',
                'fallback': 'form',
                'form_type': config['form_type']
            }

        # Run AI Vision review
        result = ClaudeVisionReviewService.review_document(document)

        # Update document
        document.review_status = result['status']
        document.ai_confidence_score = result['confidence']
        document.ai_review_notes = result['notes']
        document.ai_detected_issues = result['issues']
        document.reviewed_at = timezone.now()
        document.save()

        # Check if AI review was successful
        if result['status'] == AssistanceDocument.ReviewStatus.APPROVED:
            return {
                'success': True,
                'status': 'approved',
                'message': 'Documento aprobado automaticamente',
                'confidence': result['confidence'],
                'next_step': None
            }
        elif result['status'] == AssistanceDocument.ReviewStatus.REJECTED:
            return {
                'success': False,
                'status': 'rejected',
                'message': 'Documento rechazado. Por favor use el formulario.',
                'issues': result['issues'],
                'fallback': 'form',
                'form_type': config['form_type']
            }
        else:  # NEEDS_RESUBMIT or other
            return {
                'success': False,
                'status': 'needs_review',
                'message': 'Documento requiere revision adicional',
                'issues': result['issues'],
                'fallback': 'form',
                'form_type': config['form_type']
            }

    @classmethod
    def process_form_evidence(cls, form: EvidenceForm) -> Dict[str, Any]:
        """
        Process form-based evidence with automated validation.
        Returns result with status and whether admin review is needed.
        """
        # Run automated validation
        analysis = EvidenceFormReviewService.analyze_form(form)

        # Update form with analysis
        form.ai_analysis = analysis
        form.ai_confidence_score = analysis['score'] / 100.0

        if analysis['score'] >= 80 and analysis['can_submit']:
            # High confidence - auto approve
            form.status = EvidenceForm.Status.APPROVED
            form.review_notes = 'Aprobado automaticamente por sistema'
            form.reviewed_at = timezone.now()
            form.save()

            return {
                'success': True,
                'status': 'approved',
                'message': 'Formulario aprobado automaticamente',
                'score': analysis['score'],
                'next_step': None
            }
        elif analysis['score'] >= 60:
            # Medium confidence - needs admin review
            form.status = EvidenceForm.Status.REVIEWING
            form.save()

            return {
                'success': True,
                'status': 'pending_review',
                'message': 'Formulario enviado para revision por agente MAWDY',
                'score': analysis['score'],
                'issues': analysis['issues'],
                'fallback': 'admin_review'
            }
        else:
            # Low confidence - request more info or admin review
            form.status = EvidenceForm.Status.NEEDS_INFO
            form.save()

            return {
                'success': False,
                'status': 'needs_info',
                'message': 'Se requiere mas informacion',
                'score': analysis['score'],
                'issues': analysis['issues'],
                'fallback': 'admin_review'
            }

    @classmethod
    def escalate_to_admin(cls, request: AssistanceRequest, reason: str) -> Dict[str, Any]:
        """
        Escalate the request to MAWDY admin for manual review.
        """
        # Update request status to indicate admin review needed
        request.status = 'PENDING_REVIEW'
        request.resolution_notes = f'Escalado a revision manual: {reason}'
        request.save()

        return {
            'success': True,
            'status': 'escalated',
            'message': 'Su solicitud ha sido escalada a un agente de MAWDY',
            'reason': reason,
            'estimated_wait': '15-30 minutos'
        }

    @classmethod
    def get_request_evidence_status(cls, request: AssistanceRequest) -> Dict[str, Any]:
        """
        Get the overall evidence status for a request.
        """
        # Get all documents
        documents = request.ai_documents.all()
        approved_docs = documents.filter(review_status='APPROVED').count()
        total_docs = documents.count()

        # Get all evidence forms
        forms = request.evidence_forms.all()
        approved_forms = forms.filter(status='APPROVED').count()
        total_forms = forms.count()

        # Determine overall status
        config = cls.get_flow_config(request.incident_type or '')

        if config['primary'] == 'form' or not config['allow_photos']:
            # Form-based flow
            if approved_forms > 0:
                status = 'complete'
                message = 'Evidencia aprobada'
            elif total_forms > 0:
                status = 'pending'
                message = 'Formulario en revision'
            else:
                status = 'missing'
                message = 'Por favor complete el formulario de evidencia'
        else:
            # Photo-based flow
            if approved_docs > 0:
                status = 'complete'
                message = 'Evidencia fotografica aprobada'
            elif approved_forms > 0:
                status = 'complete'
                message = 'Formulario de evidencia aprobado'
            elif total_docs > 0 or total_forms > 0:
                status = 'pending'
                message = 'Evidencia en revision'
            else:
                status = 'missing'
                message = 'Por favor suba fotos o complete el formulario'

        return {
            'request_id': request.id,
            'status': status,
            'message': message,
            'documents': {
                'total': total_docs,
                'approved': approved_docs
            },
            'forms': {
                'total': total_forms,
                'approved': approved_forms
            },
            'can_proceed': status == 'complete'
        }
