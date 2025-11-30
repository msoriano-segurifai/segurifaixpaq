"""
Promo Codes and Discounts Models

Supports various discount types for plans and services.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class PromoCode(models.Model):
    """Promotional discount codes"""

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', _('Porcentaje')
        FIXED_AMOUNT = 'FIXED_AMOUNT', _('Monto Fijo')
        FREE_TRIAL = 'FREE_TRIAL', _('Prueba Gratis')

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Activo')
        INACTIVE = 'INACTIVE', _('Inactivo')
        EXPIRED = 'EXPIRED', _('Expirado')
        DEPLETED = 'DEPLETED', _('Agotado')

    # Code identifier
    code = models.CharField(
        _('codigo'),
        max_length=50,
        unique=True,
        help_text='Codigo unico para el descuento'
    )
    name = models.CharField(_('nombre'), max_length=200)
    description = models.TextField(_('descripcion'), blank=True)

    # Discount configuration
    discount_type = models.CharField(
        _('tipo de descuento'),
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(
        _('valor del descuento'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Porcentaje (0-100) o monto fijo en GTQ'
    )
    max_discount_amount = models.DecimalField(
        _('descuento maximo'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Limite maximo de descuento para porcentajes'
    )

    # Usage limits
    max_uses = models.PositiveIntegerField(
        _('usos maximos totales'),
        null=True,
        blank=True,
        help_text='Dejar vacio para usos ilimitados'
    )
    max_uses_per_user = models.PositiveIntegerField(
        _('usos maximos por usuario'),
        default=1,
        help_text='Cuantas veces puede usar este codigo cada usuario'
    )
    current_uses = models.PositiveIntegerField(_('usos actuales'), default=0)

    # Validity dates
    valid_from = models.DateTimeField(_('valido desde'))
    valid_until = models.DateTimeField(_('valido hasta'))

    # Minimum requirements
    minimum_purchase = models.DecimalField(
        _('compra minima'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Monto minimo de compra requerido'
    )

    # Restrictions
    applicable_plans = models.ManyToManyField(
        'services.ServicePlan',
        blank=True,
        related_name='promo_codes',
        verbose_name=_('planes aplicables'),
        help_text='Dejar vacio para aplicar a todos los planes'
    )
    applicable_categories = models.ManyToManyField(
        'services.ServiceCategory',
        blank=True,
        related_name='promo_codes',
        verbose_name=_('categorias aplicables')
    )
    first_purchase_only = models.BooleanField(
        _('solo primera compra'),
        default=False
    )
    new_users_only = models.BooleanField(
        _('solo usuarios nuevos'),
        default=False
    )

    # Status
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_promo_codes',
        verbose_name=_('creado por')
    )
    created_at = models.DateTimeField(_('creado en'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado en'), auto_now=True)

    class Meta:
        verbose_name = _('codigo promocional')
        verbose_name_plural = _('codigos promocionales')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status', 'valid_from', 'valid_until']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'

    @property
    def is_valid(self):
        """Check if promo code is currently valid"""
        from django.utils import timezone
        now = timezone.now()

        if self.status != self.Status.ACTIVE:
            return False

        if now < self.valid_from or now > self.valid_until:
            return False

        if self.max_uses and self.current_uses >= self.max_uses:
            return False

        return True

    def calculate_discount(self, original_price: Decimal) -> Decimal:
        """Calculate the discount amount for a given price"""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = original_price * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        elif self.discount_type == self.DiscountType.FIXED_AMOUNT:
            discount = min(self.discount_value, original_price)
        elif self.discount_type == self.DiscountType.FREE_TRIAL:
            discount = original_price
        else:
            discount = Decimal('0.00')

        return discount.quantize(Decimal('0.01'))


class PromoCodeUsage(models.Model):
    """Track usage of promo codes"""

    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name=_('codigo promocional')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='promo_code_usages',
        verbose_name=_('usuario')
    )

    # Transaction reference
    transaction = models.ForeignKey(
        'paq_wallet.WalletTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promo_code_usages',
        verbose_name=_('transaccion')
    )
    user_service = models.ForeignKey(
        'services.UserService',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promo_code_usages',
        verbose_name=_('servicio')
    )

    # Discount details
    original_price = models.DecimalField(
        _('precio original'),
        max_digits=10,
        decimal_places=2
    )
    discount_amount = models.DecimalField(
        _('monto descontado'),
        max_digits=10,
        decimal_places=2
    )
    final_price = models.DecimalField(
        _('precio final'),
        max_digits=10,
        decimal_places=2
    )

    used_at = models.DateTimeField(_('usado en'), auto_now_add=True)

    class Meta:
        verbose_name = _('uso de codigo promocional')
        verbose_name_plural = _('usos de codigos promocionales')
        ordering = ['-used_at']

    def __str__(self):
        return f'{self.promo_code.code} usado por {self.user.email}'


class Campaign(models.Model):
    """Marketing campaigns with multiple promo codes"""

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Borrador')
        ACTIVE = 'ACTIVE', _('Activa')
        PAUSED = 'PAUSED', _('Pausada')
        COMPLETED = 'COMPLETED', _('Completada')

    name = models.CharField(_('nombre'), max_length=200)
    description = models.TextField(_('descripcion'), blank=True)

    promo_codes = models.ManyToManyField(
        PromoCode,
        related_name='campaigns',
        verbose_name=_('codigos promocionales')
    )

    start_date = models.DateTimeField(_('fecha inicio'))
    end_date = models.DateTimeField(_('fecha fin'))

    target_audience = models.CharField(
        _('audiencia objetivo'),
        max_length=100,
        blank=True,
        help_text='Descripcion del publico objetivo'
    )
    budget = models.DecimalField(
        _('presupuesto'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_campaigns',
        verbose_name=_('creado por')
    )
    created_at = models.DateTimeField(_('creado en'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado en'), auto_now=True)

    class Meta:
        verbose_name = _('campana')
        verbose_name_plural = _('campanas')
        ordering = ['-created_at']

    def __str__(self):
        return self.name
