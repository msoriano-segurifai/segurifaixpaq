# SegurifAI x PAQ - Complete API Reference

## Base URL

```
Development: http://localhost:8000/api/
Production: https://your-domain.com/api/
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Response Format

### Success Response
```json
{
  "id": 1,
  "field": "value",
  ...
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

or

```json
{
  "field_name": ["Error message for this field"]
}
```

---

## Authentication Endpoints

### 1. Obtain Token
**POST** `/auth/token/`

Get access and refresh tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Refresh Token
**POST** `/auth/token/refresh/`

Refresh access token.

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 3. Verify Token
**POST** `/auth/token/verify/`

Verify token validity.

**Request:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{}
```

---

## User Endpoints

### 1. Register User
**POST** `/users/register/`

**Permission:** Public

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "first_name": "Juan",
  "last_name": "Perez",
  "phone_number": "+50212345678",
  "role": "USER",
  "address": "6a Avenida 5-55",
  "city": "Ciudad de Guatemala",
  "state": "Guatemala",
  "postal_code": "01001",
  "country": "Guatemala"
}
```

**Response:** 201 Created
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Juan",
  "last_name": "Perez",
  "phone_number": "+50212345678",
  "role": "USER",
  ...
}
```

### 2. Get Current User Profile
**GET** `/users/me/`

**Permission:** Authenticated

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Juan",
  "last_name": "Perez",
  "full_name": "Juan Perez",
  "phone_number": "+50212345678",
  "role": "USER",
  "paq_wallet_id": "PAQ123456",
  ...
}
```

### 3. Update Current User Profile
**PUT/PATCH** `/users/me/`

**Permission:** Authenticated

**Request:**
```json
{
  "first_name": "Juan",
  "last_name": "Garcia",
  "address": "7a Avenida 10-20",
  "emergency_contact_name": "Maria Perez",
  "emergency_contact_phone": "+50287654321"
}
```

### 4. Change Password
**POST** `/users/change-password/`

**Permission:** Authenticated

**Request:**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!",
  "new_password2": "NewPass123!"
}
```

**Response:**
```json
{
  "message": "Password updated successfully"
}
```

### 5. List Users
**GET** `/users/`

**Permission:** Admin only

**Query Parameters:**
- `search`: Search by email, name
- `ordering`: Order by field
- `page`: Page number
- `page_size`: Items per page

---

## Service Endpoints

### 1. List Service Categories
**GET** `/services/categories/`

**Permission:** Public

**Response:**
```json
[
  {
    "id": 1,
    "name": "Asistencia Vial",
    "category_type": "ROADSIDE",
    "description": "Asistencia vehicular 24/7 en toda Guatemala",
    "icon": "road-icon",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Asistencia Medica",
    "category_type": "HEALTH",
    "description": "Cobertura medica de emergencia",
    "icon": "health-icon",
    "is_active": true
  },
  {
    "id": 3,
    "name": "Seguro de Tarjeta",
    "category_type": "CARD_INSURANCE",
    "description": "Proteccion contra fraude y robo de tarjeta",
    "icon": "card-icon",
    "is_active": true
  }
]
```

### 2. List Service Plans
**GET** `/services/plans/`

**Permission:** Public

**Query Parameters:**
- `search`: Search plans
- `ordering`: Order by price, created_at
- `category`: Filter by category type

**Response:**
```json
[
  {
    "id": 1,
    "category_type": "ROADSIDE",
    "category_name": "Asistencia Vial",
    "name": "Asistencia Vial Basico",
    "price_monthly": 150.00,
    "price_yearly": 1500.00,
    "currency": "GTQ",
    "is_active": true,
    "is_featured": false
  },
  {
    "id": 2,
    "category_type": "ROADSIDE",
    "category_name": "Asistencia Vial",
    "name": "Asistencia Vial Premium",
    "price_monthly": 300.00,
    "price_yearly": 3000.00,
    "currency": "GTQ",
    "is_active": true,
    "is_featured": true
  }
]
```

### 3. Get Featured Plans
**GET** `/services/plans/featured/`

**Permission:** Public

### 4. Get Plans by Category
**GET** `/services/plans/by-category/{category_type}/`

**Permission:** Public

**Example:** `/services/plans/by-category/ROADSIDE/`

### 5. List User Services
**GET** `/services/user-services/`

**Permission:** Authenticated

**Response:**
```json
[
  {
    "id": 1,
    "user_email": "user@example.com",
    "plan_name": "Asistencia Vial Basico",
    "plan_category": "ROADSIDE",
    "status": "ACTIVE",
    "start_date": "2025-01-01",
    "end_date": "2026-01-01",
    "requests_this_month": 2,
    "total_requests": 5,
    "can_request": true
  }
]
```

### 6. Subscribe to Service
**POST** `/services/user-services/`

**Permission:** Authenticated

**Request:**
```json
{
  "user": 1,
  "plan": 1,
  "start_date": "2025-01-01",
  "end_date": "2026-01-01",
  "status": "ACTIVE"
}
```

### 7. Get Active Services
**GET** `/services/user-services/active/`

**Permission:** Authenticated

### 8. Cancel Service
**POST** `/services/user-services/{id}/cancel/`

**Permission:** Authenticated

---

## Provider Endpoints

### 1. List Providers
**GET** `/providers/`

**Permission:** Public for viewing, Admin/Provider for modifications

**Query Parameters:**
- `search`: Search by company name, city, state
- `category`: Filter by service category
- `available`: Filter by availability (true/false)
- `ordering`: Order by rating, total_completed

**Response:**
```json
[
  {
    "id": 1,
    "company_name": "MAPFRE Guatemala",
    "city": "Ciudad de Guatemala",
    "state": "Guatemala",
    "rating": 4.8,
    "total_reviews": 500,
    "is_available": true,
    "status": "ACTIVE",
    "service_categories_names": ["Asistencia Vial", "Asistencia Medica", "Seguro de Tarjeta"]
  }
]
```

### 2. Get Provider Details
**GET** `/providers/{id}/`

**Permission:** Public

**Response:**
```json
{
  "id": 1,
  "company_name": "MAPFRE Guatemala",
  "business_phone": "+502 2328 0000",
  "business_email": "asistencia@mapfre.com.gt",
  "address": "7a Avenida 5-10, Zona 4",
  "city": "Ciudad de Guatemala",
  "rating": 4.8,
  "total_reviews": 500,
  "total_completed": 2500,
  "is_available": true,
  "working_hours": {
    "note": "24/7 cobertura nacional"
  },
  "service_categories_details": [...],
  "recent_reviews": [...]
}
```

### 3. Get Available Providers
**GET** `/providers/available/`

**Permission:** Public

### 4. List Provider Reviews
**GET** `/providers/reviews/`

**Permission:** Authenticated

**Query Parameters:**
- `provider`: Filter by provider ID

### 5. Create Provider Review
**POST** `/providers/reviews/`

**Permission:** Authenticated

**Request:**
```json
{
  "provider": 1,
  "assistance_request": 1,
  "rating": 5,
  "comment": "Excelente servicio de MAPFRE!"
}
```

---

## Assistance Request Endpoints

### 1. List Assistance Requests
**GET** `/assistance/requests/`

**Permission:** Authenticated

**Query Parameters:**
- `search`: Search by request number, title, description
- `status`: Filter by status
- `category`: Filter by service category
- `ordering`: Order by created_at, priority, status

### 2. Get Assistance Request Details
**GET** `/assistance/requests/{id}/`

**Permission:** Authenticated (owner, assigned provider, or admin)

### 3. Create Assistance Request
**POST** `/assistance/requests/`

**Permission:** Authenticated User

**Request (Roadside - Asistencia Vial):**
```json
{
  "user_service": 1,
  "service_category": 1,
  "title": "Vehiculo averiado",
  "description": "Motor no enciende",
  "priority": "HIGH",
  "location_address": "6a Avenida 5-55, Zona 1",
  "location_city": "Ciudad de Guatemala",
  "location_state": "Guatemala",
  "location_latitude": 14.6349,
  "location_longitude": -90.5069,
  "vehicle_make": "Toyota",
  "vehicle_model": "Corolla",
  "vehicle_year": 2020,
  "vehicle_plate": "P-123ABC"
}
```

**Request (Health - Asistencia Medica):**
```json
{
  "user_service": 2,
  "service_category": 2,
  "title": "Emergencia medica",
  "description": "Paciente con dolor en el pecho",
  "priority": "URGENT",
  "location_address": "10a Calle 5-20, Zona 10",
  "location_city": "Ciudad de Guatemala",
  "location_state": "Guatemala",
  "patient_name": "Juan Perez",
  "patient_age": 55,
  "symptoms": "Dolor en el pecho, dificultad para respirar"
}
```

**Request (Card Insurance - Seguro de Tarjeta):**
```json
{
  "user_service": 3,
  "service_category": 3,
  "title": "Transaccion fraudulenta",
  "description": "Cargos no autorizados en mi tarjeta",
  "priority": "HIGH",
  "location_address": "5a Avenida 10-15",
  "location_city": "Ciudad de Guatemala",
  "location_state": "Guatemala",
  "card_last_four": "1234",
  "incident_type": "FRAUD"
}
```

### 4. Update Assistance Request
**PUT/PATCH** `/assistance/requests/{id}/`

**Permission:** Provider (assigned) or Admin

### 5. Get Pending Requests
**GET** `/assistance/requests/pending/`

**Permission:** Authenticated

### 6. Get Active Requests
**GET** `/assistance/requests/active/`

**Permission:** Authenticated

### 7. Assign Provider to Request
**POST** `/assistance/requests/{id}/assign_provider/`

**Permission:** Admin

**Request:**
```json
{
  "provider_id": 1
}
```

### 8. Cancel Request
**POST** `/assistance/requests/{id}/cancel/`

**Permission:** Request owner or Admin

**Request:**
```json
{
  "reason": "Ya no necesito la asistencia"
}
```

---

## PAQ Wallet Endpoints

The platform integrates with PAQ Wallet's PAQ-GO system for payments in Guatemala.

### 1. Get Wallet Balance
**GET** `/wallet/balance/`

**Permission:** Authenticated

**Response:**
```json
{
  "balance": 1500.00,
  "currency": "GTQ",
  "status": "active"
}
```

### 2. Get Transaction History
**GET** `/wallet/history/`

**Permission:** Authenticated

**Query Parameters:**
- `limit`: Number of transactions (default: 10)

### 3. List Wallet Transactions
**GET** `/wallet/transactions/`

**Permission:** Authenticated

**Response:**
```json
[
  {
    "id": 1,
    "user_email": "user@example.com",
    "transaction_type": "PAYMENT",
    "amount": 150.00,
    "currency": "GTQ",
    "reference_number": "SUB-12345",
    "paypaq_token": "AB12C",
    "status": "COMPLETED",
    "assistance_request_number": null,
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### 4. Create Wallet Transaction
**POST** `/wallet/transactions/`

**Permission:** Authenticated

**Request:**
```json
{
  "user": 1,
  "transaction_type": "PAYMENT",
  "amount": 150.00,
  "currency": "GTQ",
  "assistance_request": null
}
```

### PAQ-GO Payment Flow

1. **Generate Token**: System calls PAQ API `emite_token()` with payment details
2. **SMS Notification**: PAQ sends 5-character PAYPAQ code to customer
3. **Customer Entry**: Customer enters code + phone in app
4. **Process Payment**: System calls PAQ API `PAQgo()` to complete transaction
5. **Instant Credit**: Funds credited immediately

For detailed PAQ integration documentation, see [docs/PAQ_WALLET.md](docs/PAQ_WALLET.md)

---

## Field Tech Dispatch Endpoints (Delivery-App Style)

MAWDY field technicians work like food delivery drivers - they receive job alerts within a radius.

### 1. Get My Profile
**GET** `/providers/dispatch/profile/`
**Permission:** MAWDY Field Tech

### 2. Go Online
**POST** `/providers/dispatch/online/`
**Permission:** MAWDY Field Tech
```json
{"latitude": 14.6349, "longitude": -90.5069}
```

### 3. Go Offline
**POST** `/providers/dispatch/offline/`
**Permission:** MAWDY Field Tech

### 4. Update Location
**POST** `/providers/dispatch/location/`
**Permission:** MAWDY Field Tech
```json
{"latitude": 14.635, "longitude": -90.507}
```

### 5. Get Available Jobs
**GET** `/providers/dispatch/jobs/available/`
**Permission:** MAWDY Field Tech

### 6. Accept Job
**POST** `/providers/dispatch/jobs/{offer_id}/accept/`
**Permission:** MAWDY Field Tech

### 7. Decline Job
**POST** `/providers/dispatch/jobs/{offer_id}/decline/`
**Permission:** MAWDY Field Tech

### 8. Get Active Job
**GET** `/providers/dispatch/jobs/active/`
**Permission:** MAWDY Field Tech

### 9. Mark Arrived
**POST** `/providers/dispatch/jobs/{offer_id}/arrived/`
**Permission:** MAWDY Field Tech

### 10. Start Service
**POST** `/providers/dispatch/jobs/{offer_id}/start/`
**Permission:** MAWDY Field Tech

### 11. Complete Job
**POST** `/providers/dispatch/jobs/{offer_id}/complete/`
**Permission:** MAWDY Field Tech
```json
{"notes": "Llanta reemplazada exitosamente"}
```

### 12. Get Earnings
**GET** `/providers/dispatch/earnings/`
**Permission:** MAWDY Field Tech

### 13. Get Job History
**GET** `/providers/dispatch/jobs/history/`
**Permission:** MAWDY Field Tech

---

## Evidence Flow Endpoints

### Business Rules

**HEALTH Assistance (NO photos):**
- Form-only → AI Validation → MAWDY Admin fallback

**ROAD Assistance:**
- AI Photo Analysis → Form Fallback → MAWDY Admin fallback

### 1. Get Evidence Options
**GET** `/assistance/evidence/{request_id}/options/`
**Permission:** Authenticated

### 2. Get Evidence Status
**GET** `/assistance/evidence/{request_id}/status/`
**Permission:** Authenticated

### 3. Get Form Template
**GET** `/assistance/evidence/template/{form_type}/`
**Permission:** Authenticated
**Form Types:** VEHICLE_DAMAGE, ROADSIDE_ISSUE, HEALTH_INCIDENT

### 4. Create Evidence Form
**POST** `/assistance/evidence/forms/create/`
**Permission:** Authenticated
```json
{
  "request_id": 1,
  "form_type": "ROADSIDE_ISSUE",
  "incident_date": "2025-01-22T10:00:00Z",
  "incident_description": "Description...",
  "location_description": "Location...",
  "vehicle_make": "Toyota",
  "vehicle_model": "Corolla",
  "vehicle_plate": "P-123ABC",
  "issue_type": "FLAT_TIRE"
}
```

### 5. Get Evidence Form
**GET** `/assistance/evidence/forms/{form_id}/`
**Permission:** Form owner or Admin

### 6. Update Evidence Form
**PUT** `/assistance/evidence/forms/{form_id}/update/`
**Permission:** Form owner

### 7. Submit Evidence Form
**POST** `/assistance/evidence/forms/{form_id}/submit/`
**Permission:** Form owner
```json
{"declaration_accepted": true}
```

### 8. Get My Evidence Forms
**GET** `/assistance/evidence/forms/`
**Permission:** Authenticated

### 9. Get Pending Forms (Admin)
**GET** `/assistance/evidence/admin/pending/`
**Permission:** MAWDY Admin or SegurifAI Admin

### 10. Review Evidence Form (Admin)
**POST** `/assistance/evidence/admin/{form_id}/review/`
**Permission:** MAWDY Admin or SegurifAI Admin
```json
{"action": "approve", "notes": "Verified"}
```
**Actions:** approve, reject, needs_info

### 11. AI Review Document
**POST** `/assistance/docs/{document_id}/ai-review/`
**Permission:** Authenticated

---

## Status Codes

- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: No permission
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering & Search

Most list endpoints support:
- `search`: Full-text search
- `ordering`: Sort by field (prefix with `-` for descending)

Example:
```
GET /api/providers/?search=mapfre&ordering=-rating
```

---

## Role-Based Permissions Summary

### Public (No Auth Required)
- Service categories
- Service plans
- Provider list (read-only)

### User
- Own profile
- Own services
- Create assistance requests
- View own requests
- Create reviews

### Provider
- Own provider profile
- Assigned assistance requests
- Update request status
- Toggle availability

### Admin
- All user operations
- All provider operations
- All assistance requests
- Assign providers
- Manage all resources

---

## Currency & Location

| Setting | Value |
|---------|-------|
| Currency | GTQ (Guatemalan Quetzales) |
| Country | Guatemala |
| Provider | MAPFRE Guatemala |
| Phone Format | +502 XXXX XXXX |

---

For interactive documentation, visit:
- Swagger UI: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- ReDoc: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
