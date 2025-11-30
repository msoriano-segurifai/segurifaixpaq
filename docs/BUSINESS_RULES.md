# SegurifAI x PAQ - Business Rules Documentation

## Overview

This document defines the business rules for the SegurifAI x PAQ assistance platform, including evidence review flows, field technician dispatch, and admin review processes.

---

## 1. Evidence Review System

### 1.1 Review Chain by Assistance Type

#### HEALTH Assistance
```
[User Request] → [Form-Based Evidence ONLY] → [AI Form Analysis] → [MAWDY Admin Fallback]
```

**Rules:**
- NO photos allowed for health assistance
- User MUST submit form-based evidence
- AI analyzes form content for completeness and consistency
- If AI confidence >= 70% AND no issues → Auto-approve
- If AI confidence < 70% OR issues detected → Escalate to MAWDY Admin
- MAWDY Admin makes final approve/reject decision

#### ROADSIDE Assistance
```
[User Request] → [AI Photo Analysis] → [Form Fallback] → [MAWDY Admin Fallback]
                        ↓                     ↓                    ↓
                   If fails →            If fails →           Final Decision
```

**Rules:**
- Photos are PRIMARY evidence method
- AI Vision analyzes photos (vehicle, damage, location)
- If AI Photo Analysis fails → User can submit form instead
- Form goes through AI Form Analysis
- If AI Form Analysis fails → Escalate to MAWDY Admin
- MAWDY Admin makes final approve/reject decision

### 1.2 AI Document Analysis (Photos)

| Document Type | Validation Criteria |
|---------------|---------------------|
| PHOTO_VEHICLE | Vehicle visible, image quality, vehicle type identifiable |
| PHOTO_DAMAGE | Damage visible, damage type, severity, appears recent |
| LICENSE_PLATE | Plate visible, plate readable, valid Guatemala format |
| DRIVER_LICENSE | Valid license, photo visible, name readable, not expired |
| INSURANCE_CARD | Valid insurance, holder name, policy number, current |

**AI Confidence Thresholds:**
- >= 85%: Auto-approve
- 70-84%: Auto-approve with notes
- < 70%: Escalate to MAWDY Admin

### 1.3 AI Form Analysis

**Analysis Criteria:**
1. Information consistency (no contradictions)
2. Description completeness (sufficient detail)
3. Damage/symptoms match incident description
4. No red flags or suspicious patterns

**Outcomes:**
| AI Confidence | Issues Found | Action |
|---------------|--------------|--------|
| >= 70% | None | Auto-approve |
| >= 70% | Minor | Auto-approve with notes |
| < 70% | Any | Escalate to MAWDY Admin |
| Any | Major inconsistencies | Escalate to MAWDY Admin |

### 1.4 MAWDY Admin Review

MAWDY Admin team members have authority to:
- **Approve**: Validate evidence and allow request to proceed
- **Reject**: Decline evidence with reason (user notified)
- **Request Info**: Ask user for additional information

**Access Control:**
- SegurifAI Admin: Full access to all reviews
- MAWDY Admin: Access to forms and documents needing review

---

## 2. Field Technician Dispatch System

### 2.1 Dispatch Flow (Delivery-App Style)

```
[Assistance Request Created]
        ↓
[DispatchService.dispatch_job()]
        ↓
[Find Techs within Radius (Haversine)]
        ↓
[Create Job Offers (sorted by distance)]
        ↓
[Send Alerts to Field Techs]
        ↓
[Tech Accepts/Declines within Timeout]
        ↓
[If Declined → Next Tech in Queue]
        ↓
[Job Assigned → Tech En Route]
```

### 2.2 Dispatch Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| MAX_SEARCH_RADIUS | 10 km | Maximum radius to find technicians |
| JOB_OFFER_TIMEOUT | 60 seconds | Time for tech to accept/decline |
| MAX_CONCURRENT_OFFERS | 3 | Max active offers per technician |
| ETA_SPEED_KMH | 30 km/h | Average speed for ETA calculation |

### 2.3 Field Tech States

```
[OFFLINE] ←→ [ONLINE/AVAILABLE]
                    ↓
              [JOB_OFFERED]
                    ↓
              [EN_ROUTE]
                    ↓
              [ARRIVED]
                    ↓
              [IN_SERVICE]
                    ↓
              [COMPLETED] → [ONLINE/AVAILABLE]
```

### 2.4 Vehicle Types

| Vehicle Type | Use Case |
|--------------|----------|
| MOTORCYCLE | General roadside, fast response |
| VAN | Equipment transport, towing |
| TOW_TRUCK | Vehicle towing |
| AMBULANCE | Health emergencies |
| CAR | General assistance |

### 2.5 Earnings Calculation

```python
Base Earning = Distance (km) * Rate per km
+ Service Type Bonus
+ Peak Hours Bonus (if applicable)
+ Customer Rating Bonus
```

### 2.6 Location Updates

- Tech must update location every 30 seconds while on job
- Location history stored for tracking
- ETA recalculated on each location update

---

## 3. Assistance Request States

### 3.1 Request Lifecycle

```
PENDING → ASSIGNED → IN_PROGRESS → COMPLETED
    ↓         ↓           ↓
CANCELLED  CANCELLED   CANCELLED
```

### 3.2 Tracking States

```
SEARCHING → PROVIDER_ASSIGNED → EN_ROUTE → ARRIVING → ARRIVED → IN_SERVICE → COMPLETED
```

### 3.3 State Transitions

| From State | To State | Trigger |
|------------|----------|---------|
| PENDING | ASSIGNED | Provider accepts job |
| PENDING | CANCELLED | User cancels |
| ASSIGNED | IN_PROGRESS | Provider starts service |
| ASSIGNED | CANCELLED | Provider/User cancels |
| IN_PROGRESS | COMPLETED | Service finished |
| IN_PROGRESS | CANCELLED | Emergency cancellation |

---

## 4. PAQ-Only Access (SSO Authentication)

### 4.1 Access Model

**SegurifAI is ONLY accessible through PAQ app. No standalone registration.**

```
[PAQ App] → "SegurifAI" Button → [SSO Token] → [SegurifAI Web App]
```

### 4.2 PAQ SSO Authentication Flow

```
1. User clicks "SegurifAI" button in PAQ app
2. PAQ app generates signed token with user data
3. PAQ app redirects to SegurifAI with token
4. SegurifAI verifies token signature (HMAC-SHA256)
5. SegurifAI creates/retrieves user account
6. User receives JWT tokens for session
```

### 4.3 Token Format

**Token Structure:** `base64(payload).signature`

**Payload:**
```json
{
    "phone": "30082653",
    "paq_id": "PAQ-123456",
    "name": "Juan Garcia",
    "email": "juan@email.com",
    "ts": 1700000000
}
```

**Signature:** `HMAC-SHA256(base64_payload, PAQ_SSO_SECRET)`

### 4.4 Token Validation Rules

| Check | Requirement | Error |
|-------|-------------|-------|
| Format | Must be `payload.signature` | Invalid token format |
| Signature | Must match HMAC-SHA256 | Invalid signature |
| Timestamp | Within 5 minutes | Token expired |
| Phone | Required field | Missing phone |

### 4.5 PAQ Authentication Endpoints

| Endpoint | Method | Use Case |
|----------|--------|----------|
| `/api/users/auth/paq/sso/` | POST | Main SSO entry (button click) |
| `/api/users/auth/paq/sso/redirect/` | GET | URL-based SSO redirect |
| `/api/users/auth/paq/request-otp/` | POST | Alternative OTP flow |
| `/api/users/auth/paq/verify-otp/` | POST | OTP verification |

### 4.6 Per-Request Authentication

For tracking endpoints, PAQ token must be sent in header:

```
X-PAQ-Token: base64payload.signature
```

**Protected Endpoints:**
- `/api/assistance/tracking/paq/{tracking_token}/`
- `/api/assistance/live/paq/{tracking_token}/`

### 4.7 No Public Endpoints

| Removed | Reason |
|---------|--------|
| Public tracking URLs | Replaced with PAQ-authenticated tracking |
| Email/password registration | Only PAQ users allowed |
| Anonymous access | All access requires PAQ token or JWT |

---

## 5. User Roles and Permissions

### 5.1 Role Hierarchy

```
SEGURIFAI_ADMIN (Super Admin)
        ↓
MAWDY_ADMIN (MAWDY Team Admin)
        ↓
MAWDY_PROVIDER / MAWDY_FIELD_TECH
        ↓
USER (End Customer)
```

### 5.2 Permission Matrix

| Action | USER | FIELD_TECH | MAWDY_ADMIN | SEGURIFAI_ADMIN |
|--------|------|------------|-------------|-----------------|
| Create Request | ✓ | ✗ | ✗ | ✓ |
| View Own Requests | ✓ | ✗ | ✓ | ✓ |
| Accept Jobs | ✗ | ✓ | ✗ | ✗ |
| Review Evidence | ✗ | ✗ | ✓ | ✓ |
| Manage Users | ✗ | ✗ | ✓* | ✓ |
| View Analytics | ✗ | ✗ | ✓* | ✓ |

*MAWDY Admin limited to MAWDY-related data

---

## 6. Evidence Form Types

### 6.1 Form Types and Required Fields

#### VEHICLE_DAMAGE Form
| Field | Required | Description |
|-------|----------|-------------|
| vehicle_make | Yes | Vehicle manufacturer |
| vehicle_model | Yes | Vehicle model |
| vehicle_plate | Yes | License plate |
| damage_description | Yes | Detailed damage description |
| damage_location | No | Where on vehicle |
| incident_description | Yes | What happened |
| location_description | Yes | Where it happened |

#### ROADSIDE_ISSUE Form
| Field | Required | Description |
|-------|----------|-------------|
| issue_type | Yes | Type of problem |
| vehicle_make | Yes | Vehicle manufacturer |
| vehicle_model | Yes | Vehicle model |
| vehicle_plate | Yes | License plate |
| location_description | Yes | Current location |
| incident_description | Yes | Description of issue |

#### HEALTH_INCIDENT Form
| Field | Required | Description |
|-------|----------|-------------|
| symptoms_description | Yes | Current symptoms |
| incident_date | Yes | When symptoms started |
| location_description | Yes | Current location |
| medical_history | No | Relevant conditions |
| current_medications | No | Current medications |
| allergies | No | Known allergies |

---

## 7. API Response Codes

### 7.1 Success Responses
- **200 OK**: Successful GET, PUT, PATCH
- **201 Created**: Successful POST creating resource
- **204 No Content**: Successful DELETE

### 7.2 Error Responses
- **400 Bad Request**: Invalid input, validation errors
- **401 Unauthorized**: Not authenticated
- **403 Forbidden**: No permission for action
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Server error

---

## 8. Notification Rules

### 8.1 User Notifications
| Event | Channel | Message |
|-------|---------|---------|
| Request Created | Push | "Su solicitud fue creada" |
| Tech Assigned | Push | "Un tecnico esta en camino" |
| Tech Arrived | Push | "El tecnico ha llegado" |
| Service Complete | Push | "Servicio completado" |
| Evidence Approved | Push | "Su evidencia fue aprobada" |
| Evidence Rejected | Push | "Su evidencia requiere correccion" |

### 8.2 Field Tech Notifications
| Event | Channel | Message |
|-------|---------|---------|
| New Job Available | Push | "Nuevo trabajo disponible cerca" |
| Job Assigned | Push | "Trabajo asignado" |
| Job Cancelled | Push | "Trabajo cancelado" |

---

## 9. Rate Limiting

| Role | Requests/Minute |
|------|-----------------|
| SEGURIFAI_ADMIN | 1000 |
| MAWDY_ADMIN | 500 |
| MAWDY_FIELD_TECH | 300 |
| USER | 100 |
| ANONYMOUS | 30 |

---

## 10. Data Retention

| Data Type | Retention Period |
|-----------|------------------|
| Assistance Requests | 7 years |
| Evidence Forms | 7 years |
| Location History | 90 days |
| Audit Logs | 2 years |
| Session Data | 24 hours |

---

*Document Version: 1.1.0*
*Last Updated: 2025-01-23*
*Changes: Added PAQ-Only Access (SSO Authentication) section*
