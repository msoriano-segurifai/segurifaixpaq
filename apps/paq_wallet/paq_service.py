"""
PAQ Wallet Payment Integration Service

Implements the PAQ-GO payment flow:
1. emite_token - Generate PAYPAQ code and send SMS to customer
2. PAQgo - Process payment with the PAYPAQ code

API Endpoints:
- Token Generation: https://www.paq.com.gt/paqpayws/emite.asmx
- Payment Processing: https://www.paq.com.gt/paqgo/paqgo.asmx

Note: These are ASMX SOAP 1.2 web services. Must use SOAP envelope format.
"""
import logging
import requests
import random
import string
import re
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any
from decimal import Decimal
from decouple import config
from django.conf import settings

logger = logging.getLogger(__name__)


def parse_soap_response(response_text: str) -> dict:
    """
    Parse PAQ SOAP 1.2 response which contains JSON inside SOAP envelope.
    """
    # Try parsing as SOAP XML first
    try:
        root = ET.fromstring(response_text)

        # Look for Result element with JSON content (SOAP response pattern)
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag_name.endswith('Result') and elem.text:
                text = elem.text.strip()
                if text.startswith('{'):
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        pass

        # Look for common response fields directly in XML
        result = {}
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1].lower() if '}' in elem.tag else elem.tag.lower()
            text = elem.text.strip() if elem.text else ''

            if tag_name == 'codret' and text:
                result['codret'] = int(text) if text.lstrip('-').isdigit() else text
            elif tag_name == 'mensaje' and text:
                result['mensaje'] = text
            elif tag_name == 'token' and text:
                result['token'] = text
            elif tag_name == 'transaccion' and text:
                result['transaccion'] = int(text) if text.isdigit() else text
            elif tag_name == 'autorizacion' and text:
                result['autorizacion'] = text

        if result:
            return result

    except ET.ParseError as e:
        logger.warning(f'XML parse error: {e}')

    # Try direct JSON as fallback
    try:
        return json.loads(response_text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Return raw if we can't parse
    logger.warning(f'Could not parse response: {response_text[:200]}')
    return {'raw_response': response_text, 'codret': -999}


# Keep old name for backward compatibility
parse_paq_response = parse_soap_response

# PAQ API Configuration
PAQ_EMITE_URL = config('PAQ_WALLET_EMITE_URL', default='https://www.paq.com.gt/paqpayws/emite.asmx')
PAQ_PAQGO_URL = config('PAQ_WALLET_PAQGO_URL', default='https://www.paq.com.gt/paqgo/paqgo.asmx')
PAQ_USER = config('PAQ_WALLET_USER', default='')
PAQ_PASSWORD = config('PAQ_WALLET_PASSWORD', default='')
PAQ_REP_ID = config('PAQ_WALLET_ID_CODE', default='')

# Test phone number for PAQ testing (Q5 per transaction) and test mode toggle
PAQ_TEST_PHONE = getattr(settings, 'PAQ_TEST_PHONE', config('PAQ_TEST_PHONE', default='30082653'))
PAQ_TEST_PRICE = getattr(settings, 'PAQ_TEST_PRICE', config('PAQ_TEST_PRICE', default=Decimal('5.00'), cast=Decimal))
# PAQ OTP Test Mode: When True, generates fake tokens; When False, calls real PAQ API
PAQ_OTP_TEST_MODE = getattr(settings, 'PAQ_TEST_MODE', config('PAQ_OTP_TEST_MODE', default='False', cast=bool))


class PAQPaymentService:
    """
    PAQ Wallet Payment Service implementing the PAQ-GO flow.

    Flow:
    1. Merchant calls emite_token() to generate PAYPAQ code
    2. PAQ sends SMS to customer with the code
    3. Customer enters the code in the app
    4. Merchant calls process_payment() with the code to charge customer
    """

    @classmethod
    def emit_token(
        cls,
        phone_number: str,
        amount: Decimal,
        reference: str,
        description: str = '',
        customer_name: str = '',
        customer_email: str = '',
        validity_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate a PAYPAQ token and send it via SMS to the customer.

        Args:
            phone_number: Customer's 8-digit Guatemala phone number
            amount: Amount in GTQ (Quetzales)
            reference: Order/subscription reference for tracking
            description: Short description of the charge
            customer_name: Customer's name (optional)
            customer_email: Customer's email (optional)
            validity_hours: Token validity in hours (default 24)

        Returns:
            Dict with success status, token code, and transaction ID
        """
        # Normalize phone number - remove all non-digits first, then handle country code
        phone = ''.join(c for c in phone_number if c.isdigit())
        # Remove Guatemala country code (502) if present
        if phone.startswith('502') and len(phone) > 8:
            phone = phone[3:]

        if len(phone) != 8 or not phone.isdigit():
            return {
                'success': False,
                'error': 'Número de teléfono inválido. Debe ser 8 dígitos.',
                'error_code': 'INVALID_PHONE'
            }

        # TEST MODE: Only when PAQ_OTP_TEST_MODE=True AND phone is test phone
        # When PAQ_OTP_TEST_MODE=False, always use real PAQ API
        if PAQ_OTP_TEST_MODE and phone == PAQ_TEST_PHONE:
            test_token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            test_transaction_id = random.randint(100000, 999999)
            logger.info(f'[TEST] Generated mock PAYPAQ token: {test_token} for test phone {phone}')
            return {
                'success': True,
                'message': f'Código PAYPAQ enviado a tu teléfono. Código de prueba: {test_token}',
                'token': test_token,
                'transaction_id': test_transaction_id,
                'phone_last4': phone[-4:],
                'amount': float(amount),
                'test_mode': True
            }

        try:
            # Truncate fields to PAQ's expected lengths to avoid SQL truncation errors
            safe_reference = reference[:20] if reference else ''
            safe_description = (description or f'Pago SegurifAI')[:50]
            safe_name = (customer_name or '')[:50]
            safe_email = (customer_email or '')[:100]

            # Build SOAP 1.2 envelope for emite_token
            soap_body = '''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" xmlns:paq="http://www.paq.com.gt/paqpay/emite_token">
  <soap12:Body>
    <paq:emite_token>
      <paq:usuario>{usuario}</paq:usuario>
      <paq:password>{password}</paq:password>
      <paq:rep_id>{rep_id}</paq:rep_id>
      <paq:cliente_celular>{celular}</paq:cliente_celular>
      <paq:cliente_email>{email}</paq:cliente_email>
      <paq:monto>{monto}</paq:monto>
      <paq:referencia>{referencia}</paq:referencia>
      <paq:descripcion>{descripcion}</paq:descripcion>
      <paq:cliente_nombre>{nombre}</paq:cliente_nombre>
      <paq:horas_vigencia>{horas}</paq:horas_vigencia>
    </paq:emite_token>
  </soap12:Body>
</soap12:Envelope>'''.format(
                usuario=PAQ_USER,
                password=PAQ_PASSWORD,
                rep_id=PAQ_REP_ID,
                celular=phone,
                email=safe_email,
                monto=str(int(amount)) if float(amount) == int(amount) else str(float(amount)),
                referencia=safe_reference,
                descripcion=safe_description,
                nombre=safe_name,
                horas=str(validity_hours)
            )

            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8'
            }

            logger.info(f'Emitting PAYPAQ token for phone {phone}, amount Q{amount}')

            # Call PAQ emite_token endpoint with SOAP 1.2
            response = requests.post(
                PAQ_EMITE_URL,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=30
            )

            logger.info(f'PAQ emite_token response status: {response.status_code}')
            logger.debug(f'PAQ emite_token response: {response.text[:500]}')

            if response.status_code == 200:
                # Parse SOAP response
                data = parse_soap_response(response.text)
                logger.info(f'PAQ emite_token parsed data: {data}')

                if data.get('codret') == 0 or str(data.get('codret')) == '0':
                    token_code = data.get('token', '')
                    transaction_id = data.get('transaccion', 0)

                    logger.info(f'PAYPAQ token emitted: {token_code}, transaction: {transaction_id}')

                    return {
                        'success': True,
                        'message': 'Código PAYPAQ enviado a tu teléfono',
                        'token': token_code,
                        'transaction_id': transaction_id,
                        'phone_last4': phone[-4:],
                        'amount': float(amount)
                    }
                else:
                    error_msg = data.get('mensaje', data.get('raw_response', 'Error al generar código PAYPAQ'))
                    logger.error(f'PAQ emite_token error: {error_msg}')
                    return {
                        'success': False,
                        'error': error_msg,
                        'error_code': f'PAQ_ERROR_{data.get("codret", "UNKNOWN")}'
                    }
            else:
                logger.error(f'PAQ emite_token HTTP error: {response.status_code}')
                return {
                    'success': False,
                    'error': 'Error de conexión con PAQ Wallet',
                    'error_code': 'HTTP_ERROR'
                }

        except requests.RequestException as e:
            logger.error(f'PAQ emite_token request exception: {e}')
            return {
                'success': False,
                'error': 'No se pudo conectar con PAQ Wallet',
                'error_code': 'CONNECTION_ERROR'
            }

    @classmethod
    def process_payment(cls, token_code: str, phone_number: str) -> Dict[str, Any]:
        """
        Process payment using the PAYPAQ code (PAQ-GO button flow).

        Args:
            token_code: The 5-character PAYPAQ code received via SMS
            phone_number: Customer's phone number associated with PAQ Wallet

        Returns:
            Dict with success status and transaction details
        """
        # Normalize phone and token - remove all non-digits first, then handle country code
        phone = ''.join(c for c in phone_number if c.isdigit())
        if phone.startswith('502') and len(phone) > 8:
            phone = phone[3:]
        token = token_code.strip().upper()

        if len(phone) != 8 or not phone.isdigit():
            return {
                'success': False,
                'error': 'Número de teléfono inválido',
                'error_code': 'INVALID_PHONE'
            }

        if not token or len(token) < 4 or len(token) > 6:
            return {
                'success': False,
                'error': 'Código PAYPAQ inválido',
                'error_code': 'INVALID_TOKEN'
            }

        # TEST MODE: Only when PAQ_OTP_TEST_MODE=True AND phone is test phone
        # When PAQ_OTP_TEST_MODE=False, always use real PAQ API
        if PAQ_OTP_TEST_MODE and phone == PAQ_TEST_PHONE:
            test_transaction_id = random.randint(100000, 999999)
            test_authorization = ''.join(random.choices(string.digits, k=8))
            logger.info(f'[TEST] Simulated PAQ-GO payment for test phone {phone}, token: {token}')
            return {
                'success': True,
                'message': 'Pago realizado con éxito (modo prueba)',
                'transaction_id': test_transaction_id,
                'authorization': test_authorization,
                'test_mode': True
            }

        try:
            # Build SOAP 1.2 envelope for PAQgo
            soap_body = '''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" xmlns:paq="http://tempuri.org/">
  <soap12:Body>
    <paq:PAQgo>
      <paq:usuario>{usuario}</paq:usuario>
      <paq:password>{password}</paq:password>
      <paq:rep_id>{rep_id}</paq:rep_id>
      <paq:token>{token}</paq:token>
      <paq:celular>{celular}</paq:celular>
    </paq:PAQgo>
  </soap12:Body>
</soap12:Envelope>'''.format(
                usuario=PAQ_USER,
                password=PAQ_PASSWORD,
                rep_id=PAQ_REP_ID,
                token=token,
                celular=phone
            )

            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8'
            }

            logger.info(f'Processing PAQ-GO payment: token={token}, phone={phone}')

            # Call PAQ-GO payment endpoint with SOAP 1.2
            response = requests.post(
                PAQ_PAQGO_URL,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=30
            )

            logger.info(f'PAQ-GO response status: {response.status_code}')
            logger.debug(f'PAQ-GO response: {response.text[:500]}')

            if response.status_code == 200:
                # Parse SOAP response
                data = parse_soap_response(response.text)
                logger.info(f'PAQ-GO parsed data: {data}')

                if data.get('codret') == 0 or str(data.get('codret')) == '0':
                    transaction_id = data.get('transaccion', 0)

                    logger.info(f'PAQ-GO payment successful: transaction={transaction_id}')

                    return {
                        'success': True,
                        'message': 'Pago realizado con éxito',
                        'transaction_id': transaction_id,
                        'authorization': data.get('autorizacion', '')
                    }
                else:
                    error_msg = data.get('mensaje', data.get('raw_response', 'Error al procesar pago'))
                    logger.error(f'PAQ-GO payment error: {error_msg}')
                    return {
                        'success': False,
                        'error': error_msg,
                        'error_code': f'PAQ_ERROR_{data.get("codret", "UNKNOWN")}'
                    }
            else:
                logger.error(f'PAQ-GO HTTP error: {response.status_code}')
                return {
                    'success': False,
                    'error': 'Error de conexión con PAQ Wallet',
                    'error_code': 'HTTP_ERROR'
                }

        except requests.RequestException as e:
            logger.error(f'PAQ-GO request exception: {e}')
            return {
                'success': False,
                'error': 'No se pudo conectar con PAQ Wallet',
                'error_code': 'CONNECTION_ERROR'
            }

    @classmethod
    def check_token_status(cls, transaction_id: int = None, reference: str = None) -> Dict[str, Any]:
        """
        Check the status of a PAYPAQ token.

        Args:
            transaction_id: PAQ transaction ID
            reference: Order reference

        Returns:
            Dict with token status (0=Processing, 1=Emitted, 2=Paid, 3=Cancelled, 4=Expired)
        """
        try:
            params = {
                'usuario': PAQ_USER,
                'password': PAQ_PASSWORD,
                'rep_id': PAQ_REP_ID,
            }

            if transaction_id:
                params['transaccion'] = transaction_id
            elif reference:
                params['referencia'] = reference
            else:
                return {
                    'success': False,
                    'error': 'Debe especificar transaccion o referencia',
                    'error_code': 'MISSING_FILTER'
                }

            response = requests.get(
                f'{PAQ_EMITE_URL}/consulta_tokens',
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('codret') == 0 or str(data.get('codret')) == '0':
                    tokens = data.get('Ctoken', [])
                    if tokens:
                        token_data = tokens[0]
                        status_map = {
                            0: 'EN_PROCESO',
                            1: 'EMITIDO',
                            2: 'PAGADO',
                            3: 'ANULADO',
                            4: 'VENCIDO'
                        }
                        return {
                            'success': True,
                            'status': status_map.get(token_data.get('status'), 'DESCONOCIDO'),
                            'status_code': token_data.get('status'),
                            'token': token_data.get('token'),
                            'amount': token_data.get('monto'),
                            'date_issued': token_data.get('fecha_emitido'),
                            'date_paid': token_data.get('fecha_cobrado'),
                            'authorization': token_data.get('autorizacion_cobra')
                        }
                    return {
                        'success': False,
                        'error': 'Token no encontrado',
                        'error_code': 'NOT_FOUND'
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('mensaje', 'Error al consultar token'),
                        'error_code': 'PAQ_ERROR'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Error de conexión',
                    'error_code': 'HTTP_ERROR'
                }

        except requests.RequestException as e:
            logger.error(f'PAQ consulta_tokens exception: {e}')
            return {
                'success': False,
                'error': 'No se pudo conectar con PAQ',
                'error_code': 'CONNECTION_ERROR'
            }


# Convenience functions
emit_paypaq_token = PAQPaymentService.emit_token
process_paq_payment = PAQPaymentService.process_payment
check_paq_token = PAQPaymentService.check_token_status
