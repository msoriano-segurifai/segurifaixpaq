"""
Document Upload and AI Review for Assistance Requests
Automated document verification based on assistance type requirements
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import os
import uuid


class AssistanceDocument(models.Model):
    """Documents uploaded for assistance requests"""

    class DocumentType(models.TextChoices):
        PHOTO_VEHICLE = 'PHOTO_VEHICLE', _('Foto del Vehiculo')
        PHOTO_DAMAGE = 'PHOTO_DAMAGE', _('Foto del Dano')
        PHOTO_LOCATION = 'PHOTO_LOCATION', _('Foto de Ubicacion')
        LICENSE_PLATE = 'LICENSE_PLATE', _('Placa del Vehiculo')
        DRIVER_LICENSE = 'DRIVER_LICENSE', _('Licencia de Conducir')
        INSURANCE_CARD = 'INSURANCE_CARD', _('Tarjeta de Seguro')
        MEDICAL_PRESCRIPTION = 'MEDICAL_PRESCRIPTION', _('Receta Medica')
        MEDICAL_REPORT = 'MEDICAL_REPORT', _('Informe Medico')
        CREDIT_CARD_STATEMENT = 'CREDIT_CARD_STATEMENT', _('Estado de Cuenta')
        POLICE_REPORT = 'POLICE_REPORT', _('Reporte Policial')
        OTHER = 'OTHER', _('Otro')

    class ReviewStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pendiente de Revision')
        REVIEWING = 'REVIEWING', _('En Revision')
        APPROVED = 'APPROVED', _('Aprobado')
        REJECTED = 'REJECTED', _('Rechazado')
        NEEDS_RESUBMIT = 'NEEDS_RESUBMIT', _('Requiere Reenvio')

    def document_upload_path(instance, filename):
        ext = filename.split('.')[-1]
        new_filename = f'{uuid.uuid4().hex}.{ext}'
        return f'assistance_docs/{instance.request.id}/{new_filename}'

    request = models.ForeignKey(
        'assistance.AssistanceRequest',
        on_delete=models.CASCADE,
        related_name='ai_documents',
        verbose_name=_('solicitud')
    )
    document_type = models.CharField(
        _('tipo de documento'),
        max_length=30,
        choices=DocumentType.choices
    )
    file = models.FileField(
        _('archivo'),
        upload_to=document_upload_path
    )
    original_filename = models.CharField(_('nombre original'), max_length=255)
    file_size = models.PositiveIntegerField(_('tamano en bytes'), default=0)
    mime_type = models.CharField(_('tipo MIME'), max_length=100, blank=True)

    # AI Review fields
    review_status = models.CharField(
        _('estado de revision'),
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING
    )
    ai_confidence_score = models.FloatField(
        _('puntuacion de confianza IA'),
        null=True,
        blank=True,
        help_text='0.0 - 1.0'
    )
    ai_review_notes = models.TextField(_('notas de revision IA'), blank=True)
    ai_detected_issues = models.JSONField(
        _('problemas detectados'),
        default=list,
        blank=True
    )
    reviewed_at = models.DateTimeField(_('revisado en'), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_documents',
        verbose_name=_('revisado por')
    )

    # Timestamps
    uploaded_at = models.DateTimeField(_('subido en'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado en'), auto_now=True)

    class Meta:
        verbose_name = _('documento de asistencia')
        verbose_name_plural = _('documentos de asistencia')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.get_document_type_display()} - {self.request.request_number}'


# Required documents by assistance type
REQUIRED_DOCUMENTS = {
    'ROADSIDE': [
        {'type': 'PHOTO_VEHICLE', 'required': True, 'description': 'Foto clara del vehiculo'},
        {'type': 'PHOTO_DAMAGE', 'required': True, 'description': 'Foto del dano o problema'},
        {'type': 'PHOTO_LOCATION', 'required': False, 'description': 'Foto de la ubicacion'},
        {'type': 'LICENSE_PLATE', 'required': True, 'description': 'Foto de la placa visible'},
        {'type': 'DRIVER_LICENSE', 'required': False, 'description': 'Licencia de conducir'},
    ],
    'HEALTH': [
        {'type': 'MEDICAL_PRESCRIPTION', 'required': False, 'description': 'Receta medica si aplica'},
        {'type': 'MEDICAL_REPORT', 'required': False, 'description': 'Informe medico previo'},
        {'type': 'INSURANCE_CARD', 'required': True, 'description': 'Tarjeta de seguro medico'},
    ],
    'CARD_INSURANCE': [
        {'type': 'CREDIT_CARD_STATEMENT', 'required': True, 'description': 'Estado de cuenta reciente'},
        {'type': 'POLICE_REPORT', 'required': False, 'description': 'Denuncia policial si aplica'},
    ]
}


class DocumentReviewService:
    """AI-powered document review service"""

    # Validation rules by document type
    VALIDATION_RULES = {
        'PHOTO_VEHICLE': {
            'min_resolution': (640, 480),
            'allowed_formats': ['jpg', 'jpeg', 'png', 'webp'],
            'max_size_mb': 10,
            'checks': ['is_vehicle_visible', 'is_clear', 'has_good_lighting']
        },
        'PHOTO_DAMAGE': {
            'min_resolution': (640, 480),
            'allowed_formats': ['jpg', 'jpeg', 'png', 'webp'],
            'max_size_mb': 10,
            'checks': ['shows_damage', 'is_clear', 'is_recent']
        },
        'LICENSE_PLATE': {
            'min_resolution': (320, 240),
            'allowed_formats': ['jpg', 'jpeg', 'png'],
            'max_size_mb': 5,
            'checks': ['plate_readable', 'matches_vehicle_info']
        },
        'DRIVER_LICENSE': {
            'min_resolution': (640, 480),
            'allowed_formats': ['jpg', 'jpeg', 'png', 'pdf'],
            'max_size_mb': 5,
            'checks': ['is_valid_license', 'not_expired', 'photo_visible']
        },
        'INSURANCE_CARD': {
            'min_resolution': (640, 480),
            'allowed_formats': ['jpg', 'jpeg', 'png', 'pdf'],
            'max_size_mb': 5,
            'checks': ['is_valid_insurance', 'not_expired', 'covers_service']
        },
        'MEDICAL_PRESCRIPTION': {
            'allowed_formats': ['jpg', 'jpeg', 'png', 'pdf'],
            'max_size_mb': 5,
            'checks': ['has_doctor_signature', 'is_legible', 'is_recent']
        },
        'CREDIT_CARD_STATEMENT': {
            'allowed_formats': ['jpg', 'jpeg', 'png', 'pdf'],
            'max_size_mb': 10,
            'checks': ['is_recent', 'shows_account_info']
        },
        'POLICE_REPORT': {
            'allowed_formats': ['jpg', 'jpeg', 'png', 'pdf'],
            'max_size_mb': 10,
            'checks': ['is_official', 'has_case_number', 'is_signed']
        }
    }

    @classmethod
    def review_document(cls, document: AssistanceDocument) -> dict:
        """
        Perform automated review of uploaded document
        Returns review result with confidence score and issues
        """
        issues = []
        confidence = 1.0
        rules = cls.VALIDATION_RULES.get(document.document_type, {})

        # Check file format
        ext = document.original_filename.split('.')[-1].lower()
        allowed = rules.get('allowed_formats', ['jpg', 'jpeg', 'png', 'pdf'])
        if ext not in allowed:
            issues.append({
                'code': 'INVALID_FORMAT',
                'message': f'Formato no permitido. Use: {", ".join(allowed)}',
                'severity': 'error'
            })
            confidence -= 0.5

        # Check file size
        max_size = rules.get('max_size_mb', 10) * 1024 * 1024
        if document.file_size > max_size:
            issues.append({
                'code': 'FILE_TOO_LARGE',
                'message': f'Archivo muy grande. Maximo: {rules.get("max_size_mb", 10)}MB',
                'severity': 'error'
            })
            confidence -= 0.3

        # Simulate AI checks (in production, integrate with vision API)
        checks = rules.get('checks', [])
        for check in checks:
            # Placeholder for actual AI vision analysis
            # In production: call Claude Vision, AWS Rekognition, etc.
            pass

        # Determine review status
        if confidence >= 0.8 and not any(i['severity'] == 'error' for i in issues):
            status = AssistanceDocument.ReviewStatus.APPROVED
        elif confidence >= 0.5:
            status = AssistanceDocument.ReviewStatus.NEEDS_RESUBMIT
        else:
            status = AssistanceDocument.ReviewStatus.REJECTED

        return {
            'status': status,
            'confidence': max(0, confidence),
            'issues': issues,
            'notes': cls._generate_review_notes(document, issues, confidence)
        }

    @classmethod
    def _generate_review_notes(cls, document, issues, confidence):
        """Generate human-readable review notes"""
        if not issues:
            return f'Documento {document.get_document_type_display()} verificado correctamente.'

        notes = f'Revision de {document.get_document_type_display()}:\n'
        for issue in issues:
            notes += f'- {issue["message"]}\n'
        return notes

    @classmethod
    def get_required_documents(cls, assistance_type: str) -> list:
        """Get list of required documents for assistance type"""
        return REQUIRED_DOCUMENTS.get(assistance_type, [])

    @classmethod
    def check_documents_complete(cls, request) -> dict:
        """Check if all required documents are uploaded and approved"""
        assistance_type = request.service_category.category_type if request.service_category else 'ROADSIDE'
        required = REQUIRED_DOCUMENTS.get(assistance_type, [])

        uploaded_types = set(request.ai_documents.values_list('document_type', flat=True))
        approved_types = set(
            request.ai_documents.filter(
                review_status=AssistanceDocument.ReviewStatus.APPROVED
            ).values_list('document_type', flat=True)
        )

        missing = []
        pending = []

        for doc in required:
            if doc['required']:
                if doc['type'] not in uploaded_types:
                    missing.append(doc)
                elif doc['type'] not in approved_types:
                    pending.append(doc)

        return {
            'complete': len(missing) == 0 and len(pending) == 0,
            'missing_required': missing,
            'pending_approval': pending,
            'total_required': len([d for d in required if d['required']]),
            'total_uploaded': len(uploaded_types),
            'total_approved': len(approved_types)
        }
