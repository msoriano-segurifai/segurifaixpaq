from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Provider(models.Model):
    """Assistance Provider Profile"""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        ACTIVE = 'ACTIVE', _('Active')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        INACTIVE = 'INACTIVE', _('Inactive')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_profile',
        verbose_name=_('user'),
        limit_choices_to={'role': 'PROVIDER'}
    )

    # Company Information
    company_name = models.CharField(_('company name'), max_length=200)
    business_license = models.CharField(_('business license'), max_length=100, unique=True)
    tax_id = models.CharField(_('tax ID'), max_length=50, blank=True)

    # Contact Information
    business_phone = models.CharField(_('business phone'), max_length=20)
    business_email = models.EmailField(_('business email'))
    website = models.URLField(_('website'), blank=True)

    # Address
    address = models.TextField(_('address'))
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(_('country'), max_length=100, default='Guatemala')

    # Location (for geolocation)
    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6, null=True, blank=True)

    # Services offered
    service_categories = models.ManyToManyField(
        'services.ServiceCategory',
        related_name='providers',
        verbose_name=_('service categories')
    )

    # Service area
    service_radius_km = models.IntegerField(_('service radius (km)'), default=50)
    service_areas = models.JSONField(_('service areas'), default=list, help_text='List of cities/areas served')

    # Availability
    is_available = models.BooleanField(_('currently available'), default=True)
    working_hours = models.JSONField(
        _('working hours'),
        default=dict,
        help_text='Working hours by day: {"monday": {"start": "08:00", "end": "18:00"}, ...}'
    )

    # Ratings
    rating = models.DecimalField(
        _('average rating'),
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)]
    )
    total_reviews = models.IntegerField(_('total reviews'), default=0)
    total_completed = models.IntegerField(_('total completed requests'), default=0)

    # Documents
    certificate = models.FileField(_('certificate'), upload_to='providers/certificates/', blank=True, null=True)
    insurance_policy = models.FileField(_('insurance policy'), upload_to='providers/insurance/', blank=True, null=True)

    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    verification_notes = models.TextField(_('verification notes'), blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('provider')
        verbose_name_plural = _('providers')
        ordering = ['-created_at']

    def __str__(self):
        return self.company_name

    @property
    def is_active(self):
        """Check if provider is active"""
        return self.status == self.Status.ACTIVE and self.is_available


class ProviderReview(models.Model):
    """Reviews for providers"""

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('provider')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_reviews',
        verbose_name=_('user')
    )
    assistance_request = models.ForeignKey(
        'assistance.AssistanceRequest',
        on_delete=models.CASCADE,
        related_name='provider_reviews',
        verbose_name=_('assistance request'),
        null=True,
        blank=True
    )

    rating = models.IntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_('comment'), blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('provider review')
        verbose_name_plural = _('provider reviews')
        ordering = ['-created_at']
        unique_together = [['provider', 'user', 'assistance_request']]

    def __str__(self):
        return f'{self.provider.company_name} - {self.rating}/5 by {self.user.email}'


class ProviderLocation(models.Model):
    """Real-time location tracking for providers"""

    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='current_location',
        verbose_name=_('provider')
    )

    # Location coordinates
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6
    )

    # Movement data
    heading = models.FloatField(
        _('heading (degrees)'),
        null=True,
        blank=True,
        help_text='Direction of movement in degrees (0-360)'
    )
    speed = models.FloatField(
        _('speed (km/h)'),
        null=True,
        blank=True
    )
    accuracy = models.FloatField(
        _('accuracy (meters)'),
        null=True,
        blank=True,
        help_text='GPS accuracy in meters'
    )

    # Status
    is_online = models.BooleanField(_('is online'), default=True)
    last_updated = models.DateTimeField(_('last updated'), auto_now=True)

    class Meta:
        verbose_name = _('provider location')
        verbose_name_plural = _('provider locations')

    def __str__(self):
        return f'{self.provider.company_name} - ({self.latitude}, {self.longitude})'


class ProviderLocationHistory(models.Model):
    """Historical location data for providers"""

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='location_history',
        verbose_name=_('provider')
    )
    assistance_request = models.ForeignKey(
        'assistance.AssistanceRequest',
        on_delete=models.CASCADE,
        related_name='provider_locations',
        verbose_name=_('assistance request'),
        null=True,
        blank=True
    )

    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6)
    heading = models.FloatField(_('heading'), null=True, blank=True)
    speed = models.FloatField(_('speed'), null=True, blank=True)

    recorded_at = models.DateTimeField(_('recorded at'), auto_now_add=True)

    class Meta:
        verbose_name = _('provider location history')
        verbose_name_plural = _('provider location history')
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['provider', 'recorded_at']),
            models.Index(fields=['assistance_request', 'recorded_at']),
        ]

    def __str__(self):
        return f'{self.provider.company_name} at {self.recorded_at}'
