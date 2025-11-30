from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class WalletTransaction(models.Model):
    """Track wallet transactions (for future integration with PAQ Wallet API)"""

    class TransactionType(models.TextChoices):
        PAYMENT = 'PAYMENT', _('Payment')
        REFUND = 'REFUND', _('Refund')
        CHARGE = 'CHARGE', _('Charge')
        CREDIT = 'CREDIT', _('Credit')

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        EXPIRED = 'EXPIRED', _('Expired')
        UNKNOWN = 'UNKNOWN', _('Unknown')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet_transactions',
        verbose_name=_('user')
    )

    # Transaction details
    transaction_type = models.CharField(
        _('transaction type'),
        max_length=20,
        choices=TransactionType.choices
    )
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='GTQ')

    # Reference
    reference_number = models.CharField(_('reference number'), max_length=100, unique=True)
    external_transaction_id = models.CharField(_('external transaction ID'), max_length=200, blank=True, help_text='PAQ Wallet transaction ID')

    # Related objects
    assistance_request = models.ForeignKey(
        'assistance.AssistanceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
        verbose_name=_('assistance request')
    )
    user_service = models.ForeignKey(
        'services.UserService',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
        verbose_name=_('user service'),
        help_text='Linked subscription payment'
    )

    # Completion timestamp
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)

    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    status_message = models.TextField(_('status message'), blank=True)

    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('wallet transaction')
        verbose_name_plural = _('wallet transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference_number']),
        ]

    def __str__(self):
        return f'{self.reference_number} - {self.user.email} - {self.transaction_type}'


class PaymentWebhookLog(models.Model):
    """Log all incoming payment webhooks for audit and debugging"""

    class Status(models.TextChoices):
        RECEIVED = 'RECEIVED', _('Received')
        PROCESSED = 'PROCESSED', _('Processed')
        ERROR = 'ERROR', _('Error')
        LOGGED = 'LOGGED', _('Logged Only')
        DUPLICATE = 'DUPLICATE', _('Duplicate - Skipped')

    provider = models.CharField(_('provider'), max_length=50, default='PAQ')
    event_type = models.CharField(_('event type'), max_length=50)

    # Idempotency key for preventing duplicate processing
    idempotency_key = models.CharField(
        _('idempotency key'),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text='Unique identifier to prevent duplicate webhook processing'
    )

    # Link to transaction if found
    transaction = models.ForeignKey(
        WalletTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_logs',
        verbose_name=_('transaction')
    )

    # Payload data
    payload = models.JSONField(_('payload'), default=dict)
    raw_payload = models.TextField(_('raw payload'), blank=True)

    # Processing status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED
    )
    error_message = models.TextField(_('error message'), blank=True)

    # Source info
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.CharField(_('user agent'), max_length=500, blank=True)

    received_at = models.DateTimeField(_('received at'), auto_now_add=True)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)

    class Meta:
        verbose_name = _('payment webhook log')
        verbose_name_plural = _('payment webhook logs')
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['status', 'received_at']),
        ]

    def __str__(self):
        return f'{self.provider} - {self.event_type} - {self.status}'
