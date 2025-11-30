"""
PAQ Wallet Single Sign-On Authentication

Allows users to login to SegurifAI using their PAQ Wallet credentials.
"""
import logging
import requests
from typing import Optional, Dict, Any

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
logger = logging.getLogger(__name__)

# PAQ Wallet API Configuration - NO FALLBACK DEFAULTS (must be configured)
from decouple import config

PAQ_AUTH_URL = config('PAQ_AUTH_URL', default='https://www.paq.com.gt/paqpayws/emite.asmx')
PAQ_ID_CODE = config('PAQ_WALLET_ID_CODE', default='')
PAQ_USER = config('PAQ_WALLET_USER', default='')
PAQ_PASSWORD = config('PAQ_WALLET_PASSWORD', default='')
PAQ_OTP_TEST_MODE = config('PAQ_OTP_TEST_MODE', default=False, cast=bool)

# Validate credentials are configured in production
if not all([PAQ_ID_CODE, PAQ_USER, PAQ_PASSWORD]) and not settings.DEBUG:
    logger.error('SECURITY: PAQ credentials not configured in production!')
    raise ValueError('PAQ_WALLET_ID_CODE, PAQ_WALLET_USER, and PAQ_WALLET_PASSWORD must be configured')


class PAQAuthService:
    """
    Service for authenticating users via PAQ Wallet.

    PAQ Wallet authentication flow (when embedded in PAQ app):
    1. User is already authenticated in PAQ Wallet app
    2. User accesses SegurifAI from within PAQ app
    3. System validates phone number exists in PAQ Wallet
    4. Create/update SegurifAI account and return JWT tokens
    """

    @classmethod
    def verify_paq_wallet_exists(cls, phone_number: str) -> Dict[str, Any]:
        """
        Verify that a phone number has a registered PAQ Wallet.

        Uses PAQ API to check if the phone number is registered.

        Args:
            phone_number: 8-digit Guatemala phone number

        Returns:
            Dictionary with verification result
        """
        import xml.etree.ElementTree as ET

        phone = phone_number.strip().replace('-', '').replace(' ', '').replace('+502', '')

        # In test/dev mode, allow specific test numbers
        if settings.DEBUG:
            # Allow test phone numbers
            TEST_PHONES = ['30082653', '12345678', '99999999']
            if phone in TEST_PHONES:
                logger.info(f'Test mode: allowing phone {phone}')
                return {'success': True, 'verified': True, 'is_test': True}

        try:
            # Use PAQ consulta_cliente endpoint to verify wallet exists
            soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:paq="http://www.paq.com.gt/paqpay">
    <soap:Body>
        <paq:consulta_cliente>
            <paq:id_code>{PAQ_ID_CODE}</paq:id_code>
            <paq:user>{PAQ_USER}</paq:user>
            <paq:password>{PAQ_PASSWORD}</paq:password>
            <paq:celular>{phone}</paq:celular>
        </paq:consulta_cliente>
    </soap:Body>
</soap:Envelope>'''

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://www.paq.com.gt/paqpay/consulta_cliente'
            }

            logger.info(f'Verifying PAQ wallet for phone {phone}...')

            response = requests.post(
                PAQ_AUTH_URL,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.text)
                    namespaces = {
                        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                        'paq': 'http://www.paq.com.gt/paqpay'
                    }

                    result = root.find('.//paq:consulta_clienteResult', namespaces)
                    if result is not None:
                        result_text = result.text.upper() if result.text else ''
                        if result_text in ['OK', 'SUCCESS', 'TRUE', '1', 'ACTIVO']:
                            logger.info(f'PAQ wallet verified for phone {phone}')
                            return {'success': True, 'verified': True}
                        elif 'NO ENCONTRADO' in result_text or 'NOT FOUND' in result_text:
                            logger.warning(f'PAQ wallet not found for phone {phone}')
                            return {
                                'success': False,
                                'verified': False,
                                'error': 'Este número no tiene una cuenta PAQ Wallet registrada.',
                                'error_code': 'WALLET_NOT_FOUND'
                            }

                    # If we can't determine status, allow in dev mode
                    if settings.DEBUG:
                        logger.warning(f'Could not verify PAQ status for {phone}, allowing in dev mode')
                        return {'success': True, 'verified': True, 'is_test': True}

                    return {
                        'success': False,
                        'error': 'No se pudo verificar la cuenta PAQ',
                        'error_code': 'VERIFICATION_FAILED'
                    }

                except ET.ParseError:
                    if settings.DEBUG:
                        return {'success': True, 'verified': True, 'is_test': True}
                    return {
                        'success': False,
                        'error': 'Error al verificar cuenta PAQ',
                        'error_code': 'PARSE_ERROR'
                    }
            else:
                if settings.DEBUG:
                    logger.warning(f'PAQ API error {response.status_code}, allowing in dev mode')
                    return {'success': True, 'verified': True, 'is_test': True}

                return {
                    'success': False,
                    'error': 'Error de conexión con PAQ',
                    'error_code': 'CONNECTION_ERROR'
                }

        except requests.RequestException as e:
            logger.error(f'PAQ verification error: {e}')
            if settings.DEBUG:
                return {'success': True, 'verified': True, 'is_test': True}

            return {
                'success': False,
                'error': 'No se pudo conectar con PAQ Wallet',
                'error_code': 'CONNECTION_ERROR'
            }

    @classmethod
    def authenticate_by_phone(cls, phone_number: str) -> Dict[str, Any]:
        """
        Authenticate PAQ user with just phone number (no OTP).

        Used when SegurifAI is embedded in PAQ Wallet app, where user
        is already authenticated by PAQ.

        Args:
            phone_number: 8-digit Guatemala phone number

        Returns:
            Dictionary with success status, user data, and JWT tokens
        """
        # Validate phone number format
        phone = phone_number.strip().replace('-', '').replace(' ', '').replace('+502', '')
        if len(phone) != 8 or not phone.isdigit():
            return {
                'success': False,
                'error': 'Número de teléfono inválido. Debe ser 8 dígitos.',
                'error_code': 'INVALID_PHONE'
            }

        # Verify PAQ wallet exists for this phone number
        wallet_check = cls.verify_paq_wallet_exists(phone)
        if not wallet_check.get('success'):
            return wallet_check

        # Build PAQ user data
        paq_user_data = {
            'paq_wallet_id': f'PAQ-{phone}',
            'phone': phone,
            'name': None,
            'email': None,
            'verified': True
        }

        # Create or authenticate user
        try:
            result = cls.authenticate_or_create_user(paq_user_data)
            logger.info(f'PAQ phone authentication successful for {phone}')
            return result
        except Exception as e:
            logger.error(f'PAQ phone authentication failed: {e}')
            return {
                'success': False,
                'error': 'Error al autenticar con PAQ Wallet',
                'error_code': 'AUTH_ERROR'
            }

    @classmethod
    def request_otp(cls, phone_number: str) -> Dict[str, Any]:
        """
        Request OTP to be sent to user's PAQ Wallet phone.

        Args:
            phone_number: 8-digit Guatemala phone number

        Returns:
            Dictionary with success status and transaction ID
        """
        import xml.etree.ElementTree as ET

        # Validate phone number format
        phone = phone_number.strip().replace('-', '').replace(' ', '').replace('+502', '')
        if len(phone) != 8 or not phone.isdigit():
            return {
                'success': False,
                'error': 'Numero de telefono invalido. Debe ser 8 digitos.',
                'error_code': 'INVALID_PHONE'
            }

        try:
            # Build SOAP request for OTP
            soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:paq="http://www.paq.com.gt/paqpay">
    <soap:Body>
        <paq:solicita_otp>
            <paq:id_code>{PAQ_ID_CODE}</paq:id_code>
            <paq:user>{PAQ_USER}</paq:user>
            <paq:password>{PAQ_PASSWORD}</paq:password>
            <paq:celular>{phone}</paq:celular>
            <paq:motivo>Login SegurifAI</paq:motivo>
        </paq:solicita_otp>
    </soap:Body>
</soap:Envelope>'''

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://www.paq.com.gt/paqpay/solicita_otp'
            }

            logger.info(f'Requesting OTP from PAQ for phone {phone}...')

            response = requests.post(
                PAQ_AUTH_URL,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=30
            )

            logger.info(f'PAQ OTP response status: {response.status_code}')
            logger.debug(f'PAQ OTP response body: {response.text[:500]}')

            if response.status_code == 200:
                # Parse SOAP response
                try:
                    root = ET.fromstring(response.text)
                    # Navigate SOAP response structure
                    namespaces = {
                        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                        'paq': 'http://www.paq.com.gt/paqpay'
                    }

                    # Extract response elements
                    result = root.find('.//paq:solicita_otpResult', namespaces)
                    if result is not None:
                        transaction_id = result.text
                        logger.info(f'OTP requested successfully for phone {phone}, transaction: {transaction_id}')

                        return {
                            'success': True,
                            'message': 'Codigo OTP enviado a tu telefono',
                            'transaction_id': transaction_id,
                            'phone': phone[-4:]  # Last 4 digits for display
                        }
                    else:
                        logger.error(f'Could not parse PAQ OTP response')
                        return {
                            'success': False,
                            'error': 'Error al procesar respuesta de PAQ',
                            'error_code': 'PARSE_ERROR'
                        }
                except ET.ParseError as e:
                    logger.error(f'XML parse error: {e}')
                    return {
                        'success': False,
                        'error': 'Error al procesar respuesta de PAQ',
                        'error_code': 'PARSE_ERROR'
                    }
            else:
                logger.error(f'PAQ OTP request failed: {response.status_code}')
                return {
                    'success': False,
                    'error': 'Error al solicitar OTP. Intente de nuevo.',
                    'error_code': 'PAQ_ERROR'
                }

        except requests.RequestException as e:
            logger.error(f'PAQ OTP request exception: {e}')
            return {
                'success': False,
                'error': 'No se pudo conectar con PAQ Wallet',
                'error_code': 'CONNECTION_ERROR'
            }

    @classmethod
    def verify_otp(cls, phone_number: str, otp_code: str, transaction_id: str) -> Dict[str, Any]:
        """
        Verify OTP code with PAQ Wallet.

        Args:
            phone_number: User's phone number
            otp_code: OTP code entered by user
            transaction_id: Transaction ID from OTP request

        Returns:
            Dictionary with verification result and user data
        """
        import xml.etree.ElementTree as ET

        phone = phone_number.strip().replace('-', '').replace(' ', '').replace('+502', '')

        try:
            # Build SOAP request for OTP verification
            soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:paq="http://www.paq.com.gt/paqpay">
    <soap:Body>
        <paq:valida_otp>
            <paq:id_code>{PAQ_ID_CODE}</paq:id_code>
            <paq:user>{PAQ_USER}</paq:user>
            <paq:password>{PAQ_PASSWORD}</paq:password>
            <paq:celular>{phone}</paq:celular>
            <paq:otp>{otp_code}</paq:otp>
            <paq:transaccion>{transaction_id}</paq:transaccion>
        </paq:valida_otp>
    </soap:Body>
</soap:Envelope>'''

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://www.paq.com.gt/paqpay/valida_otp'
            }

            logger.info(f'Verifying OTP from PAQ for phone {phone}, transaction: {transaction_id}...')

            response = requests.post(
                PAQ_AUTH_URL,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=30
            )

            logger.info(f'PAQ OTP verification response status: {response.status_code}')
            logger.debug(f'PAQ OTP verification response body: {response.text[:500]}')

            if response.status_code == 200:
                # Parse SOAP response
                try:
                    root = ET.fromstring(response.text)
                    # Navigate SOAP response structure
                    namespaces = {
                        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                        'paq': 'http://www.paq.com.gt/paqpay'
                    }

                    # Extract response elements
                    result = root.find('.//paq:valida_otpResult', namespaces)
                    if result is not None and result.text.upper() in ['OK', 'SUCCESS', 'TRUE', '1']:
                        # OTP verified successfully
                        paq_user_data = cls._get_paq_user_info(phone)
                        logger.info(f'OTP verified successfully for phone {phone}')

                        return {
                            'success': True,
                            'verified': True,
                            'paq_user': paq_user_data
                        }
                    else:
                        logger.warning(f'OTP verification failed for phone {phone}')
                        return {
                            'success': False,
                            'error': 'Codigo OTP invalido',
                            'error_code': 'INVALID_OTP'
                        }
                except ET.ParseError as e:
                    logger.error(f'XML parse error during OTP verification: {e}')
                    return {
                        'success': False,
                        'error': 'Error al procesar respuesta de PAQ',
                        'error_code': 'PARSE_ERROR'
                    }
            else:
                logger.error(f'PAQ OTP verification failed: {response.status_code}')
                return {
                    'success': False,
                    'error': 'Error al verificar OTP',
                    'error_code': 'VERIFICATION_ERROR'
                }

        except requests.RequestException as e:
            logger.error(f'PAQ OTP verification exception: {e}')
            return {
                'success': False,
                'error': 'Error al verificar OTP',
                'error_code': 'VERIFICATION_ERROR'
            }

    @classmethod
    def _get_paq_user_info(cls, phone: str) -> Dict[str, Any]:
        """
        Get user information from PAQ Wallet.

        In production, this would call PAQ API to get user details.
        """
        # Simulated PAQ user data
        # In production, call PAQ API endpoint to get actual user info
        return {
            'paq_wallet_id': f'PAQ-{phone}',
            'phone': phone,
            'name': None,  # PAQ may provide this
            'email': None,  # PAQ may provide this
            'verified': True
        }

    @classmethod
    def authenticate_or_create_user(cls, paq_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find existing user or create new one based on PAQ data.

        Args:
            paq_user_data: User data from PAQ Wallet

        Returns:
            Dictionary with user info and JWT tokens
        """
        phone = paq_user_data.get('phone')
        paq_wallet_id = paq_user_data.get('paq_wallet_id')

        # Try to find existing user by phone or PAQ wallet ID
        user = User.objects.filter(phone_number=phone).first()

        if not user:
            user = User.objects.filter(paq_wallet_id=paq_wallet_id).first()

        if user:
            # Update PAQ wallet ID if not set
            if not user.paq_wallet_id:
                user.paq_wallet_id = paq_wallet_id
                user.save()

            # Mark phone as verified since PAQ verified it
            if not user.is_phone_verified:
                user.is_phone_verified = True
                user.save()

            is_new_user = False
        else:
            # Create new user from PAQ data
            user = User.objects.create_user(
                email=f'{phone}@paq.segurifai.com',  # Placeholder email
                phone_number=phone,
                paq_wallet_id=paq_wallet_id,
                is_phone_verified=True,
                role='USER'
            )

            # Set name if provided by PAQ
            if paq_user_data.get('name'):
                names = paq_user_data['name'].split(' ', 1)
                user.first_name = names[0]
                if len(names) > 1:
                    user.last_name = names[1]
                user.save()

            is_new_user = True
            logger.info(f'Created new user from PAQ login: {phone}')

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return {
            'success': True,
            'is_new_user': is_new_user,
            'user': {
                'id': user.id,
                'email': user.email,
                'phone': user.phone_number,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'paq_wallet_id': user.paq_wallet_id,
                'role': user.role,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }


# Convenience functions
request_paq_otp = PAQAuthService.request_otp
verify_paq_otp = PAQAuthService.verify_otp
paq_login = PAQAuthService.authenticate_or_create_user
