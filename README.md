# SegurifAI x PAQ - Assistance Platform Backend

Complete Django REST API backend for the SegurifAI assistance platform integrated with PAQ Wallet (PAQ-GO) for Guatemala.

## Overview

SegurifAI x PAQ is a comprehensive assistance services platform that allows users in Guatemala to subscribe to and request assistance services (roadside, medical, card insurance) powered by MAPFRE Guatemala, with payments processed through PAQ Wallet's PAQ-GO integration.

## Features

### Core Features
- **Role-Based Access Control**: Admin, User, and Provider roles with granular permissions
- **Three Service Types**:
  - Asistencia Vial (Roadside Assistance)
  - Asistencia Medica (Health Assistance)
  - Seguro de Tarjeta (Card Insurance)
- **Provider**: MAPFRE Guatemala - 24/7 national coverage
- **PAQ Wallet Integration**: Full PAQ-GO integration for payments via PAYPAQ tokens
- **PAQ Wallet SSO**: Login with PAQ Wallet credentials (OTP-based)
- **JWT Authentication**: Secure token-based authentication
- **Guatemala Focus**: GTQ currency, Guatemala addresses, +502 phone numbers

### Advanced Features
- **Document Upload with AI Review**: Automated document verification for assistance requests
- **Real-time Location WebSocket**: Live provider tracking during assistance
- **Payment Webhooks**: Automatic payment status updates from PAQ
- **Transactional Emails**: Payment receipts, confirmations, reminders
- **Admin Dashboard API**: Statistics, reports, and analytics
- **Subscription Renewal**: Auto-renewal and reminder system
- **Promo Codes & Discounts**: Coupon system for plans
- **Gamification**: Educational modules with points, achievements, leaderboard

## Technology Stack

- **Framework**: Django 5.2.8
- **API**: Django REST Framework 3.16.1
- **Authentication**: JWT (djangorestframework-simplejwt)
- **WebSockets**: Django Channels
- **Documentation**: drf-spectacular (Swagger/OpenAPI)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Payment**: PAQ Wallet PAQ-GO Integration (SOAP/XML)

## Project Structure

```
SegurifAI x PAQ/
├── apps/
│   ├── users/           # User management, auth, PAQ SSO
│   ├── services/        # Service categories, plans, renewal
│   ├── providers/       # Provider profiles, locations, reviews
│   ├── assistance/      # Requests, documents, WebSocket tracking
│   ├── paq_wallet/      # PAQ-GO payments, webhooks
│   ├── gamification/    # Educational modules, achievements
│   ├── promotions/      # Promo codes, campaigns
│   ├── admin_dashboard/ # Statistics and reports
│   └── notifications/   # Email service
├── templates/
│   └── emails/          # Email templates
├── segurifai_backend/   # Project settings
├── manage.py
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 2. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Setup production data (MAPFRE + Service Plans)
python manage.py setup_production_data --confirm
```

### 3. Run Server

```bash
python manage.py runserver 8002
```

Access the API at: http://localhost:8002

## API Documentation

- **Swagger UI**: http://localhost:8002/api/docs/
- **ReDoc**: http://localhost:8002/api/redoc/
- **Admin Panel**: http://localhost:8002/admin/

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@segurifai.com | Admin123! |

## API Endpoints Summary

### Authentication
```
POST /api/auth/token/                    # Login (JWT tokens)
POST /api/auth/token/refresh/            # Refresh token
POST /api/users/auth/paq/request-otp/    # PAQ SSO - Request OTP
POST /api/users/auth/paq/verify-otp/     # PAQ SSO - Verify & login
POST /api/users/auth/paq/link/           # Link account to PAQ
```

### Users
```
POST /api/users/register/                # Register new user
GET  /api/users/me/                      # Get current profile
PUT  /api/users/me/                      # Update profile
```

### Services & Subscriptions
```
GET  /api/services/categories/           # Service types
GET  /api/services/plans/                # All plans
POST /api/services/user-services/        # Subscribe to plan
GET  /api/services/renewal/my/           # My renewal status
POST /api/services/renewal/{id}/renew/   # Initiate renewal
```

### Assistance Requests
```
GET  /api/assistance/requests/           # List requests
POST /api/assistance/requests/           # Create request
POST /api/assistance/docs/upload/        # Upload document
GET  /api/assistance/docs/{id}/required/ # Required documents
```

### PAQ Wallet Payments
```
POST /api/wallet/generate-token/         # Generate PAYPAQ token
POST /api/wallet/paqgo/                  # Process payment
GET  /api/wallet/check-token/            # Check payment status
POST /api/wallet/webhook/paq/            # Payment callback
```

### Promotions
```
POST /api/promotions/validate/           # Validate promo code
POST /api/promotions/apply/              # Apply discount
GET  /api/promotions/available/          # Available codes
```

### Gamification
```
GET  /api/educacion/modulos/             # Educational modules
POST /api/educacion/submit-quiz/         # Submit quiz answers
GET  /api/educacion/achievements/        # User achievements
GET  /api/educacion/leaderboard/         # Points leaderboard
```

### Admin Dashboard
```
GET  /api/admin/dashboard/overview/      # Main statistics
GET  /api/admin/dashboard/revenue/       # Revenue report
GET  /api/admin/dashboard/users/         # User analytics
GET  /api/admin/dashboard/assistance/    # Request stats
```

### WebSocket Endpoints
```
ws://localhost:8002/ws/tracking/request/{id}/   # Track request location
ws://localhost:8002/ws/tracking/provider/{id}/  # Provider broadcasts
ws://localhost:8002/ws/assistance/{id}/         # Request updates/chat
```

## PAQ Wallet Configuration

```env
PAQ_WALLET_EMITE_URL=https://www.pfrfrws.pfrfl.com/PAQPayWS/PAQpayWS.asmx
PAQ_WALLET_PAQGO_URL=https://www.pfrfrws.pfrfl.com/PAQGOws/PAQgows.asmx
PAQ_WALLET_ID_CODE=89E3AF
PAQ_WALLET_USER=APPW
PAQ_WALLET_PASSWORD=123456
```

## Service Plans (GTQ)

| Service | Basic | Premium |
|---------|-------|---------|
| Asistencia Vial | Q150/mes | Q300/mes |
| Asistencia Medica | Q225/mes | Q450/mes |
| Seguro de Tarjeta | Q75/mes | Q150/mes |

## Testing with Postman

Import these files into Postman:
- `SegurifAI_API.postman_collection.json`
- `SegurifAI_Environment.postman_environment.json`

## Documentation Files

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Quick Start Guide](QUICKSTART.md) - 5-minute setup
- [Postman Guide](POSTMAN_GUIDE.md) - API testing guide
- [Start Here](START_HERE.md) - Entry point for developers

## Security

- JWT token authentication
- PAQ Wallet OTP verification
- Role-based access control
- Document validation
- CORS protection
- HTTPS in production

---

**Built for Guatemala with Django REST Framework + PAQ Wallet**

Last Updated: November 2025
