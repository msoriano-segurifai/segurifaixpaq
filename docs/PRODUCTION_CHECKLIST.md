# PAQ x SegurifAI MVP Production Checklist

## Overview

This checklist ensures the SegurifAI x PAQ platform is production-ready, covering both frontend and backend requirements. Complete all items before deploying to production.

**Target Environment**: Guatemala (GT)
**Primary Currency**: GTQ (Quetzales)
**Compliance**: ISO 27001, PCI-DSS v4.0, Guatemala SAT

---

## Backend Checklist

### Infrastructure & Deployment

- [ ] **Server Configuration**
  - [ ] Production server provisioned (AWS/GCP/Azure)
  - [ ] PostgreSQL database configured (not SQLite)
  - [ ] Redis cache server configured
  - [ ] Load balancer configured
  - [ ] Auto-scaling policies set

- [ ] **Domain & SSL**
  - [ ] Production domain configured (api.segurifai.gt)
  - [ ] SSL/TLS certificate installed (Let's Encrypt or commercial)
  - [ ] HTTPS enforced (HTTP redirects to HTTPS)
  - [ ] HSTS headers enabled
  - [ ] Certificate auto-renewal configured

- [ ] **Cloudflare Configuration**
  - [ ] Cloudflare DNS configured
  - [ ] WAF rules enabled
  - [ ] DDoS protection active
  - [ ] Bot protection enabled
  - [ ] Rate limiting configured
  - [ ] Country blocking (if required)

### Django Settings

- [ ] **Security Settings**
  - [ ] `DEBUG = False`
  - [ ] `SECRET_KEY` is unique and secure (min 50 chars)
  - [ ] `ALLOWED_HOSTS` configured properly
  - [ ] `CSRF_COOKIE_SECURE = True`
  - [ ] `SESSION_COOKIE_SECURE = True`
  - [ ] `SECURE_SSL_REDIRECT = True`
  - [ ] `SECURE_HSTS_SECONDS = 31536000`
  - [ ] `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
  - [ ] `SECURE_HSTS_PRELOAD = True`
  - [ ] `SECURE_CONTENT_TYPE_NOSNIFF = True`
  - [ ] `X_FRAME_OPTIONS = 'DENY'`

- [ ] **Database**
  - [ ] PostgreSQL connection configured
  - [ ] Database credentials in environment variables
  - [ ] Connection pooling enabled
  - [ ] Database backups scheduled (daily)
  - [ ] Point-in-time recovery enabled

- [ ] **Environment Variables**
  ```bash
  # Required for production
  SECRET_KEY=<secure-random-key>
  DEBUG=False
  ALLOWED_HOSTS=api.segurifai.gt,segurifai.gt

  # Database
  DB_ENGINE=django.db.backends.postgresql
  DB_NAME=segurifai_prod
  DB_USER=segurifai_user
  DB_PASSWORD=<secure-password>
  DB_HOST=<rds-endpoint>
  DB_PORT=5432

  # PAQ SSO Authentication (CRITICAL - must match PAQ app)
  PAQ_SSO_SECRET=<32-char-min-shared-secret>

  # PAQ Wallet Production
  PAQ_WALLET_EMITE_URL=https://www.paq.com.gt/paqpayws/emite.asmx
  PAQ_WALLET_PAQGO_URL=https://www.paq.com.gt/paqgo/paqgo.asmx
  PAQ_WALLET_ID_CODE=<production-rep-id>
  PAQ_WALLET_USER=<production-user>
  PAQ_WALLET_PASSWORD=<production-password>

  # Cloudflare
  CLOUDFLARE_ENABLED=True
  CLOUDFLARE_VERIFY_IP=True

  # JWT
  JWT_ACCESS_TOKEN_LIFETIME=30
  JWT_REFRESH_TOKEN_LIFETIME=1440

  # Data Encryption
  DATA_ENCRYPTION_KEY=<32-byte-key>
  ```

### Security & Compliance

- [ ] **PCI-DSS Compliance**
  - [ ] No raw card data stored anywhere
  - [ ] PAQ tokenization used for all payments
  - [ ] CVV/PIN never logged or stored
  - [ ] PAN masking implemented (show first 6, last 4)
  - [ ] TLS 1.2+ for all PAQ API calls
  - [ ] Quarterly vulnerability scans scheduled

- [ ] **ISO 27001 Controls**
  - [ ] Access control policies documented
  - [ ] Audit logging enabled and tested
  - [ ] Incident response plan documented
  - [ ] Data classification implemented
  - [ ] Encryption at rest configured
  - [ ] Encryption in transit verified

- [ ] **Authentication**
  - [ ] JWT tokens configured with short expiry
  - [ ] Refresh token rotation enabled
  - [ ] Password hashing uses Argon2
  - [ ] Brute force protection active
  - [ ] Account lockout after 5 failed attempts
  - [ ] Password complexity requirements enforced

- [ ] **Rate Limiting**
  - [ ] Per-IP rate limiting configured
  - [ ] Per-user rate limiting configured
  - [ ] Role-based rate limits set
  - [ ] API abuse detection enabled

### API & Endpoints

- [ ] **Endpoint Testing**
  - [ ] All endpoints return correct status codes
  - [ ] Error responses don't leak sensitive info
  - [ ] Input validation on all endpoints
  - [ ] SQL injection protection verified
  - [ ] XSS protection verified
  - [ ] CSRF protection verified

- [ ] **PAQ Wallet Integration**
  - [ ] Production PAQ credentials configured
  - [ ] Token generation tested
  - [ ] Payment processing tested
  - [ ] Refund flow tested
  - [ ] Balance queries tested
  - [ ] Error handling for PAQ timeouts

- [ ] **Real-Time Tracking**
  - [ ] GPS coordinate validation
  - [ ] Location update rate limiting
  - [ ] ETA calculation accuracy
  - [ ] Provider location privacy

### Logging & Monitoring

- [ ] **Logging**
  - [ ] Application logs configured
  - [ ] Security audit logs enabled
  - [ ] PCI-DSS compliant logging (no sensitive data)
  - [ ] Log rotation configured
  - [ ] Log retention policies set (2 years security, 7 years financial)
  - [ ] Centralized logging (CloudWatch/DataDog/etc)

- [ ] **Monitoring & Alerts**
  - [ ] Server health monitoring
  - [ ] API response time monitoring
  - [ ] Error rate alerting
  - [ ] Database connection monitoring
  - [ ] PAQ API availability monitoring
  - [ ] Security incident alerting

### Data & Backups

- [ ] **Database Backups**
  - [ ] Automated daily backups
  - [ ] Backup encryption enabled
  - [ ] Backup restoration tested
  - [ ] Cross-region backup replication
  - [ ] 30-day backup retention

- [ ] **Data Retention**
  - [ ] 7-year retention for financial data (SAT compliance)
  - [ ] 90-day retention for location data
  - [ ] 2-year retention for audit logs
  - [ ] Automated data cleanup jobs

---

## Frontend Checklist

### Build & Deployment

- [ ] **Production Build**
  - [ ] Production build created (`npm run build` or equivalent)
  - [ ] Environment variables set for production
  - [ ] Source maps disabled in production
  - [ ] Bundle size optimized
  - [ ] Code splitting implemented
  - [ ] Tree shaking enabled

- [ ] **Hosting**
  - [ ] CDN configured (Cloudflare/CloudFront)
  - [ ] HTTPS enforced
  - [ ] Compression enabled (gzip/brotli)
  - [ ] Cache headers configured
  - [ ] Service worker for offline support (if applicable)

### Security

- [ ] **API Security**
  - [ ] API base URL points to production
  - [ ] JWT tokens stored securely (httpOnly cookies or secure storage)
  - [ ] Token refresh logic implemented
  - [ ] Logout clears all tokens
  - [ ] API errors don't expose sensitive data

- [ ] **Input Validation**
  - [ ] All forms validated client-side
  - [ ] DPI format validation (Guatemala)
  - [ ] Phone number validation (+502 format)
  - [ ] Amount validation (GTQ limits)
  - [ ] XSS prevention in user inputs

- [ ] **Content Security**
  - [ ] CSP headers configured
  - [ ] No inline scripts (where possible)
  - [ ] External scripts from trusted sources only
  - [ ] No eval() usage
  - [ ] Subresource integrity for CDN assets

### PAQ Wallet UI

- [ ] **Payment Flow**
  - [ ] Token generation UI working
  - [ ] Payment confirmation screen
  - [ ] Transaction status polling
  - [ ] Error handling for failed payments
  - [ ] Retry mechanism for timeouts
  - [ ] Receipt generation/display

- [ ] **Balance Display**
  - [ ] Balance updates on login
  - [ ] Pull-to-refresh for balance
  - [ ] Masked balance option for privacy
  - [ ] Currency formatting (Q 1,234.56)

### Real-Time Tracking UI

- [ ] **Map Integration**
  - [ ] Google Maps/Mapbox configured
  - [ ] Provider location updates in real-time
  - [ ] ETA display accurate
  - [ ] Route visualization
  - [ ] Zoom/pan controls
  - [ ] Offline map fallback

- [ ] **Status Updates**
  - [ ] Status badges clear and visible
  - [ ] Push notifications for status changes
  - [ ] Sound/vibration alerts (optional)
  - [ ] Status history visible

### User Experience

- [ ] **Performance**
  - [ ] First Contentful Paint < 1.5s
  - [ ] Time to Interactive < 3s
  - [ ] Lighthouse score > 80
  - [ ] Images optimized (WebP)
  - [ ] Lazy loading implemented

- [ ] **Accessibility**
  - [ ] Keyboard navigation works
  - [ ] Screen reader compatible
  - [ ] Color contrast meets WCAG AA
  - [ ] Touch targets minimum 44x44px
  - [ ] Spanish language support

- [ ] **Error Handling**
  - [ ] Friendly error messages
  - [ ] Network error handling
  - [ ] Offline state handling
  - [ ] Session expiry handling
  - [ ] Form validation errors clear

### Mobile App (if applicable)

- [ ] **iOS**
  - [ ] App Store submission ready
  - [ ] Privacy policy URL set
  - [ ] App icons all sizes
  - [ ] Splash screens configured
  - [ ] Deep links configured

- [ ] **Android**
  - [ ] Play Store submission ready
  - [ ] Privacy policy URL set
  - [ ] App icons all sizes
  - [ ] Splash screens configured
  - [ ] Deep links configured

---

## Integration Checklist

### PAQ SSO Authentication (CRITICAL)

All SegurifAI access is through PAQ app. No standalone registration.

- [ ] **PAQ SSO Secret Configuration**
  - [ ] `PAQ_SSO_SECRET` environment variable set
  - [ ] Secret is strong (min 32 characters)
  - [ ] Secret shared securely with PAQ team
  - [ ] Token expiry configured (5 minutes default)

- [ ] **PAQ App Integration**
  - [ ] PAQ team has SSO endpoint URL: `/api/users/auth/paq/sso/`
  - [ ] PAQ team has token format documentation
  - [ ] Test SSO flow works end-to-end
  - [ ] User creation from PAQ data verified
  - [ ] JWT token return verified

- [ ] **Token Format for PAQ Team**
  ```
  Token = base64(JSON payload) + "." + HMAC-SHA256 signature

  Payload:
  {
      "phone": "30082653",
      "paq_id": "PAQ-123456",
      "name": "Juan Garcia",
      "email": "juan@email.com",  // optional
      "ts": 1700000000  // Unix timestamp
  }

  Signature = HMAC-SHA256(base64_payload, PAQ_SSO_SECRET)
  ```

- [ ] **Security Verification**
  - [ ] Invalid tokens return 401
  - [ ] Expired tokens (>5 min) return 401
  - [ ] Missing X-PAQ-Token header returns 401
  - [ ] No public endpoints without PAQ auth

### PAQ Wallet Production

- [ ] **Credentials**
  - [ ] Production API credentials received from PAQ
  - [ ] Credentials stored securely (env vars)
  - [ ] Test transaction successful
  - [ ] Webhook endpoints configured (if applicable)

- [ ] **Testing**
  - [ ] Small amount test payment (Q1-5)
  - [ ] Refund test successful
  - [ ] Balance query accurate
  - [ ] Token expiry handling tested
  - [ ] Rate limit handling tested

### MAWDY Provider Integration

- [ ] **Provider Onboarding**
  - [ ] Provider registration flow tested
  - [ ] Document upload working
  - [ ] Verification process documented
  - [ ] Provider dashboard accessible

- [ ] **Dispatch System**
  - [ ] Job assignment working
  - [ ] Location updates working
  - [ ] Status transitions correct
  - [ ] Completion flow tested

---

## Pre-Launch Checklist

### Final Testing

- [ ] **End-to-End Testing**
  - [ ] User registration flow
  - [ ] User login/logout
  - [ ] Create assistance request
  - [ ] PAQ payment flow
  - [ ] Real-time tracking
  - [ ] Provider dispatch flow
  - [ ] Request completion

- [ ] **Load Testing**
  - [ ] 100 concurrent users tested
  - [ ] API response times acceptable
  - [ ] No memory leaks
  - [ ] Database performance acceptable

- [ ] **Security Testing**
  - [ ] Penetration test completed
  - [ ] OWASP Top 10 verified
  - [ ] Dependency vulnerabilities fixed
  - [ ] Security headers verified

### Documentation

- [ ] **Technical Documentation**
  - [ ] API documentation complete
  - [ ] Database schema documented
  - [ ] Deployment procedures documented
  - [ ] Rollback procedures documented

- [ ] **User Documentation**
  - [ ] User guide created
  - [ ] FAQ prepared
  - [ ] Support contact info ready

### Legal & Compliance

- [ ] **Legal**
  - [ ] Terms of Service finalized
  - [ ] Privacy Policy finalized
  - [ ] Cookie Policy (if applicable)
  - [ ] Data processing agreements

- [ ] **Guatemala Compliance**
  - [ ] SAT registration (if required)
  - [ ] Invoice/receipt requirements met
  - [ ] Data protection compliance

---

## Launch Day

### Deployment

- [ ] **Backend**
  - [ ] Database migrations run
  - [ ] Static files collected
  - [ ] Cache cleared
  - [ ] Health check passing
  - [ ] Monitoring active

- [ ] **Frontend**
  - [ ] Production build deployed
  - [ ] CDN cache cleared
  - [ ] SSL certificate valid
  - [ ] DNS propagated

### Verification

- [ ] **Smoke Tests**
  - [ ] Homepage loads
  - [ ] Login works
  - [ ] API endpoints responding
  - [ ] PAQ integration working
  - [ ] Tracking working

### Monitoring

- [ ] **First 24 Hours**
  - [ ] Error rate normal
  - [ ] Response times acceptable
  - [ ] No security alerts
  - [ ] User feedback monitored

---

## Post-Launch

### Ongoing Maintenance

- [ ] **Weekly**
  - [ ] Review error logs
  - [ ] Check security alerts
  - [ ] Monitor performance metrics
  - [ ] Review user feedback

- [ ] **Monthly**
  - [ ] Security updates applied
  - [ ] Dependency updates reviewed
  - [ ] Backup restoration test
  - [ ] Access rights review

- [ ] **Quarterly**
  - [ ] PCI-DSS vulnerability scan
  - [ ] Penetration test
  - [ ] Compliance audit
  - [ ] Disaster recovery test

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Technical Lead | TBD | email@segurifai.gt |
| Security Lead | TBD | security@segurifai.gt |
| PAQ Support | PAQ Guatemala | support@paq.com.gt |
| MAWDY Operations | TBD | operations@mawdy.gt |
| On-Call DevOps | TBD | oncall@segurifai.gt |

---

## Sign-Off

| Checklist Section | Completed By | Date | Signature |
|-------------------|--------------|------|-----------|
| Backend | | | |
| Frontend | | | |
| Security | | | |
| PAQ Integration | | | |
| Final Testing | | | |

---

*Version: 1.0.0*
*Last Updated: 2025-01-21*
