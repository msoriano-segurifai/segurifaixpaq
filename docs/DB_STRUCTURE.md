# SegurifAI x PAQ - Database Structure

## Overview

This document describes the database schema for SegurifAI x PAQ platform.

**Database:** SQLite (development) / PostgreSQL (production)
**ORM:** Django ORM
**Migrations:** Django migrations

---

## Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│    User     │────<│  UserService    │>────│  ServicePlan │
└─────────────┘     └─────────────────┘     └──────────────┘
       │                    │                      │
       │                    │                      │
       ▼                    ▼                      ▼
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Provider   │────<│AssistanceRequest│>────│ ServiceCategory  │
└─────────────┘     └─────────────────┘     └──────────────────┘
       │                    │
       │                    │
       ▼                    ▼
┌─────────────────┐  ┌─────────────────┐
│ProviderLocation │  │  RequestUpdate  │
└─────────────────┘  └─────────────────┘
                            │
                            ▼
                     ┌─────────────────┐
                     │ RequestDocument │
                     └─────────────────┘
```

---

## Tables by Application

### 1. Users App (`apps.users`)

#### `users_user`
Custom user model extending Django AbstractUser.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Primary key |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL | Login email |
| `password` | VARCHAR(128) | NOT NULL | Hashed password |
| `first_name` | VARCHAR(150) | | User first name |
| `last_name` | VARCHAR(150) | | User last name |
| `phone_number` | VARCHAR(20) | UNIQUE | Phone number |
| `role` | VARCHAR(20) | NOT NULL | USER, ADMIN, PROVIDER |
| `paq_wallet_id` | VARCHAR(50) | UNIQUE, NULL | PAQ Wallet identifier |
| `profile_picture` | VARCHAR(100) | NULL | Profile image path |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account active |
| `is_staff` | BOOLEAN | DEFAULT FALSE | Staff access |
| `is_superuser` | BOOLEAN | DEFAULT FALSE | Superuser access |
| `date_joined` | DATETIME | AUTO | Registration date |
| `last_login` | DATETIME | NULL | Last login timestamp |

**Indexes:**
- `email` (UNIQUE)
- `phone_number` (UNIQUE)
- `paq_wallet_id` (UNIQUE)
- `role`

---

### 2. Services App (`apps.services`)

#### `services_servicecategory`
Service categories offered.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `name` | VARCHAR(100) | NOT NULL | Category name |
| `category_type` | VARCHAR(20) | UNIQUE | ROADSIDE, HEALTH, CARD_INSURANCE |
| `description` | TEXT | | Category description |
| `icon` | VARCHAR(50) | | Icon identifier |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active status |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

#### `services_serviceplan`
Available service plans with pricing.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `category_id` | INTEGER | FK | Service category |
| `name` | VARCHAR(100) | NOT NULL | Plan name |
| `description` | TEXT | | Plan description |
| `price_monthly` | DECIMAL(10,2) | NOT NULL | Monthly price (GTQ) |
| `price_yearly` | DECIMAL(10,2) | NOT NULL | Yearly price (GTQ) |
| `features` | JSON | DEFAULT [] | Feature list |
| `coverage_details` | JSON | DEFAULT {} | Coverage info |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active status |
| `is_featured` | BOOLEAN | DEFAULT FALSE | Featured plan |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

#### `services_userservice`
User subscriptions to service plans.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `user_id` | UUID | FK | Subscriber |
| `plan_id` | INTEGER | FK | Service plan |
| `status` | VARCHAR(20) | NOT NULL | ACTIVE, EXPIRED, CANCELLED |
| `start_date` | DATE | NOT NULL | Subscription start |
| `end_date` | DATE | NULL | Subscription end |
| `auto_renew` | BOOLEAN | DEFAULT TRUE | Auto-renewal |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

**Indexes:**
- `user_id, plan_id` (UNIQUE)
- `status`
- `end_date`

---

### 3. Providers App (`apps.providers`)

#### `providers_provider`
Provider/assistant profiles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `user_id` | UUID | FK, UNIQUE | Associated user |
| `company_name` | VARCHAR(200) | NOT NULL | Company name |
| `business_license` | VARCHAR(100) | UNIQUE | License number |
| `tax_id` | VARCHAR(50) | | Tax ID (NIT) |
| `business_phone` | VARCHAR(20) | NOT NULL | Contact phone |
| `business_email` | VARCHAR(254) | NOT NULL | Contact email |
| `website` | VARCHAR(200) | | Website URL |
| `address` | TEXT | NOT NULL | Physical address |
| `city` | VARCHAR(100) | NOT NULL | City |
| `state` | VARCHAR(100) | NOT NULL | State/Department |
| `postal_code` | VARCHAR(20) | NOT NULL | Postal code |
| `country` | VARCHAR(100) | DEFAULT 'Guatemala' | Country |
| `latitude` | DECIMAL(9,6) | NULL | HQ latitude |
| `longitude` | DECIMAL(9,6) | NULL | HQ longitude |
| `service_radius_km` | INTEGER | DEFAULT 50 | Service radius |
| `service_areas` | JSON | DEFAULT [] | Service areas |
| `is_available` | BOOLEAN | DEFAULT TRUE | Currently available |
| `working_hours` | JSON | DEFAULT {} | Working schedule |
| `rating` | DECIMAL(3,2) | DEFAULT 0.00 | Average rating |
| `total_reviews` | INTEGER | DEFAULT 0 | Review count |
| `total_completed` | INTEGER | DEFAULT 0 | Completed requests |
| `certificate` | VARCHAR(100) | NULL | Certificate file |
| `insurance_policy` | VARCHAR(100) | NULL | Insurance file |
| `status` | VARCHAR(20) | DEFAULT 'PENDING' | PENDING, ACTIVE, SUSPENDED |
| `verification_notes` | TEXT | | Admin notes |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

**Indexes:**
- `user_id` (UNIQUE)
- `business_license` (UNIQUE)
- `status`
- `latitude, longitude` (for geo queries)

#### `providers_providerlocation`
Real-time provider location.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `provider_id` | INTEGER | FK, UNIQUE | Provider |
| `latitude` | DECIMAL(9,6) | NOT NULL | Current latitude |
| `longitude` | DECIMAL(9,6) | NOT NULL | Current longitude |
| `heading` | FLOAT | NULL | Direction (0-360) |
| `speed` | FLOAT | NULL | Speed (km/h) |
| `accuracy` | FLOAT | NULL | GPS accuracy (m) |
| `is_online` | BOOLEAN | DEFAULT TRUE | Online status |
| `last_updated` | DATETIME | AUTO | Last update |

**Indexes:**
- `provider_id` (UNIQUE)
- `is_online`
- `last_updated`

#### `providers_providerlocationhistory`
Historical location tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `provider_id` | INTEGER | FK | Provider |
| `assistance_request_id` | INTEGER | FK, NULL | Associated request |
| `latitude` | DECIMAL(9,6) | NOT NULL | Latitude |
| `longitude` | DECIMAL(9,6) | NOT NULL | Longitude |
| `heading` | FLOAT | NULL | Direction |
| `speed` | FLOAT | NULL | Speed |
| `recorded_at` | DATETIME | AUTO | Recording time |

**Indexes:**
- `provider_id, recorded_at`
- `assistance_request_id, recorded_at`

#### `providers_providerreview`
Provider reviews from users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `provider_id` | INTEGER | FK | Provider reviewed |
| `user_id` | UUID | FK | Reviewer |
| `assistance_request_id` | INTEGER | FK, NULL | Associated request |
| `rating` | INTEGER | 1-5 | Star rating |
| `comment` | TEXT | | Review comment |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

**Constraints:**
- `UNIQUE(provider_id, user_id, assistance_request_id)`

---

### 4. Assistance App (`apps.assistance`)

#### `assistance_assistancerequest`
Service assistance requests.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `request_number` | VARCHAR(20) | UNIQUE | Tracking number |
| `user_id` | UUID | FK | Requesting user |
| `user_service_id` | INTEGER | FK, NULL | User subscription |
| `service_category_id` | INTEGER | FK, NULL | Service category |
| `provider_id` | INTEGER | FK, NULL | Assigned provider |
| `title` | VARCHAR(200) | NOT NULL | Request title |
| `description` | TEXT | | Request details |
| `location_latitude` | DECIMAL(9,6) | NULL | User latitude |
| `location_longitude` | DECIMAL(9,6) | NULL | User longitude |
| `location_address` | VARCHAR(500) | | User address |
| `location_city` | VARCHAR(100) | | City |
| `priority` | VARCHAR(20) | DEFAULT 'MEDIUM' | LOW, MEDIUM, HIGH, URGENT |
| `status` | VARCHAR(20) | DEFAULT 'PENDING' | Request status |
| `estimated_cost` | DECIMAL(10,2) | NULL | Estimated cost |
| `actual_cost` | DECIMAL(10,2) | NULL | Final cost |
| `estimated_arrival_time` | DATETIME | NULL | ETA |
| `actual_arrival_time` | DATETIME | NULL | Actual arrival |
| `completed_at` | DATETIME | NULL | Completion time |
| `cancellation_reason` | TEXT | | Cancellation reason |
| `notes` | TEXT | | Internal notes |
| `metadata` | JSON | DEFAULT {} | Additional data |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

**Status Values:**
- `PENDING` - New request
- `ASSIGNED` - Provider assigned
- `IN_PROGRESS` - Service in progress
- `COMPLETED` - Service completed
- `CANCELLED` - Request cancelled

**Priority Values:**
- `LOW` - Non-urgent
- `MEDIUM` - Standard
- `HIGH` - High priority
- `URGENT` - Emergency

**Indexes:**
- `request_number` (UNIQUE)
- `user_id`
- `provider_id`
- `status`
- `created_at`
- `location_latitude, location_longitude`

#### `assistance_requestupdate`
Request status updates and timeline.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `request_id` | INTEGER | FK | Parent request |
| `user_id` | UUID | FK, NULL | Update author |
| `update_type` | VARCHAR(50) | NOT NULL | Update type |
| `message` | TEXT | NOT NULL | Update message |
| `metadata` | JSON | DEFAULT {} | Additional data |
| `created_at` | DATETIME | AUTO | Creation timestamp |

**Update Types:**
- `STATUS_CHANGE` - Status changed
- `LOCATION_UPDATE` - Location updated
- `NOTE` - General note
- `DOCUMENT` - Document uploaded
- `PAYMENT` - Payment processed

**Indexes:**
- `request_id, created_at`

#### `assistance_requestdocument`
Documents attached to requests.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `request_id` | INTEGER | FK | Parent request |
| `uploaded_by_id` | UUID | FK | Uploader |
| `document_type` | VARCHAR(50) | NOT NULL | Document type |
| `file` | VARCHAR(100) | NOT NULL | File path |
| `filename` | VARCHAR(255) | NOT NULL | Original filename |
| `file_size` | INTEGER | | Size in bytes |
| `mime_type` | VARCHAR(100) | | MIME type |
| `review_status` | VARCHAR(20) | DEFAULT 'PENDING' | Review status |
| `ai_analysis` | JSON | DEFAULT {} | AI review results |
| `reviewer_notes` | TEXT | | Manual review notes |
| `created_at` | DATETIME | AUTO | Upload timestamp |

**Document Types:**
- `ID_FRONT` - ID front
- `ID_BACK` - ID back
- `LICENSE` - Driver's license
- `VEHICLE_PHOTO` - Vehicle photo
- `DAMAGE_PHOTO` - Damage photo
- `INVOICE` - Invoice
- `OTHER` - Other

**Review Status:**
- `PENDING` - Awaiting review
- `APPROVED` - Document approved
- `REJECTED` - Document rejected
- `NEEDS_REVIEW` - Needs manual review

---

### 5. PAQ Wallet App (`apps.paq_wallet`)

#### `paq_wallet_paqwalletlink`
User wallet connections.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `user_id` | UUID | FK, UNIQUE | User account |
| `wallet_id` | VARCHAR(100) | UNIQUE | PAQ Wallet ID |
| `wallet_token` | VARCHAR(500) | | Encrypted token |
| `is_verified` | BOOLEAN | DEFAULT FALSE | Verification status |
| `linked_at` | DATETIME | AUTO | Link timestamp |
| `last_sync` | DATETIME | NULL | Last sync time |

#### `paq_wallet_paqtransaction`
Payment transactions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `transaction_id` | VARCHAR(100) | UNIQUE | PAQ transaction ID |
| `user_id` | UUID | FK | User |
| `assistance_request_id` | INTEGER | FK, NULL | Related request |
| `transaction_type` | VARCHAR(20) | NOT NULL | PAYMENT, REFUND, REWARD |
| `amount` | DECIMAL(10,2) | NOT NULL | Amount (GTQ) |
| `status` | VARCHAR(20) | NOT NULL | Status |
| `description` | TEXT | | Description |
| `metadata` | JSON | DEFAULT {} | PAQ response data |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `processed_at` | DATETIME | NULL | Processing time |

**Transaction Status:**
- `PENDING` - Awaiting processing
- `COMPLETED` - Successfully processed
- `FAILED` - Transaction failed
- `REFUNDED` - Refunded

---

### 6. Gamification App (`apps.gamification`)

#### `gamification_educationalmodule`
Educational learning modules.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `titulo` | VARCHAR(200) | NOT NULL | Module title |
| `descripcion` | TEXT | | Description |
| `categoria` | VARCHAR(50) | NOT NULL | Category |
| `dificultad` | VARCHAR(20) | DEFAULT 'PRINCIPIANTE' | Difficulty |
| `orden` | INTEGER | DEFAULT 0 | Display order |
| `puntos_completar` | INTEGER | DEFAULT 0 | Completion points |
| `duracion_minutos` | INTEGER | DEFAULT 10 | Duration |
| `contenido` | TEXT | | Markdown content |
| `video_url` | VARCHAR(500) | NULL | Video link |
| `esta_activo` | BOOLEAN | DEFAULT TRUE | Active status |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

**Categories:**
- `PREVENCION` - Prevention
- `SEGURIDAD_VIAL` - Road safety
- `PRIMEROS_AUXILIOS` - First aid
- `FINANZAS` - Finance

**Difficulty Levels:**
- `PRINCIPIANTE` - Beginner
- `INTERMEDIO` - Intermediate
- `AVANZADO` - Advanced

#### `gamification_quizquestion`
Quiz questions for modules.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `modulo_id` | INTEGER | FK | Parent module |
| `pregunta` | TEXT | NOT NULL | Question text |
| `opcion_a` | VARCHAR(500) | NOT NULL | Option A |
| `opcion_b` | VARCHAR(500) | NOT NULL | Option B |
| `opcion_c` | VARCHAR(500) | NOT NULL | Option C |
| `opcion_d` | VARCHAR(500) | NOT NULL | Option D |
| `respuesta_correcta` | CHAR(1) | NOT NULL | A, B, C, or D |
| `explicacion` | TEXT | | Answer explanation |
| `orden` | INTEGER | DEFAULT 0 | Question order |

#### `gamification_achievement`
Available achievements/badges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `nombre` | VARCHAR(100) | UNIQUE | Achievement name |
| `descripcion` | TEXT | | Description |
| `condicion` | VARCHAR(200) | | Unlock condition |
| `icono` | VARCHAR(50) | | Icon identifier |
| `puntos_bonus` | INTEGER | DEFAULT 0 | Bonus points |
| `es_secreto` | BOOLEAN | DEFAULT FALSE | Hidden achievement |
| `created_at` | DATETIME | AUTO | Creation timestamp |

#### `gamification_userpoints`
User points and levels.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `user_id` | UUID | FK, UNIQUE | User |
| `puntos_totales` | INTEGER | DEFAULT 0 | Total points |
| `nivel` | VARCHAR(20) | DEFAULT 'NOVATO' | Current level |
| `racha_dias` | INTEGER | DEFAULT 0 | Day streak |
| `ultima_actividad` | DATE | NULL | Last activity |
| `modulos_completados` | INTEGER | DEFAULT 0 | Completed modules |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

**Levels:**
- `NOVATO` - 0-99 points
- `APRENDIZ` - 100-249 points
- `CONOCEDOR` - 250-499 points
- `EXPERTO` - 500-999 points
- `MAESTRO` - 1000+ points

#### `gamification_userachievement`
User earned achievements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `user_id` | UUID | FK | User |
| `achievement_id` | INTEGER | FK | Achievement |
| `earned_at` | DATETIME | AUTO | Earning timestamp |

**Constraints:**
- `UNIQUE(user_id, achievement_id)`

#### `gamification_userprogress`
User module progress.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `user_id` | UUID | FK | User |
| `modulo_id` | INTEGER | FK | Module |
| `esta_completado` | BOOLEAN | DEFAULT FALSE | Completion status |
| `puntuacion_quiz` | INTEGER | NULL | Quiz score |
| `intentos_quiz` | INTEGER | DEFAULT 0 | Quiz attempts |
| `tiempo_dedicado` | INTEGER | DEFAULT 0 | Time spent (min) |
| `started_at` | DATETIME | AUTO | Start timestamp |
| `completed_at` | DATETIME | NULL | Completion timestamp |

**Constraints:**
- `UNIQUE(user_id, modulo_id)`

---

### 7. Promotions App (`apps.promotions`)

#### `promotions_promocode`
Promotional code definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `code` | VARCHAR(50) | UNIQUE | Promo code |
| `name` | VARCHAR(100) | NOT NULL | Code name |
| `description` | TEXT | | Description |
| `discount_type` | VARCHAR(20) | NOT NULL | PERCENTAGE, FIXED_AMOUNT |
| `discount_value` | DECIMAL(10,2) | NOT NULL | Discount value |
| `max_discount_amount` | DECIMAL(10,2) | NULL | Max discount cap |
| `min_purchase_amount` | DECIMAL(10,2) | DEFAULT 0 | Min purchase |
| `max_uses` | INTEGER | NULL | Total use limit |
| `max_uses_per_user` | INTEGER | DEFAULT 1 | Per-user limit |
| `current_uses` | INTEGER | DEFAULT 0 | Current usage |
| `valid_from` | DATETIME | NOT NULL | Start date |
| `valid_until` | DATETIME | NOT NULL | End date |
| `applicable_services` | JSON | DEFAULT [] | Service IDs |
| `status` | VARCHAR(20) | DEFAULT 'ACTIVE' | Status |
| `created_at` | DATETIME | AUTO | Creation timestamp |
| `updated_at` | DATETIME | AUTO | Update timestamp |

**Discount Types:**
- `PERCENTAGE` - Percentage off
- `FIXED_AMOUNT` - Fixed amount off

**Status:**
- `ACTIVE` - Code is active
- `INACTIVE` - Code disabled
- `EXPIRED` - Code expired

**Indexes:**
- `code` (UNIQUE)
- `status, valid_from, valid_until`

#### `promotions_promocodeusage`
Promo code usage tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Primary key |
| `promo_code_id` | INTEGER | FK | Promo code |
| `user_id` | UUID | FK | User |
| `assistance_request_id` | INTEGER | FK, NULL | Request applied |
| `discount_applied` | DECIMAL(10,2) | NOT NULL | Actual discount |
| `used_at` | DATETIME | AUTO | Usage timestamp |

---

## Database Indexes Summary

### Performance Indexes

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| `users_user` | `email_idx` | `email` | Login lookup |
| `users_user` | `role_idx` | `role` | Role filtering |
| `assistance_assistancerequest` | `status_idx` | `status` | Status filtering |
| `assistance_assistancerequest` | `user_requests_idx` | `user_id, created_at` | User history |
| `assistance_assistancerequest` | `provider_requests_idx` | `provider_id, status` | Provider queue |
| `assistance_assistancerequest` | `geo_idx` | `location_latitude, location_longitude` | Geolocation |
| `providers_provider` | `status_idx` | `status` | Provider filtering |
| `providers_provider` | `geo_idx` | `latitude, longitude` | Nearby search |
| `providers_providerlocation` | `online_idx` | `is_online, last_updated` | Active tracking |

### Foreign Key Relationships

```
users_user (PK: id)
    ├── providers_provider (user_id)
    ├── services_userservice (user_id)
    ├── assistance_assistancerequest (user_id)
    ├── assistance_requestupdate (user_id)
    ├── assistance_requestdocument (uploaded_by_id)
    ├── providers_providerreview (user_id)
    ├── paq_wallet_paqwalletlink (user_id)
    ├── paq_wallet_paqtransaction (user_id)
    ├── gamification_userpoints (user_id)
    ├── gamification_userachievement (user_id)
    ├── gamification_userprogress (user_id)
    └── promotions_promocodeusage (user_id)

services_servicecategory (PK: id)
    ├── services_serviceplan (category_id)
    └── assistance_assistancerequest (service_category_id)

providers_provider (PK: id)
    ├── providers_providerlocation (provider_id)
    ├── providers_providerlocationhistory (provider_id)
    ├── providers_providerreview (provider_id)
    └── assistance_assistancerequest (provider_id)

assistance_assistancerequest (PK: id)
    ├── assistance_requestupdate (request_id)
    ├── assistance_requestdocument (request_id)
    ├── providers_providerlocationhistory (assistance_request_id)
    ├── providers_providerreview (assistance_request_id)
    ├── paq_wallet_paqtransaction (assistance_request_id)
    └── promotions_promocodeusage (assistance_request_id)
```

---

## Data Retention Policies

| Data Type | Retention Period | Action |
|-----------|------------------|--------|
| User accounts | Indefinite | Archive on deletion |
| Assistance requests | 7 years | Archive after 2 years |
| Location history | 90 days | Auto-delete |
| Audit logs | 2 years | Archive and compress |
| Session data | 24 hours | Auto-expire |

---

## Backup Recommendations

### Production Backups

```bash
# Daily full backup
pg_dump -Fc segurifai_db > backup_$(date +%Y%m%d).dump

# Hourly incremental
pg_basebackup -D /backups/incremental -Ft -z -P

# Transaction log archiving
archive_command = 'cp %p /archive/%f'
```

### Backup Schedule

| Type | Frequency | Retention |
|------|-----------|-----------|
| Full | Daily | 30 days |
| Incremental | Hourly | 7 days |
| Transaction logs | Continuous | 14 days |

---

## Migration Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback specific migration
python manage.py migrate app_name migration_name
```

---

*Database documentation for SegurifAI x PAQ v1.0.0*
