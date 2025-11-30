# SegurifAI x PAQ - Postman Collection Guide

## Overview

This guide explains how to use the Postman collection to test all API endpoints for the SegurifAI x PAQ backend (Guatemala).

---

## Files Included

1. **SegurifAI_API.postman_collection.json** - Complete API collection with all endpoints
2. **SegurifAI_Local.postman_environment.json** - Local development environment
3. **SegurifAI_Production.postman_environment.json** - Production environment template

---

## Installation

### Step 1: Import Collection

1. Open Postman
2. Click **Import** button (top left)
3. Select **SegurifAI_API.postman_collection.json**
4. The collection will appear in your Collections sidebar

### Step 2: Import Environment

1. Click **Import** button
2. Select **SegurifAI_Local.postman_environment.json**
3. Select **SegurifAI_Production.postman_environment.json** (optional)
4. Select the environment from the dropdown (top right)

---

## Quick Start

### 1. Set Environment

Select **SegurifAI Local** from the environment dropdown (top right corner)

### 2. Login to Get Access Token

1. Expand **Authentication** folder
2. Click **Login (Get Token)**
3. The request body contains admin credentials by default:
   ```json
   {
       "email": "admin@segurifai.com",
       "password": "Admin123!"
   }
   ```
4. Click **Send**
5. **Tokens are automatically saved** to environment variables

### 3. Test Other Endpoints

Now you can test any endpoint! The access token is automatically included in the Authorization header.

---

## Collection Structure

### 1. Authentication
- **Login (Get Token)** - Automatically saves access and refresh tokens
- **Refresh Token** - Get new access token using refresh token
- **Verify Token** - Check if access token is valid

### 2. Users
- **Register New User** - Create new user account
- **Get My Profile** - Get current user profile
- **Update My Profile** - Update user information
- **Change Password** - Change user password

### 3. Services
- **Get Service Categories** - List all service types (Public)
- **Get Service Category by ID** - Get specific category
- **Get All Service Plans** - List all plans (Public)
- **Get Service Plan by ID** - Get specific plan
- **Get Featured Plans** - Get premium/featured plans
- **Get My Subscriptions** - User's active subscriptions
- **Subscribe to Plan** - Subscribe to a service plan

### 4. Providers
- **Get All Providers** - List all providers (MAPFRE Guatemala)
- **Get Provider by ID** - Get provider details
- **Get Available Providers** - Currently available providers
- **Get Provider Reviews** - List provider reviews
- **Submit Provider Review** - Submit a review

### 5. Assistance Requests
- **Get My Assistance Requests** - User's requests
- **Get Assistance Request by ID** - Specific request details
- **Create Roadside Assistance Request** - Request asistencia vial
- **Create Health Assistance Request** - Request asistencia medica
- **Create Card Insurance Request** - Report card issues
- **Get Pending Requests** - All pending requests
- **Cancel Assistance Request** - Cancel a request
- **Get Request Updates** - Get status updates

### 6. PAQ Wallet
- **Get Wallet Balance** - Get wallet balance (GTQ)
- **Get Transaction History** - Transaction history
- **Get All Transactions** - All transactions

### 7. Admin Only
- **Get All Users** - List all users (Admin)
- **Get User by ID** - Get user details (Admin)
- **Create Service Category** - Create new category (Admin)
- **Create Service Plan** - Create new plan (Admin)

---

## Test Accounts

### Admin Account
- **Email:** admin@segurifai.com
- **Password:** Admin123!
- **Access:** Full system access

---

## Testing Different Service Types

### Roadside Assistance (Asistencia Vial)
```json
{
    "user_service": 1,
    "service_category": 1,
    "title": "Llanta ponchada en carretera",
    "description": "Necesito cambio de llanta",
    "priority": "HIGH",
    "location_address": "Km 15 Carretera al Atlantico",
    "location_city": "Ciudad de Guatemala",
    "location_state": "Guatemala",
    "vehicle_make": "Toyota",
    "vehicle_model": "Hilux",
    "vehicle_year": 2022,
    "vehicle_plate": "P-456DEF"
}
```

### Health Assistance (Asistencia Medica)
```json
{
    "user_service": 2,
    "service_category": 2,
    "title": "Emergencia Medica",
    "description": "Paciente con fiebre alta",
    "priority": "URGENT",
    "location_address": "12 Calle 5-20, Zona 10",
    "location_city": "Ciudad de Guatemala",
    "location_state": "Guatemala",
    "patient_name": "Maria Garcia",
    "patient_age": 45,
    "symptoms": "Fiebre alta, dolor de cabeza"
}
```

### Card Insurance (Seguro de Tarjeta)
```json
{
    "user_service": 3,
    "service_category": 3,
    "title": "Transacciones Fraudulentas",
    "description": "Detecte cargos no autorizados en mi tarjeta",
    "priority": "HIGH",
    "location_address": "6a Avenida 9-30, Zona 1",
    "location_city": "Ciudad de Guatemala",
    "location_state": "Guatemala",
    "card_last_four": "5678",
    "incident_type": "FRAUD"
}
```

---

## Environment Variables

The local environment includes these variables:

| Variable | Description | Auto-Set |
|----------|-------------|----------|
| `base_url` | API base URL (http://localhost:8000/api) | No |
| `access_token` | JWT access token | Yes (on login) |
| `refresh_token` | JWT refresh token | Yes (on login) |
| `admin_email` | Admin email | No |
| `admin_password` | Admin password | No |

---

## Auto-Save Tokens Feature

The collection includes automatic token management:

1. When you run **Login (Get Token)**, tokens are automatically saved
2. All authenticated requests use `{{access_token}}` variable
3. Run **Refresh Token** when access token expires
4. No need to manually copy/paste tokens!

---

## Testing Workflow Example

### Complete User Journey Test

1. **Register New User**
   - Go to Users > Register New User
   - Modify email and details (use Guatemala data)
   - Send request

2. **Login with New User**
   - Go to Authentication > Login
   - Update credentials
   - Send request (tokens auto-saved)

3. **Get User Profile**
   - Go to Users > Get My Profile
   - Send request

4. **View Service Plans**
   - Go to Services > Get All Service Plans
   - Send request (prices in GTQ)

5. **Subscribe to Plan**
   - Go to Services > Subscribe to Plan
   - Update plan ID in body
   - Send request

6. **Create Assistance Request**
   - Go to Assistance Requests > Create [Type] Request
   - Fill in details with Guatemala locations
   - Send request

7. **View My Requests**
   - Go to Assistance Requests > Get My Assistance Requests
   - Send request

---

## Public vs Authenticated Endpoints

### Public Endpoints (No Authentication Required)
- All Service Categories
- All Service Plans
- All Providers (MAPFRE Guatemala)
- User Registration

### Authenticated Endpoints
- User Profile
- Subscriptions
- Assistance Requests
- PAQ Wallet
- Reviews

### Admin-Only Endpoints
- User Management
- Create/Edit Categories
- Create/Edit Plans

---

## Service Plans Reference (GTQ)

| Service | Plan | Monthly Price |
|---------|------|---------------|
| Asistencia Vial | Basico | Q150 |
| Asistencia Vial | Premium | Q300 |
| Asistencia Medica | Basico | Q225 |
| Asistencia Medica | Premium | Q450 |
| Seguro de Tarjeta | Basico | Q75 |
| Seguro de Tarjeta | Premium | Q150 |

---

## Troubleshooting

### Issue: "Unauthorized" Error

**Solution:** Run **Login (Get Token)** first to get access token

### Issue: Token Expired

**Solution:** Run **Refresh Token** or login again

### Issue: "Forbidden" Error

**Solution:** You're trying to access an admin endpoint without admin privileges. Login with admin credentials.

### Issue: Connection Refused

**Solution:** Make sure Django server is running:
```bash
python manage.py runserver
```

---

## Production Setup

When moving to production:

1. **Select Production Environment**
2. **Update base_url** in environment to your production URL
3. **Update credentials** with production accounts
4. **Enable HTTPS** (production URLs should use https://)

---

## Tips & Best Practices

1. **Always login first** before testing authenticated endpoints
2. **Use variables** for IDs (create variables for user_id, plan_id, etc.)
3. **Check response status** - 200/201 means success
4. **Save responses** - Use Postman's save response feature for reference
5. **Use Guatemala data** - Addresses, phone numbers (+502), currency (GTQ)
6. **Share collection** - Export and share with your team

---

## API Documentation

For detailed API documentation, visit:
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/

---

## Related Documentation

- [README.md](README.md) - Project overview
- [API_REFERENCE.md](API_REFERENCE.md) - Complete API reference
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [docs/PAQ_WALLET.md](docs/PAQ_WALLET.md) - PAQ Wallet integration

---

**Currency:** GTQ (Guatemalan Quetzales)
**Provider:** MAPFRE Guatemala
**Country:** Guatemala
