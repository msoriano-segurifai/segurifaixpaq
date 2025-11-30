"""
PAQ Wallet Payment Webhooks

Handles callbacks from PAQ when payment status changes.
"""
import hmac
import hashlib
import json
import logging
from decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import WalletTransaction, PaymentWebhookLog
from apps.services.models import UserService

logger = logging.getLogger(__name__)


# PAQ Wallet webhook secret - REQUIRED in production
PAQ_WEBHOOK_SECRET = getattr(settings, 'PAQ_WEBHOOK_SECRET', None)


def verify_paq_signature(payload: str, signature: str) -> bool:
    """
    Verify the webhook signature from PAQ.
    PAQ sends signature in X-PAQ-Signature header (HMAC-SHA256).

    SECURITY: In production (DEBUG=False), signature verification is MANDATORY.
    """
    # In production, webhook secret is REQUIRED
    if not settings.DEBUG and not PAQ_WEBHOOK_SECRET:
        logger.error('SECURITY: PAQ_WEBHOOK_SECRET not configured in production!')
        raise ValueError('PAQ_WEBHOOK_SECRET must be configured in production')

    # In development without secret, allow unsigned webhooks (for testing only)
    if settings.DEBUG and not PAQ_WEBHOOK_SECRET:
        logger.warning('DEV MODE: Skipping webhook signature verification')
        return True

    # If no signature provided but secret is configured, reject
    if not signature:
        logger.warning('Webhook received without signature')
        return False

    expected_signature = hmac.new(
        PAQ_WEBHOOK_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


@api_view(['POST'])
@permission_classes([AllowAny])
def paq_payment_webhook(request):
    """
    Handle payment status callbacks from PAQ Wallet.

    POST /api/wallet/webhook/paq/

    Expected payload from PAQ:
    {
        "transaccion": 12345,
        "referencia": "TEST-001",
        "estado": "PAGADO",
        "monto": 5.00,
        "fecha_pago": "2025-01-15T10:30:00",
        "celular": "30082653",
        "token": "AB12C"
    }

    States:
    - PAGADO: Payment completed successfully
    - CANCELADO: Payment was cancelled
    - EXPIRADO: Token expired
    - PENDIENTE: Still pending
    """
    # Get raw payload for signature verification
    raw_payload = request.body.decode('utf-8')

    # Verify signature if provided
    signature = request.headers.get('X-PAQ-Signature', '')
    if signature and not verify_paq_signature(raw_payload, signature):
        logger.warning('Invalid PAQ webhook signature')
        return Response(
            {'error': 'Invalid signature'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Parse payload
    try:
        data = request.data
    except Exception as e:
        logger.error(f'Failed to parse PAQ webhook payload: {e}')
        return Response(
            {'error': 'Invalid payload'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate idempotency key from transaction ID and reference
    transaccion = data.get('transaccion')
    referencia = data.get('referencia')
    estado = data.get('estado', '').upper()
    idempotency_key = f"PAQ-{transaccion or ''}-{referencia or ''}-{estado}"

    # Check for duplicate webhook (idempotency protection)
    existing_webhook = PaymentWebhookLog.objects.filter(
        idempotency_key=idempotency_key,
        status='PROCESSED'
    ).first()

    if existing_webhook:
        logger.info(f'Duplicate webhook detected: {idempotency_key}')
        PaymentWebhookLog.objects.create(
            provider='PAQ',
            event_type=estado or 'UNKNOWN',
            idempotency_key=f"{idempotency_key}-dup-{timezone.now().timestamp()}",
            payload=data,
            raw_payload=raw_payload,
            status='DUPLICATE'
        )
        return Response({
            'success': True,
            'message': 'Webhook already processed (duplicate)',
            'original_webhook_id': existing_webhook.id
        })

    # Log webhook for debugging and audit
    webhook_log = PaymentWebhookLog.objects.create(
        provider='PAQ',
        event_type=estado or 'UNKNOWN',
        idempotency_key=idempotency_key,
        payload=data,
        raw_payload=raw_payload
    )

    try:
        monto = data.get('monto')
        fecha_pago = data.get('fecha_pago')

        if not transaccion and not referencia:
            webhook_log.status = 'ERROR'
            webhook_log.error_message = 'Missing transaccion or referencia'
            webhook_log.save()
            return Response(
                {'error': 'transaccion or referencia is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find the transaction
        transaction = None
        if transaccion:
            transaction = WalletTransaction.objects.filter(
                external_transaction_id=str(transaccion)
            ).first()

        if not transaction and referencia:
            transaction = WalletTransaction.objects.filter(
                reference_number=referencia
            ).first()

        if not transaction:
            webhook_log.status = 'ERROR'
            webhook_log.error_message = f'Transaction not found: {transaccion or referencia}'
            webhook_log.save()
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update transaction based on status
        old_status = transaction.status
        webhook_log.transaction = transaction

        if estado == 'PAGADO':
            transaction.status = 'COMPLETED'
            transaction.completed_at = timezone.now()

            # Activate user service if this was a subscription payment
            if transaction.user_service:
                transaction.user_service.status = 'ACTIVE'
                transaction.user_service.save()
                logger.info(f'Activated user service {transaction.user_service.id} via webhook')

        elif estado == 'CANCELADO':
            transaction.status = 'CANCELLED'

        elif estado == 'EXPIRADO':
            transaction.status = 'EXPIRED'

        elif estado == 'PENDIENTE':
            transaction.status = 'PENDING'

        else:
            transaction.status = 'UNKNOWN'
            transaction.status_message = f'Unknown status from PAQ: {estado}'

        # Update amount if provided and different
        if monto:
            paq_amount = Decimal(str(monto))
            if transaction.amount != paq_amount:
                logger.warning(
                    f'Amount mismatch for transaction {transaction.id}: '
                    f'expected {transaction.amount}, got {paq_amount}'
                )

        transaction.save()

        # Mark webhook as processed
        webhook_log.status = 'PROCESSED'
        webhook_log.save()

        logger.info(
            f'PAQ webhook processed: transaction {transaccion}, '
            f'status changed from {old_status} to {transaction.status}'
        )

        # Send notification to user (via WebSocket if connected)
        _notify_payment_status(transaction)

        return Response({
            'success': True,
            'message': 'Webhook processed',
            'transaction_id': transaction.id,
            'new_status': transaction.status
        })

    except Exception as e:
        logger.exception(f'Error processing PAQ webhook: {e}')
        webhook_log.status = 'ERROR'
        webhook_log.error_message = str(e)
        webhook_log.save()

        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def paq_notification_webhook(request):
    """
    Handle general notifications from PAQ (SMS delivery, etc.)

    POST /api/wallet/webhook/paq/notification/
    """
    raw_payload = request.body.decode('utf-8')

    # Log the notification
    PaymentWebhookLog.objects.create(
        provider='PAQ',
        event_type='NOTIFICATION',
        payload=request.data,
        raw_payload=raw_payload,
        status='LOGGED'
    )

    logger.info(f'PAQ notification received: {request.data}')

    return Response({'success': True, 'message': 'Notification received'})


def _notify_payment_status(transaction):
    """
    Send real-time notification about payment status change.
    Uses Django Channels if available.
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            # Notify user's personal channel
            user_room = f'user_{transaction.user.id}'

            async_to_sync(channel_layer.group_send)(
                user_room,
                {
                    'type': 'payment_notification',
                    'transaction_id': transaction.id,
                    'reference': transaction.reference_number,
                    'status': transaction.status,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency,
                    'timestamp': timezone.now().isoformat()
                }
            )
    except ImportError:
        # Channels not installed
        pass
    except Exception as e:
        logger.error(f'Failed to send payment notification: {e}')


@api_view(['GET'])
@permission_classes([AllowAny])
def webhook_health_check(request):
    """
    Health check endpoint for webhook monitoring.

    GET /api/wallet/webhook/health/
    """
    return Response({
        'status': 'healthy',
        'provider': 'PAQ Wallet',
        'timestamp': timezone.now().isoformat()
    })
