"""
Serializers for Assistance Document Upload and AI Review
"""
from rest_framework import serializers
from .documents import AssistanceDocument, REQUIRED_DOCUMENTS, DocumentReviewService


class AssistanceDocumentSerializer(serializers.ModelSerializer):
    """Serializer for AssistanceDocument model"""

    document_type_display = serializers.CharField(
        source='get_document_type_display',
        read_only=True
    )
    review_status_display = serializers.CharField(
        source='get_review_status_display',
        read_only=True
    )

    class Meta:
        model = AssistanceDocument
        fields = [
            'id',
            'request',
            'document_type',
            'document_type_display',
            'file',
            'original_filename',
            'file_size',
            'mime_type',
            'review_status',
            'review_status_display',
            'ai_confidence_score',
            'ai_review_notes',
            'ai_detected_issues',
            'reviewed_at',
            'reviewed_by',
            'uploaded_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'file_size',
            'mime_type',
            'review_status',
            'ai_confidence_score',
            'ai_review_notes',
            'ai_detected_issues',
            'reviewed_at',
            'reviewed_by',
            'uploaded_at',
            'updated_at'
        ]


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload"""

    request_id = serializers.IntegerField(
        help_text='ID of the assistance request'
    )
    document_type = serializers.ChoiceField(
        choices=AssistanceDocument.DocumentType.choices,
        help_text='Type of document being uploaded'
    )
    file = serializers.FileField(
        help_text='The document file (image or PDF)'
    )

    def validate_file(self, value):
        """Validate file size and type"""
        # Max 10MB
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f'Archivo muy grande. Maximo permitido: 10MB'
            )

        # Check extension
        ext = value.name.split('.')[-1].lower()
        allowed = ['jpg', 'jpeg', 'png', 'webp', 'pdf']
        if ext not in allowed:
            raise serializers.ValidationError(
                f'Formato no permitido. Use: {", ".join(allowed)}'
            )

        return value


class DocumentReviewResultSerializer(serializers.Serializer):
    """Serializer for document review results"""

    document_id = serializers.IntegerField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    confidence = serializers.FloatField()
    issues = serializers.ListField(
        child=serializers.DictField()
    )
    notes = serializers.CharField()


class RequiredDocumentSerializer(serializers.Serializer):
    """Serializer for required document info"""

    type = serializers.CharField()
    type_display = serializers.SerializerMethodField()
    required = serializers.BooleanField()
    description = serializers.CharField()
    uploaded = serializers.BooleanField(default=False)
    approved = serializers.BooleanField(default=False)
    document_id = serializers.IntegerField(allow_null=True, default=None)

    def get_type_display(self, obj):
        """Get display name for document type"""
        type_map = dict(AssistanceDocument.DocumentType.choices)
        return type_map.get(obj.get('type'), obj.get('type'))


class DocumentStatusSerializer(serializers.Serializer):
    """Serializer for document completion status"""

    complete = serializers.BooleanField()
    missing_required = RequiredDocumentSerializer(many=True)
    pending_approval = RequiredDocumentSerializer(many=True)
    total_required = serializers.IntegerField()
    total_uploaded = serializers.IntegerField()
    total_approved = serializers.IntegerField()


class ManualReviewSerializer(serializers.Serializer):
    """Serializer for manual document review by admin"""

    status = serializers.ChoiceField(
        choices=[
            ('APPROVED', 'Aprobado'),
            ('REJECTED', 'Rechazado'),
            ('NEEDS_RESUBMIT', 'Requiere Reenvio')
        ]
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Notas adicionales de revision'
    )
