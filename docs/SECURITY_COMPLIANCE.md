# SegurifAI x PAQ Security & Compliance Documentation

## Overview

This document outlines the security controls and compliance measures implemented in the SegurifAI x PAQ platform, ensuring alignment with international security standards and Guatemala-specific regulatory requirements.

---

## Compliance Framework

### ISO/IEC 27001:2022 Alignment

The platform implements controls from the following ISO 27001 Annex A control domains:

| Control Domain | Status | Implementation |
|----------------|--------|----------------|
| A.5 Information Security Policies | Implemented | Security middleware, access policies |
| A.6 Organization of Information Security | Implemented | Role-based access control |
| A.7 Human Resource Security | Partial | User training docs required |
| A.8 Asset Management | Implemented | Data classification system |
| A.9 Access Control | Implemented | RBAC, MFA-ready architecture |
| A.10 Cryptography | Implemented | HMAC integrity, hashing |
| A.11 Physical Security | N/A | Cloud infrastructure |
| A.12 Operations Security | Implemented | Audit logging, monitoring |
| A.13 Communications Security | Implemented | TLS, HTTPS enforcement |
| A.14 Secure Development | Implemented | Input validation, SAST |
| A.15 Supplier Relationships | Implemented | PAQ API security |
| A.16 Incident Management | Implemented | Incident detection & response |
| A.17 Business Continuity | Partial | Backup procedures needed |
| A.18 Compliance | Implemented | Audit trails, retention |

### PCI-DSS v4.0 Compliance

The platform implements PCI-DSS requirements for PAQ Wallet payment processing:

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Req 1: Network Security | Implemented | Cloudflare WAF, firewall rules |
| Req 2: Secure Configurations | Implemented | Secure Django defaults |
| Req 3: Protect Stored Data | Implemented | Tokenization via PAQ, no raw card storage |
| Req 4: Encrypt Transmission | Implemented | TLS 1.2+ for all PAQ API calls |
| Req 5: Anti-Malware | N/A | Cloud infrastructure managed |
| Req 6: Secure Development | Implemented | OWASP guidelines, input validation |
| Req 7: Restrict Access | Implemented | Role-based access control |
| Req 8: Identify & Authenticate | Implemented | JWT with strong authentication |
| Req 9: Physical Access | N/A | Cloud infrastructure |
| Req 10: Log & Monitor | Implemented | PCI-compliant audit logging |
| Req 11: Test Security | Partial | Quarterly scans required |
| Req 12: Information Security Policy | Implemented | Documented policies |

#### PCI-DSS Scope Reduction

SegurifAI uses **PAQ Wallet tokenization** to minimize PCI-DSS scope:
- **No raw card data** is ever stored, processed, or transmitted by SegurifAI
- All payment card interactions happen directly between user and PAQ
- SegurifAI only handles **PAQ tokens** (5-character PAYPAQ codes)
- Transaction references are non-sensitive identifiers

This approach qualifies SegurifAI for **SAQ-A** (lowest PCI-DSS scope).

---

## OWASP Top 10 Coverage

### A01:2021 - Broken Access Control
- **Implementation**: `RateLimitMiddleware`, `require_access` decorator
- **Location**: `apps/core/middleware.py`, `apps/core/compliance.py`

### A02:2021 - Cryptographic Failures
- **Implementation**: HMAC-SHA256 for data integrity, Argon2 password hashing
- **Location**: `apps/core/compliance.py::DataEncryption`

### A03:2021 - Injection
- **Implementation**: `RequestValidationMiddleware` with pattern detection
- **Location**: `apps/core/middleware.py`

### A04:2021 - Insecure Design
- **Implementation**: Defense in depth, security decorators
- **Location**: All view modules

### A05:2021 - Security Misconfiguration
- **Implementation**: Secure defaults, environment-based config
- **Location**: `segurifai_backend/settings.py`

### A06:2021 - Vulnerable Components
- **Implementation**: Dependency monitoring (manual)
- **Location**: `requirements.txt`

### A07:2021 - Authentication Failures
- **Implementation**: JWT with refresh rotation, brute force detection
- **Location**: `apps/core/compliance.py::SecurityIncidentManager`

### A08:2021 - Software and Data Integrity
- **Implementation**: Transaction HMAC verification
- **Location**: `apps/core/compliance.py::PAQTransactionSecurity`

### A09:2021 - Security Logging Failures
- **Implementation**: Comprehensive audit logging
- **Location**: `apps/core/middleware.py::AuditLoggingMiddleware`

### A10:2021 - Server-Side Request Forgery
- **Implementation**: URL validation on external calls
- **Location**: `apps/paq_wallet/services.py`

---

## Data Classification

### Classification Levels

| Level | Description | Examples | Controls |
|-------|-------------|----------|----------|
| **PUBLIC** | Non-sensitive | Service types, pricing | None required |
| **INTERNAL** | Internal use | Analytics, reports | Authentication |
| **CONFIDENTIAL** | Sensitive business | User profiles, transactions | Encryption, masking |
| **RESTRICTED** | Highly sensitive | DPI, financial data | Field encryption, audit |
| **SECRET** | Critical | API keys, passwords | Never logged, encrypted |

### PAQ Data Categories

| Category | Retention | Encryption | Masking |
|----------|-----------|------------|---------|
| `wallet_id` | 7 years | Required | Yes |
| `transaction` | 7 years | Optional | Yes (reference) |
| `balance` | 7 years | Optional | No |
| `personal_id` (DPI) | 7 years | Required | Yes |
| `authentication` | 1 day | Required | Yes |

---

## Access Control Matrix

### Role Permissions

| Resource | USER | PROVIDER | MAWDY_ADMIN | ADMIN |
|----------|------|----------|-------------|-------|
| View own profile | Read | Read | Read | CRUD |
| View own transactions | Read | Read | Read | CRUD |
| Create assistance request | Create | - | - | Create |
| View all requests | - | Own | All | All |
| Accept dispatch jobs | - | Yes | Yes | Yes |
| Process payments | Yes | - | Yes | Yes |
| Issue refunds | - | - | Yes | Yes |
| View audit logs | - | - | - | Yes |
| Manage users | - | - | - | Yes |

### Rate Limits (per minute)

| Role | Limit | Burst |
|------|-------|-------|
| ADMIN | 1000 | 100 |
| MAWDY_ADMIN | 500 | 50 |
| PROVIDER | 300 | 30 |
| USER | 100 | 15 |
| ANONYMOUS | 30 | 5 |

---

## PAQ Transactional Data Security

### Transaction Flow Security

```
User Request
     |
     v
+------------------+
| Input Validation |  <- Amount limits, format checks
+------------------+
     |
     v
+------------------+
| Access Control   |  <- Role verification, MFA check
+------------------+
     |
     v
+------------------+
| Rate Limiting    |  <- Per-user/IP throttling
+------------------+
     |
     v
+------------------+
| Audit Logging    |  <- Pre-transaction log
+------------------+
     |
     v
+------------------+
| PAQ API Call     |  <- TLS 1.2+, timeout controls
+------------------+
     |
     v
+------------------+
| Integrity Hash   |  <- HMAC verification
+------------------+
     |
     v
+------------------+
| Post-Audit Log   |  <- Result logging
+------------------+
```

### Transaction Limits (GTQ)

| Limit Type | Amount |
|------------|--------|
| Minimum transaction | Q1.00 |
| Maximum transaction | Q50,000.00 |
| Daily limit (USER) | Q10,000.00 |
| Daily limit (PROVIDER) | Q100,000.00 |

### Transaction Reference Format

```
TXN-YYYYMMDD-XXXX-XXXX

Example: TXN-20250121-A1B2-C3D4
```

---

## Security Headers

All responses include OWASP-recommended headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(self), microphone=()
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

---

## Cloudflare Integration

### Verified Headers

| Header | Purpose |
|--------|---------|
| `CF-Connecting-IP` | True client IP |
| `CF-IPCountry` | Geolocation filtering |
| `CF-Ray` | Request tracing |
| `CF-Visitor` | HTTPS verification |

### Country Filtering

Default allowed countries (configurable):
- GT (Guatemala) - Primary
- US, MX (Business partners)
- SV, HN, NI, CR, PA, BZ (Central America)

---

## Audit Logging

### Log Format (JSON)

```json
{
  "event_type": "paq.payment.success",
  "timestamp": "2025-01-21T15:30:00Z",
  "user_id": 123,
  "ip_address": "192.***.***.45",
  "resource": "paq_wallet:PAQ-****",
  "action": "PAQ payment",
  "outcome": "success",
  "details": {
    "amount_gtq": 150.00,
    "reference": "TXN-20250121-A1B2-C3D4"
  },
  "request_id": "uuid-here",
  "risk_level": "low"
}
```

### Log Retention

| Log Type | Retention | Storage |
|----------|-----------|---------|
| Security events | 2 years | Encrypted |
| Audit logs | 2 years | Encrypted |
| Transaction logs | 7 years | Encrypted |
| Access logs | 90 days | Compressed |

---

## Incident Response

### Detection Thresholds

| Incident Type | Threshold | Action |
|---------------|-----------|--------|
| Failed logins | 5 in 15 min | Block IP |
| Rate limit hits | 10 consecutive | Alert |
| SQL injection attempt | 1 | Block + Alert |
| XSS attempt | 1 | Block + Alert |

### Incident Severity Levels

| Level | Response Time | Examples |
|-------|---------------|----------|
| Critical | Immediate | Data breach, API compromise |
| High | 1 hour | Brute force attack, injection |
| Medium | 4 hours | Suspicious activity patterns |
| Low | 24 hours | Failed login attempts |

---

## Data Retention Policy

### Guatemala SAT Compliance

Financial records (including PAQ transactions) are retained for 7 years (2555 days) per Guatemala SAT requirements.

### Retention Schedule

| Data Type | Retention | Deletion Method |
|-----------|-----------|-----------------|
| PAQ transactions | 7 years | Secure wipe |
| Assistance records | 5 years | Archive + wipe |
| User profiles | 1 year post-deletion | Anonymization |
| Location data | 90 days | Secure wipe |
| Session data | 30 days | Auto-expire |
| Temporary tokens | 1 day | Auto-expire |

---

## PCI-DSS Data Protection

### Cardholder Data Handling

SegurifAI uses PAQ Wallet's tokenization service, which means:

| Data Element | Stored by SegurifAI? | Notes |
|--------------|----------------------|-------|
| Primary Account Number (PAN) | **Never** | PAQ handles all card data |
| Cardholder Name | **Never** | Not collected |
| Expiration Date | **Never** | Not collected |
| CVV/CVC | **Never** | PCI-DSS strictly prohibits |
| PIN | **Never** | PCI-DSS strictly prohibits |
| PAQ Token | Yes (masked) | 5-char code, expires in 24h |
| Transaction Reference | Yes | Non-sensitive identifier |

### PCI-DSS Compliant Masking (Requirement 3.4)

| Data Type | Input | Masked Output (in logs) |
|-----------|-------|-------------------------|
| PAN (if seen) | `4111 1111 1111 1111` | `4111-11**-****-1111` |
| CVV (if seen) | `cvv: 123` | `cvv:[REDACTED]` |
| PAQ Token | `AB12C` | `***2C` |
| PAQ Wallet ID | `PAQ-AB12-XY34` | `PAQ-AB12-****` |
| Phone (GT) | `+502 1234 5678` | `+502-****-5678` |
| DPI | `1234 56789 0123` | `****-*****-0123` |
| JWT Token | `eyJhbG...` | `[JWT_REDACTED]` |
| API Keys | `api_key: abc123xyz` | `api_key:[REDACTED]` |

### Prohibited Data Fields

Per PCI-DSS Requirement 3.2, the following fields are **never** stored or logged:

```python
PROHIBITED_FIELDS = {
    'cvv', 'cvc', 'cvv2', 'cvc2',  # Card verification codes
    'pin', 'pin_block',             # PIN data
    'track1', 'track2',             # Magnetic stripe data
    'full_pan',                     # Full unmasked PAN
}
```

---

## Authentication Security

### Password Requirements (ISO 27001 A.9.4)

| Requirement | Value | Standard |
|-------------|-------|----------|
| Minimum Length | 12 characters | PCI-DSS v4.0, ISO 27001 |
| Password Hasher | Argon2 | OWASP, PCI-DSS |
| Account Lockout | 5 failed attempts | ISO 27001 A.9.4.2 |
| Session Timeout | 30 minutes | PCI-DSS Req 8.6 |

### Password Hashing Algorithm

```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Primary
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Fallback
]
```

---

## Health Check Endpoints

Production monitoring endpoints for load balancers and orchestration:

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /api/health/` | Full system health check | None |
| `GET /api/health/ping/` | Simple probe | None |
| `GET /api/health/ready/` | Kubernetes readiness | None |
| `GET /api/health/live/` | Kubernetes liveness | None |

---

## Security Configuration

### Environment Variables

```bash
# Security Settings
CLOUDFLARE_ENABLED=true
CLOUDFLARE_VERIFY_IP=true
ALLOWED_COUNTRIES=GT,US,MX,SV,HN,NI,CR,PA,BZ

# Encryption
DATA_ENCRYPTION_KEY=your-32-byte-key-here

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

---

## Compliance Checklist

### Before Deployment

- [ ] SSL/TLS certificate installed
- [ ] Environment variables configured
- [ ] Database encrypted at rest
- [ ] Backup procedures tested
- [ ] Incident response plan documented
- [ ] Staff security training completed

### Monthly Review

- [ ] Review security logs
- [ ] Check rate limit effectiveness
- [ ] Verify backup integrity
- [ ] Update dependencies
- [ ] Review access permissions

### Annual Audit

- [ ] Full security assessment
- [ ] Penetration testing
- [ ] Compliance certification renewal
- [ ] Policy review and update

---

## Contact

**Security Team**: security@segurifai.gt
**Incident Reporting**: incidents@segurifai.gt
**Compliance**: compliance@segurifai.gt

---

*Last Updated: 2025-01-21*
*Version: 1.0.0*
