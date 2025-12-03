from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class Booking(models.Model):
    """
    SegurifAI Booking Model
    Represents a service booking/appointment made by a user.
    Supports full CRUD operations with status tracking.
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pendiente')
        CONFIRMED = 'CONFIRMED', _('Confirmado')
        IN_PROGRESS = 'IN_PROGRESS', _('En Progreso')
        COMPLETED = 'COMPLETED', _('Completado')
        CANCELLED = 'CANCELLED', _('Cancelado')
        NO_SHOW = 'NO_SHOW', _('No Asistio')
        RESCHEDULED = 'RESCHEDULED', _('Reprogramado')

    class ServiceType(models.TextChoices):
        ROADSIDE = 'ROADSIDE', _('Asistencia Vial')
        HEALTH = 'HEALTH', _('Asistencia Medica')
        CONSULTATION = 'CONSULTATION', _('Consulta')
        TOWING = 'TOWING', _('Grua')
        FUEL = 'FUEL', _('Combustible')
        TIRE = 'TIRE', _('Cambio de Neumatico')
        BATTERY = 'BATTERY', _('Paso de Corriente')
        LOCKSMITH = 'LOCKSMITH', _('Cerrajeria')
        AMBULANCE = 'AMBULANCE', _('Ambulancia')
        MEDICAL_APPOINTMENT = 'MEDICAL_APPOINTMENT', _('Cita Medica')
        LAB_EXAM = 'LAB_EXAM', _('Examen de Laboratorio')
        PSYCHOLOGY = 'PSYCHOLOGY', _('Psicologia')
        NUTRITION = 'NUTRITION', _('Nutricion')
        OTHER = 'OTHER', _('Otro')

    class Priority(models.TextChoices):
        LOW = 'LOW', _('Baja')
        NORMAL = 'NORMAL', _('Normal')
        HIGH = 'HIGH', _('Alta')
        URGENT = 'URGENT', _('Urgente')

    # Unique reference code
    reference_code = models.CharField(
        _('codigo de referencia'),
        max_length=20,
        unique=True,
        editable=False
    )

    # User who made the booking
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('usuario')
    )

    # Service details
    service_type = models.CharField(
        _('tipo de servicio'),
        max_length=30,
        choices=ServiceType.choices,
        default=ServiceType.OTHER
    )
    service_name = models.CharField(
        _('nombre del servicio'),
        max_length=200
    )
    description = models.TextField(
        _('descripcion'),
        blank=True
    )

    # Status tracking
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    priority = models.CharField(
        _('prioridad'),
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL
    )

    # Scheduling
    scheduled_date = models.DateField(
        _('fecha programada')
    )
    scheduled_time = models.TimeField(
        _('hora programada'),
        null=True,
        blank=True
    )
    estimated_duration_minutes = models.PositiveIntegerField(
        _('duracion estimada (minutos)'),
        default=60
    )

    # Location
    location_address = models.CharField(
        _('direccion'),
        max_length=500,
        blank=True
    )
    location_latitude = models.DecimalField(
        _('latitud'),
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    location_longitude = models.DecimalField(
        _('longitud'),
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    location_notes = models.TextField(
        _('notas de ubicacion'),
        blank=True,
        help_text=_('Instrucciones adicionales para llegar')
    )

    # Provider assignment (optional)
    assigned_provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings',
        verbose_name=_('proveedor asignado'),
        limit_choices_to={'role__in': ['PROVIDER', 'MAWDY_FIELD_TECH']}
    )

    # Contact information
    contact_name = models.CharField(
        _('nombre de contacto'),
        max_length=150,
        blank=True
    )
    contact_phone = models.CharField(
        _('telefono de contacto'),
        max_length=20,
        blank=True
    )

    # Notes and metadata
    user_notes = models.TextField(
        _('notas del usuario'),
        blank=True
    )
    admin_notes = models.TextField(
        _('notas internas'),
        blank=True,
        help_text=_('Notas visibles solo para administradores')
    )

    # Cancellation info
    cancelled_at = models.DateTimeField(
        _('cancelado en'),
        null=True,
        blank=True
    )
    cancellation_reason = models.TextField(
        _('razon de cancelacion'),
        blank=True
    )

    # Completion info
    completed_at = models.DateTimeField(
        _('completado en'),
        null=True,
        blank=True
    )
    completion_notes = models.TextField(
        _('notas de finalizacion'),
        blank=True
    )

    # Rating (after completion)
    rating = models.PositiveSmallIntegerField(
        _('calificacion'),
        null=True,
        blank=True,
        help_text=_('Calificacion del 1 al 5')
    )
    rating_comment = models.TextField(
        _('comentario de calificacion'),
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(_('creado en'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado en'), auto_now=True)

    class Meta:
        verbose_name = _('reserva')
        verbose_name_plural = _('reservas')
        ordering = ['-scheduled_date', '-scheduled_time', '-created_at']
        indexes = [
            models.Index(fields=['reference_code']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['status', 'priority']),
        ]

    def __str__(self):
        return f'{self.reference_code} - {self.service_name} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        # Generate unique reference code on first save
        if not self.reference_code:
            self.reference_code = self._generate_reference_code()
        super().save(*args, **kwargs)

    def _generate_reference_code(self):
        """Generate a unique reference code like SRF-XXXXXX"""
        prefix = 'SRF'
        unique_part = uuid.uuid4().hex[:6].upper()
        return f'{prefix}-{unique_part}'

    def cancel(self, reason=''):
        """Cancel the booking"""
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'updated_at'])

    def confirm(self):
        """Confirm the booking"""
        self.status = self.Status.CONFIRMED
        self.save(update_fields=['status', 'updated_at'])

    def start(self):
        """Mark booking as in progress"""
        self.status = self.Status.IN_PROGRESS
        self.save(update_fields=['status', 'updated_at'])

    def complete(self, notes=''):
        """Complete the booking"""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.completion_notes = notes
        self.save(update_fields=['status', 'completed_at', 'completion_notes', 'updated_at'])

    def rate(self, rating, comment=''):
        """Rate the completed booking"""
        if self.status != self.Status.COMPLETED:
            raise ValueError(_('Solo puedes calificar reservas completadas'))
        if not 1 <= rating <= 5:
            raise ValueError(_('La calificacion debe estar entre 1 y 5'))
        self.rating = rating
        self.rating_comment = comment
        self.save(update_fields=['rating', 'rating_comment', 'updated_at'])

    @property
    def is_cancellable(self):
        """Check if booking can be cancelled"""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

    @property
    def is_ratable(self):
        """Check if booking can be rated"""
        return self.status == self.Status.COMPLETED and self.rating is None

    @property
    def scheduled_datetime(self):
        """Get combined scheduled datetime"""
        if self.scheduled_time:
            return timezone.make_aware(
                timezone.datetime.combine(self.scheduled_date, self.scheduled_time)
            )
        return None


class BookingStatusHistory(models.Model):
    """
    Track booking status changes for audit trail
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('reserva')
    )
    previous_status = models.CharField(
        _('estado anterior'),
        max_length=20,
        choices=Booking.Status.choices,
        blank=True
    )
    new_status = models.CharField(
        _('nuevo estado'),
        max_length=20,
        choices=Booking.Status.choices
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking_status_changes',
        verbose_name=_('cambiado por')
    )
    notes = models.TextField(_('notas'), blank=True)
    created_at = models.DateTimeField(_('fecha'), auto_now_add=True)

    class Meta:
        verbose_name = _('historial de estado')
        verbose_name_plural = _('historial de estados')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.booking.reference_code}: {self.previous_status} -> {self.new_status}'
