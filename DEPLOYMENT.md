# SegurifAI x PAQ - Production Deployment Guide

## Quick Start (AWS Elastic Beanstalk)

### Prerequisites

1. **AWS Account** with admin access
2. **AWS CLI** installed and configured
3. **EB CLI** installed: `pip install awsebcli`
4. **Domain name** (optional but recommended)

### Step 1: Configure Environment Variables

Copy the production template and fill in your values:

```bash
cp .env.production .env
```

**Required variables:**
- `SECRET_KEY` - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `PAQ_SSO_SECRET` - Coordinate with PAQ team (min 32 characters)
- `PAQ_WALLET_*` - Production credentials from PAQ

### Step 2: Initialize AWS

```bash
# Configure AWS CLI
aws configure

# Initialize Elastic Beanstalk
eb init segurifai --platform python-3.11 --region us-east-1
```

### Step 3: Create Environment

```bash
# Create production environment with database
eb create segurifai-prod \
  --database \
  --database.engine postgres \
  --database.instance db.t3.micro \
  --elb-type application \
  --instance_type t3.small
```

### Step 4: Set Environment Variables

```bash
eb setenv \
  SECRET_KEY="your-secret-key" \
  DEBUG=False \
  ALLOWED_HOSTS="segurifai.gt,api.segurifai.gt" \
  PAQ_SSO_SECRET="your-paq-sso-secret" \
  PAQ_WALLET_ID_CODE="your-rep-id" \
  PAQ_WALLET_USER="your-user" \
  PAQ_WALLET_PASSWORD="your-password"
```

### Step 5: Deploy

```bash
eb deploy
```

### Step 6: Verify

```bash
# Check status
eb status

# View logs
eb logs

# Open in browser
eb open
```

---

## Domain Setup with Cloudflare

### 1. Add Domain to Cloudflare

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Add your domain (e.g., `segurifai.gt`)
3. Update nameservers at your registrar

### 2. Configure DNS Records

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | api | your-eb-url.elasticbeanstalk.com | Proxied |
| CNAME | @ | your-eb-url.elasticbeanstalk.com | Proxied |
| CNAME | www | segurifai.gt | Proxied |

### 3. SSL/TLS Settings

1. Go to **SSL/TLS** > **Overview**
2. Set mode to **Full (strict)**
3. Enable **Always Use HTTPS**
4. Enable **Automatic HTTPS Rewrites**

### 4. Security Settings

1. Go to **Security** > **WAF**
2. Enable **Bot Fight Mode**
3. Create firewall rules as needed

### 5. Update Django Settings

Add your domain to `ALLOWED_HOSTS` in environment:

```bash
eb setenv ALLOWED_HOSTS="segurifai.gt,api.segurifai.gt,www.segurifai.gt"
```

---

## Alternative: Docker Deployment

### Local Testing

```bash
# Build and run locally
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop
docker-compose down
```

### Production with Docker

```bash
# Build production image
docker build -t segurifai:prod .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag segurifai:prod YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/segurifai:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/segurifai:latest
```

---

## Production Checklist

Before going live, verify:

- [ ] `DEBUG=False`
- [ ] Unique `SECRET_KEY` (50+ characters)
- [ ] `PAQ_SSO_SECRET` coordinated with PAQ team
- [ ] Production PAQ credentials configured
- [ ] Database is PostgreSQL (not SQLite)
- [ ] SSL/HTTPS enabled
- [ ] Cloudflare protection active
- [ ] Health check passing: `/api/health/`
- [ ] Error tracking (Sentry) configured

---

## Monitoring

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/health/` | Full health check (DB, cache) |
| `/api/health/ping/` | Simple ping (load balancer) |
| `/api/health/ready/` | Readiness probe (K8s) |
| `/api/health/live/` | Liveness probe (K8s) |

### Logs

```bash
# View EB logs
eb logs

# Stream logs
eb logs --stream
```

### CloudWatch

- CPU/Memory utilization
- Request count
- Error rate
- Response time

---

## Troubleshooting

### Common Issues

**502 Bad Gateway**
- Check if app is running: `eb health`
- View logs: `eb logs`

**Database Connection Error**
- Verify RDS security group allows EB instances
- Check `DB_*` environment variables

**Static Files Not Loading**
- Run `collectstatic` during deploy (handled by .ebextensions)
- Verify S3 bucket permissions if using S3

---

## Cost Estimate (Monthly)

| Service | Estimate |
|---------|----------|
| EC2 t3.small (1 instance) | $15 |
| RDS db.t3.micro | $25 |
| Load Balancer | $20 |
| S3 (10GB) | $2 |
| Data Transfer | $5 |
| **Total** | **~$70/month** |

Scale up as needed. Production recommendation: 2+ instances behind ALB.

---

## Support

- **Issues**: https://github.com/segurifai/backend/issues
- **PAQ Support**: support@paq.com.gt
- **AWS Support**: AWS Console > Support
