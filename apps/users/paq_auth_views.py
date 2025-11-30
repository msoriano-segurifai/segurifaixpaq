"""
PAQ Wallet SSO Authentication Views

All SegurifAI access is through PAQ app - no standalone registration.
PAQ users access SegurifAI via a button in PAQ app that sends a signed token.
"""
import hmac
import hashlib
import time
import json
import base64
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .paq_auth import PAQAuthService


# PAQ SSO Configuration - from Django settings
PAQ_SSO_SECRET = getattr(settings, 'PAQ_SSO_SECRET', 'paq-segurifai-dev-secret-change-in-production')
PAQ_SSO_TOKEN_EXPIRY = getattr(settings, 'PAQ_SSO_TOKEN_EXPIRY', 300)  # 5 minutes default


def verify_paq_sso_token(token: str) -> dict:
    """
    Verify a PAQ SSO token signed by PAQ app.

    Token format: base64(json_payload).signature
    Payload: {"phone": "30082653", "paq_id": "PAQ-123", "name": "Juan", "ts": 1234567890}
    Signature: HMAC-SHA256(payload, PAQ_SSO_SECRET)
    """
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return {'valid': False, 'error': 'Invalid token format'}

        payload_b64, signature = parts

        # Verify signature
        expected_sig = hmac.new(
            PAQ_SSO_SECRET.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return {'valid': False, 'error': 'Invalid signature'}

        # Decode payload
        payload_json = base64.urlsafe_b64decode(payload_b64 + '==').decode()
        payload = json.loads(payload_json)

        # Check expiry
        ts = payload.get('ts', 0)
        if time.time() - ts > PAQ_SSO_TOKEN_EXPIRY:
            return {'valid': False, 'error': 'Token expired'}

        return {'valid': True, 'payload': payload}

    except Exception as e:
        return {'valid': False, 'error': str(e)}


@api_view(['POST'])
@permission_classes([AllowAny])
def paq_sso_authenticate(request):
    """
    PAQ App SSO Authentication - Main entry point for PAQ users.

    Called when user clicks "SegurifAI" button in PAQ app.
    PAQ app sends a signed token with user data.

    POST /api/users/auth/paq/sso/

    Body:
    {
        "token": "base64payload.signature"
    }

    The token payload contains:
    {
        "phone": "30082653",
        "paq_id": "PAQ-123456",
        "name": "Juan Garcia",
        "email": "juan@email.com",  // optional
        "ts": 1700000000  // Unix timestamp
    }

    Returns:
    {
        "success": true,
        "user": {
            "id": 1,
            "phone": "30082653",
            "name": "Juan Garcia",
            "paq_wallet_id": "PAQ-123456"
        },
        "tokens": {
            "access": "eyJ...",
            "refresh": "eyJ..."
        },
        "is_new_user": false
    }
    """
    token = request.data.get('token')

    if not token:
        return Response(
            {'error': 'token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify the token
    result = verify_paq_sso_token(token)

    if not result['valid']:
        return Response(
            {'error': result['error']},
            status=status.HTTP_401_UNAUTHORIZED
        )

    payload = result['payload']

    # Build PAQ user data
    paq_user_data = {
        'paq_wallet_id': payload.get('paq_id', f"PAQ-{payload.get('phone')}"),
        'phone': payload.get('phone'),
        'name': payload.get('name', ''),
        'email': payload.get('email'),
        'verified': True
    }

    # Create or authenticate user
    auth_result = PAQAuthService.authenticate_or_create_user(paq_user_data)

    return Response(auth_result)


@api_view(['GET'])
@permission_classes([AllowAny])
def paq_sso_redirect(request):
    """
    PAQ SSO via URL redirect (for web links).

    GET /api/users/auth/paq/sso/?token=base64payload.signature

    This endpoint can be used as a redirect URL from PAQ web app.
    Returns HTML that stores tokens and redirects to SegurifAI app.
    """
    token = request.query_params.get('token')

    if not token:
        return Response(
            {'error': 'token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify the token
    result = verify_paq_sso_token(token)

    if not result['valid']:
        return Response(
            {'error': result['error']},
            status=status.HTTP_401_UNAUTHORIZED
        )

    payload = result['payload']

    # Build PAQ user data
    paq_user_data = {
        'paq_wallet_id': payload.get('paq_id', f"PAQ-{payload.get('phone')}"),
        'phone': payload.get('phone'),
        'name': payload.get('name', ''),
        'email': payload.get('email'),
        'verified': True
    }

    # Create or authenticate user
    auth_result = PAQAuthService.authenticate_or_create_user(paq_user_data)

    # Return JSON for mobile/SPA or redirect for web
    return Response(auth_result)


@api_view(['POST'])
@permission_classes([AllowAny])
def paq_request_otp(request):
    """
    Request OTP for PAQ Wallet login.

    POST /api/users/auth/paq/request-otp/

    Body:
    {
        "phone": "30082653"
    }

    Returns:
    {
        "success": true,
        "message": "Codigo OTP enviado a tu telefono",
        "transaction_id": "ABC123...",
        "phone": "2653"
    }
    """
    phone = request.data.get('phone')

    if not phone:
        return Response(
            {'error': 'phone is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = PAQAuthService.request_otp(phone)

    if result['success']:
        return Response(result)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def paq_verify_otp(request):
    """
    Verify OTP and complete PAQ Wallet login.

    POST /api/users/auth/paq/verify-otp/

    Body:
    {
        "phone": "30082653",
        "otp": "123456",
        "transaction_id": "ABC123..."
    }

    Returns:
    {
        "success": true,
        "is_new_user": false,
        "user": {
            "id": 1,
            "email": "user@example.com",
            "phone": "30082653",
            "paq_wallet_id": "PAQ-30082653"
        },
        "tokens": {
            "access": "eyJ...",
            "refresh": "eyJ..."
        }
    }
    """
    phone = request.data.get('phone')
    otp = request.data.get('otp')
    transaction_id = request.data.get('transaction_id')

    if not phone:
        return Response(
            {'error': 'phone is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not otp:
        return Response(
            {'error': 'otp is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not transaction_id:
        return Response(
            {'error': 'transaction_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify OTP with PAQ
    verify_result = PAQAuthService.verify_otp(phone, otp, transaction_id)

    if not verify_result['success']:
        return Response(verify_result, status=status.HTTP_400_BAD_REQUEST)

    # Create or authenticate user
    auth_result = PAQAuthService.authenticate_or_create_user(verify_result['paq_user'])

    return Response(auth_result)


@api_view(['POST'])
@permission_classes([AllowAny])
def paq_phone_login(request):
    """
    PAQ Phone-Only Login - For embedded SegurifAI in PAQ Wallet app.

    When SegurifAI is accessed from within PAQ Wallet app, the user is
    already authenticated by PAQ. This endpoint allows login with just
    the phone number.

    POST /api/users/auth/paq/phone-login/

    Body:
    {
        "phone": "30082653"
    }

    Returns:
    {
        "success": true,
        "is_new_user": false,
        "user": {
            "id": 1,
            "email": "30082653@paq.segurifai.com",
            "phone": "30082653",
            "paq_wallet_id": "PAQ-30082653",
            "role": "USER"
        },
        "tokens": {
            "access": "eyJ...",
            "refresh": "eyJ..."
        }
    }
    """
    phone = request.data.get('phone')

    if not phone:
        return Response(
            {'error': 'phone is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate by phone only
    result = PAQAuthService.authenticate_by_phone(phone)

    if result.get('success'):
        return Response(result)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def paq_quick_login(request):
    """
    Quick login for development/testing - bypasses OTP.

    POST /api/users/auth/paq/quick-login/

    Body:
    {
        "phone": "30082653"
    }

    Note: This endpoint should be disabled in production.
    """
    from django.conf import settings

    if not settings.DEBUG:
        return Response(
            {'error': 'This endpoint is only available in development'},
            status=status.HTTP_403_FORBIDDEN
        )

    phone = request.data.get('phone')

    if not phone:
        return Response(
            {'error': 'phone is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Simulate PAQ user data
    phone = phone.strip().replace('-', '').replace(' ', '')
    paq_user_data = {
        'paq_wallet_id': f'PAQ-{phone}',
        'phone': phone,
        'verified': True
    }

    # Create or authenticate user
    auth_result = PAQAuthService.authenticate_or_create_user(paq_user_data)

    return Response(auth_result)


@api_view(['POST'])
@permission_classes([AllowAny])
def paq_link_account(request):
    """
    Link existing SegurifAI account with PAQ Wallet.

    POST /api/users/auth/paq/link/

    Body:
    {
        "email": "user@example.com",
        "password": "userpassword",
        "paq_phone": "30082653"
    }

    This allows users who already have a SegurifAI account
    to link it with their PAQ Wallet for future SSO logins.
    """
    from django.contrib.auth import authenticate

    email = request.data.get('email')
    password = request.data.get('password')
    paq_phone = request.data.get('paq_phone')

    if not email or not password or not paq_phone:
        return Response(
            {'error': 'email, password, and paq_phone are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate with email/password
    user = authenticate(email=email, password=password)

    if not user:
        return Response(
            {'error': 'Invalid email or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Link PAQ Wallet
    paq_phone = paq_phone.strip().replace('-', '').replace(' ', '')
    paq_wallet_id = f'PAQ-{paq_phone}'

    # Check if this wallet is already linked to another user
    from apps.users.models import User
    existing = User.objects.filter(paq_wallet_id=paq_wallet_id).exclude(id=user.id).first()
    if existing:
        return Response({
            'error': 'Esta cuenta PAQ ya está vinculada a otro usuario',
            'linked_to': existing.email[:3] + '***@***'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already has this wallet linked
    if user.paq_wallet_id == paq_wallet_id:
        return Response({
            'success': True,
            'message': 'Cuenta ya vinculada con PAQ Wallet',
            'user': {
                'id': user.id,
                'email': user.email,
                'phone': user.phone_number,
                'paq_wallet_id': user.paq_wallet_id
            }
        })

    user.paq_wallet_id = paq_wallet_id
    user.phone_number = paq_phone
    user.save()

    return Response({
        'success': True,
        'message': 'Cuenta vinculada con PAQ Wallet exitosamente',
        'user': {
            'id': user.id,
            'email': user.email,
            'phone': user.phone_number,
            'paq_wallet_id': user.paq_wallet_id
        }
    })
