from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError


class ServiceCategory(models.Model):
    """Service categories: Roadside, Health, Card Insurance"""

    class CategoryType(models.TextChoices):
        ROADSIDE = 'ROADSIDE', _('Roadside Assistance')
        HEALTH = 'HEALTH', _('Health Assistance')
        INSURANCE = 'INSURANCE', _('Personal Accident Insurance')
        CARD_INSURANCE = 'CARD_INSURANCE', _('Card Insurance')

    name = models.CharField(_('name'), max_length=100)
    category_type = models.CharField(
        _('category type'),
        max_length=20,
        choices=CategoryType.choices,
        unique=True
    )
    description = models.TextField(_('description'))
    icon = models.CharField(_('icon'), max_length=50, blank=True, help_text='Icon name or class')
    is_active = models.BooleanField(_('active'), default=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('service category')
        verbose_name_plural = _('service categories')
        ordering = ['name']

    def __str__(self):
        return self.get_category_type_display()


class ServicePlan(models.Model):
    """Service plans/packages offered"""

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='plans',
        verbose_name=_('category')
    )
    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'))
    features = models.JSONField(_('features'), default=list, help_text='List of features included')

    # Pricing
    price_monthly = models.DecimalField(_('monthly price'), max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(_('yearly price'), max_digits=10, decimal_places=2, null=True, blank=True)

    # Duration
    duration_days = models.PositiveIntegerField(
        _('duration in days'),
        default=30,
        help_text='Number of days the subscription lasts (30 for monthly, 365 for yearly)'
    )

    @property
    def price(self):
        """Default price property - returns monthly price for compatibility"""
        return self.price_monthly

    # Limits
    max_requests_per_month = models.IntegerField(_('max requests per month'), default=0, help_text='0 for unlimited')
    coverage_amount = models.DecimalField(_('coverage amount'), max_digits=12, decimal_places=2, null=True, blank=True)

    # Terms and Conditions
    terms_and_conditions = models.TextField(_('terms and conditions'), blank=True, default='')

    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_featured = models.BooleanField(_('featured'), default=False)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('service plan')
        verbose_name_plural = _('service plans')
        ordering = ['category', 'price_monthly']

    def __str__(self):
        return f'{self.category.get_category_type_display()} - {self.name}'


class UserService(models.Model):
    """Services subscribed by users"""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        CANCELLED = 'CANCELLED', _('Cancelled')
        EXPIRED = 'EXPIRED', _('Expired')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name=_('user')
    )
    plan = models.ForeignKey(
        ServicePlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('plan')
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    # Dates
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True)
    last_renewal_date = models.DateField(_('last renewal date'), null=True, blank=True)
    next_renewal_date = models.DateField(_('next renewal date'), null=True, blank=True)

    # Auto-renewal
    auto_renew = models.BooleanField(_('auto renew'), default=False)

    # Usage tracking
    requests_this_month = models.IntegerField(_('requests this month'), default=0)
    total_requests = models.IntegerField(_('total requests'), default=0)

    # Notes
    notes = models.TextField(_('notes'), blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user service')
        verbose_name_plural = _('user services')
        ordering = ['-created_at']
        unique_together = [['user', 'plan', 'status']]

    def __str__(self):
        return f'{self.user.email} - {self.plan.name} ({self.status})'

    def clean(self):
        """Validate that user doesn't have multiple ACTIVE subscriptions for same plan"""
        if self.status == self.Status.ACTIVE:
            existing = UserService.objects.filter(
                user=self.user,
                plan=self.plan,
                status=self.Status.ACTIVE
            ).exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError({
                    'plan': _('Ya tienes una suscripcion activa para este plan')
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if service is active"""
        return self.status == self.Status.ACTIVE

    @property
    def can_request_service(self):
        """Check if user can request service based on limits"""
        if not self.is_active:
            return False

        max_requests = self.plan.max_requests_per_month
        if max_requests == 0:  # Unlimited
            return True

        return self.requests_this_month < max_requests
