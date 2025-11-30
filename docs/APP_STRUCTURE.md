# SegurifAI x PAQ - Application Structure

## Overview

SegurifAI x PAQ is a Django-based assistance platform for Guatemala, integrating with PAQ Wallet for payments and MAWDY for roadside assistance services.

**Version:** 1.0.0
**Platform:** Django 4.x / Django REST Framework
**Database:** SQLite (dev) / PostgreSQL (prod)
**Authentication:** JWT (Simple JWT)

---

## Directory Structure

```
SegurifAI x PAQ/
├── apps/                           # Django applications
│   ├── core/                       # Core utilities & security
│   │   ├── __init__.py
│   │   └── middleware.py           # Security middleware
│   │
│   ├── users/                      # User management
│   │   ├── management/commands/    # Django commands
│   │   │   └── seed_data.py        # Database seeding
│   │   ├── migrations/
│   │   ├── models.py               # User model
│   │   ├── views.py                # User API views
│   │   ├── serializers.py
│   │   ├── permissions.py          # Custom permissions
│   │   └── urls.py
│   │
│   ├── services/                   # Service plans & subscriptions
│   │   ├── migrations/
│   │   ├── models.py               # ServiceCategory, ServicePlan, UserService
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   │
│   ├── providers/                  # MAWDY providers/assistants
│   │   ├── migrations/
│   │   ├── models.py               # Provider, ProviderLocation, ProviderReview
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   │
│   ├── assistance/                 # Assistance requests & tracking
│   │   ├── migrations/
│   │   ├── models.py               # AssistanceRequest, RequestUpdate, RequestDocument
│   │   ├── views.py                # CRUD operations
│   │   ├── tracking_views.py       # Real-time tracking & dispatch
│   │   ├── document_views.py       # Document upload with AI review
│   │   ├── tracking.py             # TrackingService class
│   │   ├── serializers.py
│   │   └── urls.py
│   │
│   ├── paq_wallet/                 # PAQ Wallet integration
│   │   ├── migrations/
│   │   ├── models.py               # PAQTransaction, PAQWalletLink
│   │   ├── views.py
│   │   ├── services.py             # PAQ API integration
│   │   └── urls.py
│   │
│   ├── gamification/               # Educational modules & rewards
│   │   ├── migrations/
│   │   ├── models.py               # EducationalModule, UserPoints, Achievement
│   │   ├── views.py
│   │   ├── services.py             # Rewards automation
│   │   └── urls.py
│   │
│   ├── promotions/                 # Promo codes & discounts
│   │   ├── migrations/
│   │   ├── models.py               # PromoCode, PromoCodeUsage
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── admin_dashboard/            # Admin analytics
│       ├── views.py                # Analytics endpoints
│       └── urls.py
│
├── segurifai_backend/              # Django project settings
│   ├── __init__.py
│   ├── settings.py                 # Main settings
│   ├── security_settings.py        # Security configuration
│   ├── urls.py                     # Root URL configuration
│   ├── asgi.py
│   └── wsgi.py
│
├── postman/                        # Postman collection & environment
│   ├── SegurifAI_API.postman_collection.json
│   └── SegurifAI_Local.postman_environment.json
│
├── docs/                           # Documentation
│   ├── APP_STRUCTURE.md            # This file
│   └── DB_STRUCTURE.md             # Database documentation
│
├── logs/                           # Log files (gitignored)
├── media/                          # Uploaded files
├── venv/                           # Python virtual environment
├── manage.py
├── requirements.txt
└── start.bat                       # Development startup script
```

---

## Application Modules

### 1. Core (`apps/core/`)

Central utilities and security components.

**Components:**
- `middleware.py` - Security middleware stack

**Middleware Stack:**
```python
MIDDLEWARE = [
    # Django core
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',

    # Security middleware (apps.core.middleware)
    'apps.core.middleware.CloudflareSecurityMiddleware',
    'apps.core.middleware.RequestValidationMiddleware',
    'apps.core.middleware.RateLimitMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
    'apps.core.middleware.AuditLoggingMiddleware',

    # Django rest
    'django.middleware.common.CommonMiddleware',
    ...
]
```

### 2. Users (`apps/users/`)

User authentication and management.

**Models:**
- `User` - Custom user model with roles

**User Roles:**
| Role | Description | Permissions |
|------|-------------|-------------|
| `ADMIN` | SegurifAI Platform Admin | Full access, analytics |
| `PROVIDER` | MAWDY Provider/Assistant | Dispatch, tracking |
| `USER` | Regular user | Request services |

**Key Endpoints:**
- `POST /api/auth/token/` - JWT login
- `POST /api/auth/token/refresh/` - Refresh token
- `GET /api/users/me/` - Current user profile
- `PUT /api/users/me/` - Update profile

### 3. Services (`apps/services/`)

Service plans and subscriptions management.

**Models:**
- `ServiceCategory` - Categories (ROADSIDE, HEALTH, CARD_INSURANCE)
- `ServicePlan` - Plans with GTQ pricing
- `UserService` - User subscriptions

**MAWDY Plans:**
| Plan | Monthly (GTQ) | Yearly (GTQ) |
|------|---------------|--------------|
| MAWDY Drive Inclusion | Q24.41 | Q292.95 |
| MAWDY Drive Optional | Q29.06 | Q348.75 |

**Key Endpoints:**
- `GET /api/services/categories/` - List categories
- `GET /api/services/plans/` - List plans
- `POST /api/services/subscribe/` - Create subscription

### 4. Providers (`apps/providers/`)

MAWDY provider and assistant management.

**Models:**
- `Provider` - Company/assistant profile
- `ProviderLocation` - Real-time GPS location
- `ProviderLocationHistory` - Location history
- `ProviderReview` - User reviews

**Key Endpoints:**
- `GET /api/providers/` - List providers
- `GET /api/providers/nearby/` - Find nearby providers
- `POST /api/providers/reviews/` - Submit review

### 5. Assistance (`apps/assistance/`)

Core assistance request and tracking system.

**Models:**
- `AssistanceRequest` - Service requests
- `RequestUpdate` - Status updates
- `RequestDocument` - Uploaded documents

**Request Flow:**
```
PENDING → ASSIGNED → IN_PROGRESS → COMPLETED
              ↓
          CANCELLED
```

**Tracking States:**
```
SEARCHING → PROVIDER_ASSIGNED → EN_ROUTE → ARRIVING → ARRIVED → IN_SERVICE → COMPLETED
```

**Key Endpoints:**

*Request Management:*
- `POST /api/assistance/requests/` - Create request
- `GET /api/assistance/requests/` - List requests
- `GET /api/assistance/requests/{id}/` - Request detail
- `POST /api/assistance/requests/{id}/cancel/` - Cancel request

*Real-Time Tracking:*
- `GET /api/assistance/tracking/active/` - Active requests
- `GET /api/assistance/tracking/{id}/` - Tracking info
- `POST /api/assistance/tracking/update-location/` - Update location
- `POST /api/assistance/tracking/{id}/arrived/` - Mark arrived
- `POST /api/assistance/tracking/{id}/start/` - Start service
- `POST /api/assistance/tracking/{id}/completed/` - Complete service

*Public Tracking (SSO/PAQ):*
- `GET /api/assistance/tracking/public/{token}/` - Public tracking (no auth)

*Dispatch (MAWDY Assistants):*
- `GET /api/assistance/dispatch/available/` - Available jobs
- `POST /api/assistance/dispatch/{id}/accept/` - Accept job
- `POST /api/assistance/dispatch/{id}/depart/` - Start en route
- `GET /api/assistance/dispatch/my-jobs/` - Active jobs

*Documents:*
- `POST /api/assistance/docs/upload/` - Upload document
- `GET /api/assistance/docs/{id}/` - Get documents

### 6. PAQ Wallet (`apps/paq_wallet/`)

PAQ Wallet payment integration.

**Models:**
- `PAQWalletLink` - User wallet linking
- `PAQTransaction` - Payment transactions

**Key Endpoints:**
- `POST /api/wallet/link/` - Link wallet
- `GET /api/wallet/balance/` - Check balance
- `POST /api/wallet/pay/` - Make payment

### 7. Gamification (`apps/gamification/`)

Educational modules and rewards system.

**Models:**
- `EducationalModule` - Learning content
- `QuizQuestion` - Quiz questions
- `Achievement` - Achievements/badges
- `UserPoints` - User points/levels
- `UserProgress` - Module progress

**Levels:**
| Level | Points Required |
|-------|-----------------|
| NOVATO | 0 |
| APRENDIZ | 100 |
| CONOCEDOR | 250 |
| EXPERTO | 500 |
| MAESTRO | 1000 |

**Key Endpoints:**
- `GET /api/educacion/modules/` - List modules
- `POST /api/educacion/modules/{id}/complete/` - Complete module
- `GET /api/educacion/leaderboard/` - Leaderboard
- `GET /api/educacion/achievements/` - User achievements

### 8. Promotions (`apps/promotions/`)

Promotional codes and discounts.

**Models:**
- `PromoCode` - Promo code definitions
- `PromoCodeUsage` - Usage tracking

**Key Endpoints:**
- `POST /api/promotions/validate/` - Validate code
- `POST /api/promotions/apply/` - Apply code

### 9. Admin Dashboard (`apps/admin_dashboard/`)

Analytics and reporting for admins.

**Access Levels:**
- **SegurifAI Admin:** Full platform analytics
- **MAWDY Admin:** Provider-specific analytics

**Key Endpoints:**
- `GET /api/admin/dashboard/stats/` - Platform statistics
- `GET /api/admin/dashboard/users/` - User analytics
- `GET /api/admin/dashboard/requests/` - Request analytics
- `GET /api/admin/dashboard/providers/` - Provider analytics

---

## Security Architecture

### OWASP Top 10 Compliance

| OWASP Category | Implementation |
|----------------|----------------|
| A01: Broken Access Control | Role-based permissions, audit logging |
| A02: Cryptographic Failures | Argon2 password hashing, HTTPS |
| A03: Injection | Input validation middleware, ORM |
| A04: Insecure Design | Defense in depth, fail-secure |
| A05: Security Misconfiguration | Hardened defaults, CSP |
| A06: Vulnerable Components | Regular dependency updates |
| A07: Auth Failures | Rate limiting, strong passwords |
| A08: Data Integrity | CSRF protection, signed JWTs |
| A09: Security Logging | Comprehensive audit logs |
| A10: SSRF | Cloudflare protection, URL validation |

### Rate Limits

| Role | Requests/Minute |
|------|-----------------|
| ADMIN | 1000 |
| MAWDY_ADMIN | 500 |
| PROVIDER | 300 |
| USER | 100 |
| ANONYMOUS | 30 |

### Security Headers

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: [comprehensive policy]
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## API Authentication

### JWT Authentication

```bash
# Login
POST /api/auth/token/
{
    "email": "user@example.com",
    "password": "password123"
}

# Response
{
    "access": "eyJ...",
    "refresh": "eyJ..."
}

# Use in requests
Authorization: Bearer <access_token>
```

### Token Lifetime
- Access Token: 60 minutes
- Refresh Token: 7 days

---

## Development Setup

### Quick Start

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate (Windows)
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Seed database
python manage.py seed_data

# 6. Start server
python manage.py runserver 8001
```

### Using start.bat

```bash
# Simply run:
start.bat
```

This will:
1. Activate virtual environment
2. Set environment variables
3. Run migrations
4. Seed test data
5. Start server on port 8001

---

## Test Credentials

| User Type | Email | Password |
|-----------|-------|----------|
| SegurifAI Admin | admin@segurifai.gt | AdminPass123! |
| MAWDY Admin | admin@mawdy.gt | MawdyAdmin123! |
| MAWDY Provider | soporte@mawdy.gt | MawdyPass123! |
| MAWDY Assistant | grua1@mawdy.gt | Asistente123! |
| Test User | test@segurifai.gt | TestPass123! |

---

## WebSocket Events

Real-time tracking uses WebSocket for live updates:

```javascript
// Connect
ws://localhost:8001/ws/tracking/<request_id>/

// Events
{
    "type": "tracking_update",
    "data": {
        "status": "EN_ROUTE",
        "location": { "lat": 14.625, "lng": -90.51 },
        "eta_minutes": 5
    }
}
```

---

## Deployment Considerations

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure PostgreSQL database
- [ ] Set strong `SECRET_KEY`
- [ ] Set `JWT_SECRET_KEY`
- [ ] Configure Cloudflare
- [ ] Enable HTTPS/HSTS
- [ ] Set up log rotation
- [ ] Configure Redis for caching
- [ ] Set up Celery for background tasks

### Environment Variables

```bash
DJANGO_ENVIRONMENT=production
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>
DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379
CLOUDFLARE_API_KEY=<cloudflare-key>
PAQ_WALLET_API_KEY=<paq-api-key>
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01 | Initial release |

---

*Documentation generated for SegurifAI x PAQ v1.0.0*
