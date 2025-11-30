# PAQ Wallet Integration (PAQ-GO) - Guatemala

Complete integration guide for PAQ Wallet's PAQ-GO payment system in Guatemala.

## Overview

PAQ Wallet is Guatemala's leading digital wallet solution. The PAQ-GO integration enables customers to pay for SegurifAI assistance services using their PAQWALLET balance through a simple SMS-based token system.

## API Endpoints

| Service | URL |
|---------|-----|
| Token Generation & Query | `https://www.paq.com.gt/paqpayws/emite.asmx` |
| Payment Processing (PAQ-GO) | `https://www.paq.com.gt/paqgo/paqgo.asmx` |

## Authentication

All API calls require three credentials:

| Parameter | Description |
|-----------|-------------|
| `usuario` | POS registered username |
| `password` | POS registered password |
| `rep_id` | POS registered ID (ID Code) |

## Payment Flow

```
1. GENERATE TOKEN
   System calls emite_token() with payment details

2. CUSTOMER NOTIFICATION
   PAQ sends SMS with 5-character PAYPAQ code to customer

3. CUSTOMER ENTERS CODE
   Customer enters the PAYPAQ code + their phone number in the app

4. PROCESS PAYMENT
   System calls PAQgo() to complete the transaction

5. INSTANT CREDIT
   Funds are credited immediately to the merchant account
```

## API Methods

### 1. emite_token - Generate Payment Token

Creates a PAYPAQ payment code that is sent to the customer via SMS.

**Endpoint:** `POST /emite_token`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| usuario | string | Yes | POS username |
| password | string | Yes | POS password |
| rep_id | string | Yes | POS ID code |
| monto | decimal | Yes | Amount in GTQ |
| referencia | string(256) | Yes | Reference/Order ID |
| horas_vigencia | int | Yes | Token validity in hours |
| cliente_celular | string(8) | Conditional | Customer phone (8 digits, required if no email) |
| cliente_email | string(256) | Conditional | Customer email (required if no phone) |
| descripcion | string | No | Short description |
| cliente_nombre | string(201) | No | Customer name |

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| codret | int | Return code (0 = success) |
| mensaje | string | Descriptive message |
| transaccion | int | Transaction ID |
| token | string(5) | 5-character PAYPAQ code |

**Example Request:**
```json
{
  "usuario": "APPW",
  "password": "123456",
  "rep_id": "89E3AF",
  "monto": 150.00,
  "referencia": "SUB-12345",
  "horas_vigencia": 24,
  "cliente_celular": "55551234",
  "descripcion": "Suscripcion Asistencia Vial Basico",
  "cliente_nombre": "Juan Perez"
}
```

**Example Response:**
```json
{
  "codret": 0,
  "mensaje": "Token generado exitosamente",
  "transaccion": 987654,
  "token": "AB12C"
}
```

### 2. consulta_tokens - Query Token Status

Check the status of one or more PAYPAQ tokens.

**Endpoint:** `POST /consulta_tokens`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| usuario | string | Yes | POS username |
| password | string | Yes | POS password |
| rep_id | string | Yes | POS ID code |
| transaccion | int | No | Transaction ID (if specified, ignores other filters) |
| fecha_del | string | No | Start date (YYYY-MM-DD) |
| fecha_al | string | No | End date (YYYY-MM-DD) |
| cliente_celular | string(8) | No | Filter by customer phone |
| cliente_email | string(256) | No | Filter by customer email |
| referencia | string(256) | No | Filter by reference |

**Token Status Codes:**

| Code | Status | Description |
|------|--------|-------------|
| 0 | En proceso | Token being generated |
| 1 | Token emitido | Token issued and active |
| 2 | Cobrado | Payment collected |
| 3 | Anulado | Cancelled |
| 4 | Vencido | Expired |

**Example Response:**
```json
{
  "codret": 0,
  "mensaje": "Consulta exitosa",
  "Ctoken": [
    {
      "token": "AB12C",
      "status": 2,
      "monto": 150.00,
      "referencia": "SUB-12345",
      "fecha_emitido": "2025-01-15T10:00:00",
      "fecha_cobrado": "2025-01-15T11:30:00",
      "autorizacion_cobra": "AUTH123456"
    }
  ]
}
```

### 3. PAQgo - Process Payment

Complete the payment by debiting the customer's PAQWALLET.

**Endpoint:** `POST /PAQgo`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| usuario | string | Yes | POS username |
| password | string | Yes | POS password |
| rep_id | string | Yes | POS ID code |
| token | string(5) | Yes | PAYPAQ code entered by customer |
| celular | string(8) | Yes | Customer's PAQWALLET phone number |

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| codret | int | Return code (0 = success) |
| mensaje | string | Descriptive message |
| transaccion | int | Transaction ID |

**Example Request:**
```json
{
  "usuario": "APPW",
  "password": "123456",
  "rep_id": "89E3AF",
  "token": "AB12C",
  "celular": "55551234"
}
```

**Example Response:**
```json
{
  "codret": 0,
  "mensaje": "Pago procesado exitosamente",
  "transaccion": 987654
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| -1 | Invalid parameters |
| -2 | Authentication failed |
| -3 | Token not found |
| -4 | Token expired |
| -5 | Insufficient balance |
| -6 | Transaction already processed |
| -99 | Connection error |

## SegurifAI Integration

### Service Location

The PAQ Wallet integration is implemented in:
- **File:** `apps/paq_wallet/services.py`
- **Class:** `PAQWalletService`

### Configuration

Set these environment variables in `.env`:

```env
PAQ_WALLET_EMITE_URL=https://www.paq.com.gt/paqpayws/emite.asmx
PAQ_WALLET_PAQGO_URL=https://www.paq.com.gt/paqgo/paqgo.asmx
PAQ_WALLET_ID_CODE=89E3AF
PAQ_WALLET_USER=APPW
PAQ_WALLET_PASSWORD=123456
```

### High-Level Methods

The service provides convenience methods for common operations:

#### Create Subscription Payment
```python
from apps.paq_wallet.services import paq_wallet_service

result = paq_wallet_service.create_subscription_payment(
    user_phone='55551234',
    user_email='user@example.com',
    user_name='Juan Perez',
    amount=Decimal('150.00'),
    plan_name='Asistencia Vial Basico',
    subscription_id='12345',
    validity_hours=24
)

if result['success']:
    print(f"Token: {result['token']}")
    print(f"Transaction: {result['transaccion']}")
```

#### Create Service Payment
```python
result = paq_wallet_service.create_service_payment(
    user_phone='55551234',
    user_email='user@example.com',
    user_name='Juan Perez',
    amount=Decimal('500.00'),
    service_type='ROADSIDE',
    request_id='REQ-789',
    validity_hours=48
)
```

#### Process Customer Payment
```python
result = paq_wallet_service.process_customer_payment(
    paypaq_token='AB12C',
    customer_phone='55551234'
)

if result['success']:
    print(f"Payment completed! Transaction: {result['transaccion']}")
```

#### Check Payment Status
```python
result = paq_wallet_service.check_payment_status(referencia='SUB-12345')

if result['paid']:
    print(f"Payment collected on {result['fecha_cobrado']}")
    print(f"Authorization: {result['autorizacion']}")
```

## Payment Scenarios

### Subscription Payment

1. User selects a service plan
2. System generates PAYPAQ token
3. User receives SMS with code
4. User enters code in app
5. System processes payment
6. Subscription activated immediately

### Assistance Service Payment

1. User creates assistance request
2. Service is provided by MAPFRE
3. System generates PAYPAQ token for final amount
4. User receives SMS with code
5. User enters code in app
6. System processes payment
7. Request marked as paid

## Security Considerations

- All API calls use HTTPS
- Credentials stored in environment variables
- Never log sensitive payment data
- Token expires after configured hours
- Phone numbers validated to 8 digits

## Testing

For development testing, use the configured test credentials:

```env
PAQ_WALLET_ID_CODE=89E3AF
PAQ_WALLET_USER=APPW
PAQ_WALLET_PASSWORD=123456
```

## Support

For PAQ Wallet technical support:
- Website: https://www.paq.com.gt
- Contact PAQ for production credentials

---

**Currency:** GTQ (Guatemalan Quetzales)
**Country:** Guatemala
**Provider:** PAQ Wallet / PAQ-GO
