"""
PAQ Wallet Views
================

API endpoints for PAQ Wallet integration with ISO 27001 compliance.

Security Controls Applied:
- A.9: Role-based access control
- A.10: Transaction data masking
- A.12: Comprehensive audit logging
- A.14: Input validation
- A.18: Transaction audit trail

Author: SegurifAI Development Team
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from typing import Optional

from .models import WalletTransaction
from .serializers import WalletTransactionSerializer, WalletTransactionCreateSerializer, WalletBalanceSerializer
from .services import paq_wallet_service
from apps.users.permissions import IsAdmin

# ISO 27001 Compliance imports
from apps.core.compliance import (
    audit_paq_transaction,
    require_access,
    log_security_event,
    SecurityEventType,
    PAQTransactionSecurity,
    PIIMasker,
    DataClassification,
    require_data_classification,
)


def get_paq_phone_number(user) -> Optional[str]:
    """
    Extract the phone number for PAQ API calls.

    PAQ Wallet ID is stored as 'PAQ-{phone}' format.
    This extracts the phone number for API calls.
    Falls back to user's phone_number if paq_wallet_id is not set.
    """
    def clean_phone(phone: str) -> str:
        """Remove country code, dashes and spaces from phone number"""
        phone = phone.replace('-', '').replace(' ', '').replace('+', '')
        # Remove Guatemala country code (+502)
        if phone.startswith('502') and len(phone) > 8:
            phone = phone[3:]
        return phone

    if user.paq_wallet_id:
        # Remove 'PAQ-' prefix if present
        paq_id = user.paq_wallet_id
        if paq_id.startswith('PAQ-'):
            return clean_phone(paq_id[4:])  # Remove 'PAQ-' prefix
        return clean_phone(paq_id)

    # Fallback to phone number for PAQ users
    if user.phone_number:
        return clean_phone(user.phone_number)

    return None


class WalletTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for Wallet Transactions"""

    queryset = WalletTransaction.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return WalletTransactionCreateSerializer
        return WalletTransactionSerializer

    def get_queryset(self):
        """Filter transactions based on user role"""
        user = self.request.user

        if user.is_admin:
            return self.queryset.all()
        else:
            return self.queryset.filter(user=user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    """Get user's PAQ Wallet balance"""

    user = request.user

    # Get phone number for PAQ API
    phone_number = get_paq_phone_number(user)

    if not phone_number:
        return Response(
            {'error': 'User does not have a PAQ Wallet ID linked'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Call PAQ Wallet service to get balance
    balance_data = paq_wallet_service.get_user_balance(phone_number)

    if balance_data is None:
        return Response(
            {'error': 'Failed to retrieve wallet balance'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    serializer = WalletBalanceSerializer(data=balance_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_transactions(request):
    """Get user's PAQ Wallet transaction history"""

    user = request.user

    # Get phone number for PAQ API
    phone_number = get_paq_phone_number(user)

    if not phone_number:
        return Response(
            {'error': 'User does not have a PAQ Wallet ID linked'},
            status=status.HTTP_400_BAD_REQUEST
        )

    limit = request.query_params.get('limit', 10)

    # Call PAQ Wallet service to get transactions
    transactions = paq_wallet_service.get_transaction_history(phone_number, limit=int(limit))

    # Check if we got actual transactions from PAQ
    if transactions:
        return Response({
            'paq_wallet_id': user.paq_wallet_id or f'PAQ-{phone_number}',
            'phone_number': phone_number,
            'transactions': transactions,
            'count': len(transactions)
        })
    else:
        # No transactions found - return empty list with explanation
        return Response({
            'paq_wallet_id': user.paq_wallet_id or f'PAQ-{phone_number}',
            'phone_number': phone_number,
            'transactions': [],
            'count': 0,
            'message': 'No se encontraron transacciones recientes'
        })


# ============================================
# PAQ-GO Payment Flow Endpoints
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_paq_transaction("token_generation")
def generate_payment_token(request):
    """
    Generate a PAYPAQ token for payment (emite_token)

    ISO 27001 Controls:
    - A.9.2.3: Management of privileged access rights
    - A.10.1.2: Key management for token security
    - A.12.4.1: Event logging

    POST /api/wallet/generate-token/

    Body:
    {
        "monto": 5.00,
        "referencia": "TEST-001",
        "horas_vigencia": 24,
        "cliente_celular": "55551234",
        "cliente_email": "user@example.com",  (optional if celular provided)
        "descripcion": "Test payment Q5",
        "cliente_nombre": "Juan Perez"
    }
    """
    data = request.data

    # Validate required fields
    monto = data.get('monto')
    referencia = data.get('referencia')
    horas_vigencia = data.get('horas_vigencia', 24)
    cliente_celular = data.get('cliente_celular')
    cliente_email = data.get('cliente_email')
    descripcion = data.get('descripcion', '')
    cliente_nombre = data.get('cliente_nombre', '')

    if not monto:
        return Response(
            {'error': 'monto is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate transaction amount against limits (ISO 27001 A.14)
    is_valid, error_msg = PAQTransactionSecurity.validate_transaction_amount(
        float(monto),
        user_role=getattr(request.user, 'role', 'USER')
    )
    if not is_valid:
        log_security_event(
            event_type=SecurityEventType.PAQ_PAYMENT_FAILURE,
            request=request,
            action="Amount validation failed",
            outcome="invalid_amount",
            details={"error": error_msg, "attempted_amount": float(monto)},
            risk_level="medium"
        )
        return Response(
            {'error': error_msg},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not referencia:
        return Response(
            {'error': 'referencia is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not cliente_celular and not cliente_email:
        return Response(
            {'error': 'cliente_celular or cliente_email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Call PAQ Wallet service
    result = paq_wallet_service.emite_token(
        monto=Decimal(str(monto)),
        referencia=referencia,
        horas_vigencia=int(horas_vigencia),
        cliente_celular=cliente_celular,
        cliente_email=cliente_email,
        descripcion=descripcion,
        cliente_nombre=cliente_nombre
    )

    if result['success']:
        # Save transaction record with integrity hash - ATOMIC operation
        from django.utils import timezone
        from django.db import transaction

        with transaction.atomic():
            tx = WalletTransaction.objects.create(
                user=request.user,
                transaction_type='PAYMENT',
                amount=Decimal(str(monto)),
                currency='GTQ',
                reference_number=referencia,
                external_transaction_id=str(result.get('transaccion', '')),
                status='PENDING',
                status_message=descripcion
            )

            # Log successful token generation
            PAQTransactionSecurity.log_transaction(
                request=request,
                transaction_type="token_generation",
                wallet_id=cliente_celular or cliente_email,
                amount=float(monto),
                reference=referencia,
                status="success",
                paq_response=result
            )
    else:
        # Log failed token generation
        log_security_event(
            event_type=SecurityEventType.PAQ_PAYMENT_FAILURE,
            request=request,
            action="Token generation failed",
            outcome="paq_error",
            details={"paq_code": result.get('codret')},
            risk_level="medium"
        )

    return Response(result)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def check_token_status(request):
    """
    Check status of PAYPAQ tokens (consulta_tokens)

    GET /api/wallet/check-token/?transaccion=12345
    GET /api/wallet/check-token/?referencia=TEST-001

    Or POST with body:
    {
        "transaccion": 12345,
        "fecha_del": "2025-01-01",
        "fecha_al": "2025-01-31",
        "cliente_celular": "55551234",
        "referencia": "TEST-001"
    }
    """
    if request.method == 'GET':
        transaccion = request.query_params.get('transaccion')
        referencia = request.query_params.get('referencia')

        if transaccion:
            result = paq_wallet_service.get_token_status(int(transaccion))
        elif referencia:
            result = paq_wallet_service.check_payment_status(referencia)
        else:
            return Response(
                {'error': 'transaccion or referencia query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        data = request.data
        result = paq_wallet_service.consulta_tokens(
            transaccion=data.get('transaccion'),
            fecha_del=data.get('fecha_del'),
            fecha_al=data.get('fecha_al'),
            cliente_celular=data.get('cliente_celular'),
            cliente_email=data.get('cliente_email'),
            referencia=data.get('referencia')
        )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_paq_transaction("payment")
def process_paqgo_payment(request):
    """
    Process payment using PAQ-GO (PAQgo)
    Customer enters their PAYPAQ token and phone to complete payment.

    ISO 27001 Controls:
    - A.9.4.1: Secure log-on procedures
    - A.10.1.1: Cryptographic controls for transaction integrity
    - A.12.4.1: Event logging for all transactions

    POST /api/wallet/paqgo/

    Body:
    {
        "token": "AB12C",
        "celular": "55551234"
    }
    """
    data = request.data

    token = data.get('token')
    celular = data.get('celular')

    if not token:
        log_security_event(
            event_type=SecurityEventType.PAQ_PAYMENT_FAILURE,
            request=request,
            action="Payment validation failed",
            outcome="invalid_input",
            details={"error": "token missing"},
            risk_level="low"
        )
        return Response(
            {'error': 'token is required (5-character PAYPAQ code)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not celular:
        log_security_event(
            event_type=SecurityEventType.PAQ_PAYMENT_FAILURE,
            request=request,
            action="Payment validation failed",
            outcome="invalid_input",
            details={"error": "celular missing"},
            risk_level="low"
        )
        return Response(
            {'error': 'celular is required (8-digit phone number)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate secure transaction reference for audit trail
    tx_reference = PAQTransactionSecurity.generate_transaction_reference()

    # Call PAQ Wallet service
    result = paq_wallet_service.paqgo_payment(
        token=token,
        celular=celular
    )

    # Log transaction with masked sensitive data
    PAQTransactionSecurity.log_transaction(
        request=request,
        transaction_type="payment",
        wallet_id=celular,  # Phone used as wallet identifier
        amount=0.0,  # Amount not available at this stage
        reference=tx_reference,
        status="success" if result['success'] else "failure",
        paq_response=result
    )

    # Update transaction status if we can find it
    if result['success']:
        # Try to update the transaction record
        WalletTransaction.objects.filter(
            user=request.user,
            status='PENDING'
        ).update(status='COMPLETED')

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_payment_flow(request):
    """
    Test the complete PAQ-GO payment flow with a small amount.
    This is a convenience endpoint for testing.

    POST /api/wallet/test-flow/

    Body:
    {
        "monto": 5.00,
        "celular": "55551234",
        "email": "user@example.com",
        "nombre": "Juan Perez"
    }

    Returns the generated token info. Customer must then:
    1. Wait for SMS with PAYPAQ code
    2. Call POST /api/wallet/paqgo/ with the code
    """
    data = request.data
    user = request.user

    monto = data.get('monto', 5.00)
    celular = data.get('celular')
    email = data.get('email', user.email)
    nombre = data.get('nombre', user.get_full_name() if hasattr(user, 'get_full_name') else '')

    if not celular and not email:
        return Response(
            {'error': 'celular or email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate unique reference
    import uuid
    referencia = f'TEST-{uuid.uuid4().hex[:8].upper()}'

    # Step 1: Generate token
    result = paq_wallet_service.emite_token(
        monto=Decimal(str(monto)),
        referencia=referencia,
        horas_vigencia=24,
        cliente_celular=celular,
        cliente_email=email,
        descripcion=f'Test payment Q{monto}',
        cliente_nombre=nombre
    )

    if result['success']:
        # Save transaction
        WalletTransaction.objects.create(
            user=user,
            transaction_type='PAYMENT',
            amount=Decimal(str(monto)),
            currency='GTQ',
            reference_number=referencia,
            external_transaction_id=str(result.get('transaccion', '')),
            status='PENDING',
            status_message=f'Test payment Q{monto}'
        )

        return Response({
            'success': True,
            'message': 'Token generated successfully',
            'referencia': referencia,
            'transaccion': result.get('transaccion'),
            'token': result.get('token'),
            'monto': float(monto),
            'currency': 'GTQ',
            'next_steps': [
                '1. Customer receives SMS with 5-character PAYPAQ code',
                '2. Customer enters code in app',
                f'3. Call POST /api/wallet/paqgo/ with token and celular',
                f'4. Check status with GET /api/wallet/check-token/?referencia={referencia}'
            ]
        })
    else:
        return Response({
            'success': False,
            'error': result.get('mensaje', 'Failed to generate token'),
            'codret': result.get('codret')
        }, status=status.HTTP_400_BAD_REQUEST)
