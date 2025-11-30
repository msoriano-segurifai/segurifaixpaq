"""
PAQ Wallet API Integration Service
Official integration with PAQ Wallet (PAQ-GO) for Guatemala

API Documentation:
- Token Generation: https://www.paq.com.gt/paqpayws/emite.asmx
- Payment (PAQ-GO): https://www.paq.com.gt/paqgo/paqgo.asmx

SOAP Web Services - Tested and working as of November 2024
"""
from django.conf import settings
import requests
import logging
import json
import re
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class PAQWalletService:
    """
    Service class for integrating with PAQ Wallet API (PAQ-GO)
    Uses SOAP/XML format for API calls

    Authentication credentials:
    - usuario: POS registered username
    - password: POS registered password
    - rep_id: POS registered ID (ID Code)
    """

    # Token Status Constants
    STATUS_IN_PROCESS = 0
    STATUS_TOKEN_ISSUED = 1
    STATUS_COLLECTED = 2
    STATUS_CANCELLED = 3
    STATUS_EXPIRED = 4

    STATUS_CHOICES = {
        0: 'En proceso',
        1: 'Token emitido',
        2: 'Cobrado',
        3: 'Anulado',
        4: 'Vencido'
    }

    # SOAP Namespaces
    EMITE_TOKEN_NS = 'http://www.paq.com.gt/paqpay/emite_token'
    CONSULTA_TOKENS_NS = 'http://www.paq.com.gt/paqpay/consulta_tokens'
    PAQGO_NS = 'http://tempuri.org/'

    def __init__(self):
        # Token generation and query endpoint
        self.emite_url = getattr(settings, 'PAQ_WALLET_EMITE_URL',
                                  'https://www.paq.com.gt/paqpayws/emite.asmx')
        # Payment endpoint (PAQ-GO)
        self.paqgo_url = getattr(settings, 'PAQ_WALLET_PAQGO_URL',
                                  'https://www.paq.com.gt/paqgo/paqgo.asmx')

        # Credentials - NO FALLBACK DEFAULTS (must be configured in .env)
        from decouple import config
        self.usuario = config('PAQ_WALLET_USER', default='')
        self.password = config('PAQ_WALLET_PASSWORD', default='')
        self.rep_id = config('PAQ_WALLET_ID_CODE', default='')

        # Log warning if credentials missing (will fail on actual API calls)
        if not all([self.usuario, self.password, self.rep_id]):
            logger.warning('PAQ Wallet credentials not fully configured - API calls will fail')

    def _build_soap_envelope(self, method: str, namespace: str, params: Dict) -> str:
        """
        Build a SOAP XML envelope for the request

        Args:
            method: The SOAP method name
            namespace: XML namespace for the method
            params: Parameters as dict

        Returns:
            SOAP XML string
        """
        # Build parameters XML
        params_xml = ''
        for key, value in params.items():
            if value is not None:
                params_xml += f'      <{key}>{value}</{key}>\n'
            else:
                params_xml += f'      <{key}></{key}>\n'

        soap_envelope = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <{method} xmlns="{namespace}">
{params_xml}    </{method}>
  </soap:Body>
</soap:Envelope>'''

        return soap_envelope

    def _parse_soap_response(self, response_text: str, result_element: str) -> Optional[Dict]:
        """
        Parse SOAP XML response and extract JSON result

        Args:
            response_text: Raw SOAP XML response
            result_element: Name of the result element (e.g., 'emite_tokenResult')

        Returns:
            Parsed JSON dict or None
        """
        try:
            # Extract JSON from the result element using regex
            pattern = f'<{result_element}>(.*?)</{result_element}>'
            match = re.search(pattern, response_text, re.DOTALL)

            if match:
                json_str = match.group(1)
                # Unescape XML entities
                json_str = json_str.replace('&quot;', '"').replace('&amp;', '&')
                return json.loads(json_str)

            return None
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f'Error parsing SOAP response: {str(e)}')
            logger.debug(f'Response text: {response_text}')
            return None

    def _make_soap_request(self, url: str, method: str, namespace: str,
                           soap_action: str, params: Dict, result_element: str) -> Optional[Dict]:
        """
        Make a SOAP request to PAQ Wallet API

        Args:
            url: API endpoint URL
            method: SOAP method name
            namespace: XML namespace
            soap_action: SOAPAction header value
            params: Parameters dict
            result_element: Name of result element in response

        Returns:
            Response data as dictionary or None if error
        """
        try:
            # Build SOAP envelope
            soap_body = self._build_soap_envelope(method, namespace, params)

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': soap_action
            }

            logger.info(f'PAQ Wallet API Request: POST {url} ({method})')
            logger.debug(f'SOAP Body: {soap_body}')

            response = requests.post(
                url,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=30
            )

            logger.info(f'PAQ Wallet API Response Status: {response.status_code}')
            logger.debug(f'Response: {response.text}')

            if response.status_code >= 400:
                logger.error(f'PAQ Wallet API Error: {response.text}')
                return None

            # Parse SOAP response
            result = self._parse_soap_response(response.text, result_element)

            if result:
                logger.debug(f'Parsed result: {result}')
                return result
            else:
                logger.warning(f'Could not parse response: {response.text}')
                return {'raw_response': response.text}

        except requests.exceptions.Timeout:
            logger.error('PAQ Wallet API Timeout')
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f'PAQ Wallet API Connection Error: {str(e)}')
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f'PAQ Wallet API Request Error: {str(e)}')
            return None

    def emite_token(
        self,
        monto: Decimal,
        referencia: str,
        horas_vigencia: int,
        cliente_celular: Optional[str] = None,
        cliente_email: Optional[str] = None,
        descripcion: str = '',
        cliente_nombre: str = ''
    ) -> Dict:
        """
        Generate a PAYPAQ token for payment

        Args:
            monto: Amount in GTQ (required)
            referencia: Reference number/order ID (required, max 256 chars)
            horas_vigencia: Hours of validity (required)
            cliente_celular: Customer phone (8 digits, required if no email)
            cliente_email: Customer email (required if no phone)
            descripcion: Short description
            cliente_nombre: Customer name (max 201 chars)

        Returns:
            Dict with:
            - success: bool
            - codret: Return code (0 = success)
            - mensaje: Descriptive message
            - transaccion: Transaction ID (if success)
            - token: 5-char PAYPAQ code (if success)
        """
        if not cliente_celular and not cliente_email:
            return {
                'success': False,
                'codret': -1,
                'mensaje': 'Debe especificar cliente_celular o cliente_email',
                'transaccion': 0,
                'token': ''
            }

        params = {
            'usuario': self.usuario,
            'password': self.password,
            'rep_id': self.rep_id,
            'cliente_celular': str(cliente_celular)[:8] if cliente_celular else '',
            'cliente_email': str(cliente_email)[:256] if cliente_email else '',
            'monto': str(float(monto)),
            'referencia': str(referencia)[:256],
            'descripcion': str(descripcion) if descripcion else '',
            'cliente_nombre': str(cliente_nombre)[:201] if cliente_nombre else '',
            'horas_vigencia': str(int(horas_vigencia))
        }

        response = self._make_soap_request(
            url=self.emite_url,
            method='emite_token',
            namespace=self.EMITE_TOKEN_NS,
            soap_action='http://www.paq.com.gt/paqpay/emite_token',
            params=params,
            result_element='emite_tokenResult'
        )

        if response is None:
            return {
                'success': False,
                'codret': -99,
                'mensaje': 'Error de conexion con PAQ Wallet',
                'transaccion': 0,
                'token': ''
            }

        codret = response.get('codret', -1)
        # Handle string codret
        if isinstance(codret, str):
            codret = int(codret) if codret.lstrip('-').isdigit() else -1

        return {
            'success': codret == 0,
            'codret': codret,
            'mensaje': response.get('mensaje', ''),
            'transaccion': response.get('transaccion', 0),
            'token': response.get('token', ''),
            'url': response.get('url', '')
        }

    def consulta_tokens(
        self,
        transaccion: Optional[int] = None,
        fecha_del: Optional[str] = None,
        fecha_al: Optional[str] = None,
        cliente_celular: Optional[str] = None,
        cliente_email: Optional[str] = None,
        referencia: Optional[str] = None
    ) -> Dict:
        """
        Query PAYPAQ tokens status

        Args:
            transaccion: Transaction ID (if specified, ignores other filters)
            fecha_del: Start date (YYYY-MM-DD format)
            fecha_al: End date (YYYY-MM-DD format)
            cliente_celular: Filter by customer phone
            cliente_email: Filter by customer email
            referencia: Filter by reference

        Returns:
            Dict with:
            - success: bool
            - codret: Return code (0 = success)
            - mensaje: Descriptive message
            - tokens: List of token data (if success)
        """
        params = {
            'usuario': self.usuario,
            'password': self.password,
            'rep_id': self.rep_id,
            'transaccion': str(transaccion) if transaccion else '',
            'fecha_del': fecha_del or '',
            'fecha_al': fecha_al or '',
            'cliente_celular': str(cliente_celular)[:8] if cliente_celular else '',
            'cliente_email': str(cliente_email)[:256] if cliente_email else '',
            'referencia': str(referencia)[:256] if referencia else ''
        }

        response = self._make_soap_request(
            url=self.emite_url,
            method='consulta_tokens',
            namespace=self.CONSULTA_TOKENS_NS,
            soap_action='http://www.paq.com.gt/paqpay/consulta_tokens',
            params=params,
            result_element='consulta_tokensResult'
        )

        if response is None:
            return {
                'success': False,
                'codret': -99,
                'mensaje': 'Error de conexion con PAQ Wallet',
                'tokens': []
            }

        codret = response.get('codret', response.get('codigo', -1))

        # Handle string codret
        if isinstance(codret, str):
            codret = int(codret) if codret.lstrip('-').isdigit() else -1

        tokens = response.get('Ctoken', [])
        if not isinstance(tokens, list):
            tokens = [tokens] if tokens else []

        # Map status codes to descriptions
        for token in tokens:
            status = token.get('status', -1)
            if isinstance(status, str):
                status = int(status) if status.lstrip('-').isdigit() else -1
            token['status_description'] = self.STATUS_CHOICES.get(status, 'Desconocido')

        return {
            'success': codret == 0,
            'codret': codret,
            'mensaje': response.get('mensaje', ''),
            'tokens': tokens
        }

    def get_token_status(self, transaccion_id: int) -> Dict:
        """
        Get status of a specific token by transaction ID

        Args:
            transaccion_id: The transaction ID to check

        Returns:
            Token data with status or error
        """
        result = self.consulta_tokens(transaccion=transaccion_id)

        if result['success'] and result['tokens']:
            token_data = result['tokens'][0]
            return {
                'success': True,
                'token': token_data.get('token', ''),
                'status': token_data.get('status', -1),
                'status_description': token_data.get('status_description', 'Desconocido'),
                'monto': token_data.get('monto', 0),
                'referencia': token_data.get('referencia', ''),
                'fecha_emitido': token_data.get('fecha_emitido', ''),
                'fecha_cobrado': token_data.get('fecha_cobrado', ''),
                'autorizacion_cobra': token_data.get('autorizacion_cobra', '')
            }

        return {
            'success': False,
            'mensaje': result.get('mensaje', 'Token no encontrado'),
            'status': -1
        }

    def paqgo_payment(
        self,
        token: str,
        celular: str
    ) -> Dict:
        """
        Process payment using PAQ-GO button
        Debits from customer's PAQWALLET and credits merchant immediately

        Args:
            token: 5-char PAYPAQ token (entered by customer)
            celular: Customer's phone number associated with PAQWALLET (8 digits)

        Returns:
            Dict with:
            - success: bool
            - codret: Return code (0 = success)
            - mensaje: Descriptive message
            - transaccion: Transaction ID (if success)
        """
        params = {
            'usuario': self.usuario,
            'password': self.password,
            'rep_id': self.rep_id,
            'token': str(token)[:5].upper(),
            'celular': str(celular)[:8]
        }

        response = self._make_soap_request(
            url=self.paqgo_url,
            method='PAQgo',
            namespace=self.PAQGO_NS,
            soap_action='http://tempuri.org/PAQgo',
            params=params,
            result_element='PAQgoResult'
        )

        if response is None:
            return {
                'success': False,
                'codret': -99,
                'mensaje': 'Error de conexion con PAQ Wallet',
                'transaccion': 0
            }

        codret = response.get('codret', -1)
        # Handle string codret
        if isinstance(codret, str):
            codret = int(codret) if codret.lstrip('-').isdigit() else -1

        return {
            'success': codret == 0,
            'codret': codret,
            'mensaje': response.get('mensaje', ''),
            'transaccion': response.get('transaccion', 0)
        }

    # ============================================
    # High-level convenience methods for SegurifAI
    # ============================================

    def create_subscription_payment(
        self,
        user_phone: str,
        user_email: str,
        user_name: str,
        amount: Decimal,
        plan_name: str,
        subscription_id: str,
        validity_hours: int = 24
    ) -> Dict:
        """
        Create a payment token for subscription payment

        Args:
            user_phone: User's phone number (8 digits)
            user_email: User's email
            user_name: User's full name
            amount: Subscription amount in GTQ
            plan_name: Name of the service plan
            subscription_id: Internal subscription/order ID
            validity_hours: Token validity in hours (default 24)

        Returns:
            Token creation result
        """
        referencia = f'SUB-{subscription_id}'
        descripcion = f'Suscripcion {plan_name}'

        return self.emite_token(
            monto=amount,
            referencia=referencia,
            horas_vigencia=validity_hours,
            cliente_celular=user_phone,
            cliente_email=user_email,
            descripcion=descripcion,
            cliente_nombre=user_name
        )

    def create_service_payment(
        self,
        user_phone: str,
        user_email: str,
        user_name: str,
        amount: Decimal,
        service_type: str,
        request_id: str,
        validity_hours: int = 48
    ) -> Dict:
        """
        Create a payment token for assistance service payment

        Args:
            user_phone: User's phone number (8 digits)
            user_email: User's email
            user_name: User's full name
            amount: Service amount in GTQ
            service_type: Type of service (ROADSIDE, HEALTH, CARD_INSURANCE)
            request_id: Assistance request ID
            validity_hours: Token validity in hours (default 48)

        Returns:
            Token creation result
        """
        referencia = f'REQ-{request_id}'

        service_names = {
            'ROADSIDE': 'Asistencia Vial',
            'HEALTH': 'Asistencia Medica',
            'CARD_INSURANCE': 'Seguro de Tarjeta'
        }
        descripcion = f'{service_names.get(service_type, "Servicio")} - {request_id}'

        return self.emite_token(
            monto=amount,
            referencia=referencia,
            horas_vigencia=validity_hours,
            cliente_celular=user_phone,
            cliente_email=user_email,
            descripcion=descripcion,
            cliente_nombre=user_name
        )

    def process_customer_payment(
        self,
        paypaq_token: str,
        customer_phone: str
    ) -> Dict:
        """
        Process customer payment when they enter their PAYPAQ token

        Args:
            paypaq_token: The 5-char PAYPAQ token received via SMS
            customer_phone: Customer's PAQWALLET phone number

        Returns:
            Payment result
        """
        return self.paqgo_payment(token=paypaq_token, celular=customer_phone)

    def check_payment_status(self, referencia: str) -> Dict:
        """
        Check if a payment has been completed by reference

        Args:
            referencia: The reference used when creating the token

        Returns:
            Payment status information
        """
        result = self.consulta_tokens(referencia=referencia)

        if result['success'] and result['tokens']:
            token_data = result['tokens'][0]
            status = token_data.get('status', -1)
            if isinstance(status, str):
                status = int(status) if status.lstrip('-').isdigit() else -1

            return {
                'success': True,
                'paid': status == self.STATUS_COLLECTED,
                'status': status,
                'status_description': self.STATUS_CHOICES.get(status, 'Desconocido'),
                'token': token_data.get('token', ''),
                'monto': token_data.get('monto', 0),
                'fecha_cobrado': token_data.get('fecha_cobrado', ''),
                'autorizacion': token_data.get('autorizacion_cobra', '')
            }

        return {
            'success': False,
            'paid': False,
            'mensaje': result.get('mensaje', 'Pago no encontrado')
        }

    def get_user_balance(self, paq_wallet_id: str) -> Optional[Dict]:
        """
        Get user's PAQ Wallet balance (placeholder - not available in current API)

        Args:
            paq_wallet_id: User's PAQ Wallet ID

        Returns:
            Balance data or None
        """
        # Note: Balance query is not available in the current PAQ API
        # This would need a different integration or user must check in PAQ app
        return {
            'balance': 0,
            'currency': 'GTQ',
            'note': 'Consulte su saldo directamente en la app PAQ Wallet'
        }

    def get_transaction_history(self, paq_wallet_id: str, limit: int = 10) -> List[Dict]:
        """
        Get user's transaction history (queries by phone if linked)

        Args:
            paq_wallet_id: User's PAQ Wallet phone number
            limit: Maximum number of transactions

        Returns:
            List of transactions
        """
        # Query recent tokens for this phone number
        result = self.consulta_tokens(cliente_celular=paq_wallet_id)

        if result['success']:
            return result['tokens'][:limit]

        return []


# Global instance
paq_wallet_service = PAQWalletService()
