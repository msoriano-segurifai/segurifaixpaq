from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid

# Import enhanced document model with AI review
from .documents import AssistanceDocument, REQUIRED_DOCUMENTS, DocumentReviewService


class AssistanceRequest(models.Model):
    """Assistance requests from users"""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ASSIGNED = 'ASSIGNED', _('Assigned to Provider')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        REJECTED = 'REJECTED', _('Rejected')

    class Priority(models.TextChoices):
        LOW = 'LOW', _('Low')
        MEDIUM = 'MEDIUM', _('Medium')
        HIGH = 'HIGH', _('High')
        URGENT = 'URGENT', _('Urgent')

    # Unique identifier
    request_number = models.CharField(_('request number'), max_length=50, unique=True, editable=False)

    # User and Service
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assistance_requests',
        verbose_name=_('user')
    )
    user_service = models.ForeignKey(
        'services.UserService',
        on_delete=models.PROTECT,
        related_name='requests',
        verbose_name=_('user service'),
        null=True,
        blank=True,
        help_text=_('Optional for MAWDY direct requests')
    )
    service_category = models.ForeignKey(
        'services.ServiceCategory',
        on_delete=models.PROTECT,
        related_name='requests',
        verbose_name=_('service category'),
        null=True,
        blank=True,
        help_text=_('Optional for MAWDY direct requests')
    )

    # Provider assignment
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests',
        verbose_name=_('provider')
    )

    # Direct technician assignment (for MAWDY direct assignments)
    assigned_tech = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests_as_tech',
        verbose_name=_('assigned technician'),
        help_text=_('Direct technician assignment (MAWDY field tech)')
    )
    assigned_at = models.DateTimeField(_('assigned at'), null=True, blank=True)

    # Request details
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    priority = models.CharField(
        _('priority'),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    # Location
    location_address = models.TextField(_('location address'))
    location_city = models.CharField(_('city'), max_length=100)
    location_state = models.CharField(_('state'), max_length=100)
    location_latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    location_longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6, null=True, blank=True)

    # Specific to roadside assistance
    vehicle_make = models.CharField(_('vehicle make'), max_length=100, blank=True)
    vehicle_model = models.CharField(_('vehicle model'), max_length=100, blank=True)
    vehicle_year = models.IntegerField(_('vehicle year'), null=True, blank=True)
    vehicle_plate = models.CharField(_('vehicle plate'), max_length=20, blank=True)

    # Specific to health assistance
    patient_name = models.CharField(_('patient name'), max_length=200, blank=True)
    patient_age = models.IntegerField(_('patient age'), null=True, blank=True)
    symptoms = models.TextField(_('symptoms'), blank=True)

    # Specific to card insurance
    card_last_four = models.CharField(_('card last 4 digits'), max_length=4, blank=True)
    incident_type = models.CharField(_('incident type'), max_length=100, blank=True, help_text='Fraud, theft, etc.')

    # Status and tracking
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Estimated and actual times
    estimated_arrival_time = models.DateTimeField(_('estimated arrival time'), null=True, blank=True)
    actual_arrival_time = models.DateTimeField(_('actual arrival time'), null=True, blank=True)
    completion_time = models.DateTimeField(_('completion time'), null=True, blank=True)

    # Cost
    estimated_cost = models.DecimalField(_('estimated cost'), max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(_('actual cost'), max_digits=10, decimal_places=2, null=True, blank=True)

    # Notes
    admin_notes = models.TextField(_('admin notes'), blank=True)
    cancellation_reason = models.TextField(_('cancellation reason'), blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('assistance request')
        verbose_name_plural = _('assistance requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['provider', 'status']),
        ]

    def __str__(self):
        return f'{self.request_number} - {self.user.email} - {self.status}'

    def save(self, *args, **kwargs):
        if not self.request_number:
            # Generate unique request number
            self.request_number = f'REQ-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)


class RequestUpdate(models.Model):
    """Updates and messages for assistance requests"""

    class UpdateType(models.TextChoices):
        STATUS_CHANGE = 'STATUS_CHANGE', _('Status Change')
        MESSAGE = 'MESSAGE', _('Message')
        LOCATION_UPDATE = 'LOCATION_UPDATE', _('Location Update')
        ARRIVAL_UPDATE = 'ARRIVAL_UPDATE', _('Arrival Update')

    request = models.ForeignKey(
        AssistanceRequest,
        on_delete=models.CASCADE,
        related_name='updates',
        verbose_name=_('request')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='request_updates',
        verbose_name=_('user')
    )

    update_type = models.CharField(
        _('update type'),
        max_length=20,
        choices=UpdateType.choices,
        default=UpdateType.MESSAGE
    )
    message = models.TextField(_('message'))

    # Optional metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('request update')
        verbose_name_plural = _('request updates')
        ordering = ['created_at']

    def __str__(self):
        return f'{self.request.request_number} - {self.update_type} at {self.created_at}'


class RequestDocument(models.Model):
    """Documents attached to assistance requests"""

    class DocumentType(models.TextChoices):
        PHOTO = 'PHOTO', _('Photo')
        INVOICE = 'INVOICE', _('Invoice')
        RECEIPT = 'RECEIPT', _('Receipt')
        REPORT = 'REPORT', _('Report')
        OTHER = 'OTHER', _('Other')

    request = models.ForeignKey(
        AssistanceRequest,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('request')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        verbose_name=_('uploaded by')
    )

    document_type = models.CharField(
        _('document type'),
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    file = models.FileField(_('file'), upload_to='assistance/documents/')
    description = models.CharField(_('description'), max_length=200, blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('request document')
        verbose_name_plural = _('request documents')
        ordering = ['created_at']

    def __str__(self):
        return f'{self.request.request_number} - {self.document_type}'
