# Railway + Supabase Deployment Guide

This guide walks you through deploying SegurifAI x PAQ to Railway with Supabase as the database.

## Prerequisites

- GitHub account (repository: https://github.com/msoriano-segurifai/segurifaixpaq)
- Railway account (https://railway.app)
- Supabase account (https://supabase.com)
- GoDaddy domain (optional)

---

## Step 1: Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Click **New Project**
3. Fill in:
   - **Name**: `segurifai-paq`
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to Guatemala (e.g., `us-east-1`)
4. Wait for project to be created (~2 minutes)

### Get Database Credentials

1. Go to **Settings** → **Database**
2. Copy the **Connection string (URI)** - it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

### Get API Keys

1. Go to **Settings** → **API**
2. Copy:
   - **Project URL**: `https://xxxx.supabase.co`
   - **anon public key**: `eyJhbG...`
   - **service_role key**: `eyJhbG...` (keep secret!)

---

## Step 2: Deploy to Railway

### Option A: One-Click Deploy (Recommended)

1. Go to [Railway](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select `msoriano-segurifai/segurifaixpaq`
4. Railway will auto-detect the configuration

### Option B: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to GitHub repo
railway link

# Deploy
railway up
```

---

## Step 3: Configure Environment Variables

In Railway Dashboard → Your Project → **Variables**, add:

### Required Variables

```env
# Django
DEBUG=False
SECRET_KEY=your-django-secret-key-here
DJANGO_SETTINGS_MODULE=segurifai_paq.settings
ALLOWED_HOSTS=your-app.up.railway.app

# Database (from Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_MAPS_API_KEY=AIza...

# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbG...
```

### Optional Variables

```env
# PAQ Wallet
PAQ_API_URL=https://api.paqwallet.com
PAQ_API_KEY=your-key
PAQ_MERCHANT_ID=your-merchant-id

# Twilio (SMS)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
```

---

## Step 4: Run Migrations

Railway runs migrations automatically via the `Procfile`. To manually run:

```bash
# In Railway CLI
railway run python manage.py migrate
railway run python manage.py seed_subscription_plans
railway run python manage.py seed_elearning
railway run python manage.py createsuperuser
```

---

## Step 5: Connect GoDaddy Domain (Optional)

### In Railway:
1. Go to your project → **Settings** → **Domains**
2. Click **Add Custom Domain**
3. Enter your domain: `yourdomain.com`
4. Railway will show you the required DNS records

### In GoDaddy:
1. Go to **My Products** → **DNS**
2. Add records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | @ | your-app.up.railway.app | 600 |
| CNAME | www | your-app.up.railway.app | 600 |
| CNAME | api | your-app.up.railway.app | 600 |

3. Wait for DNS propagation (up to 48 hours)

### SSL Certificate
Railway automatically provisions SSL certificates via Let's Encrypt.

---

## Step 6: Verify Deployment

1. **Check Logs**: Railway Dashboard → Deployments → View Logs
2. **Health Check**: Visit `https://your-app.up.railway.app/api/health/`
3. **Admin Panel**: Visit `https://your-app.up.railway.app/admin/`

---

## Troubleshooting

### Database Connection Issues
```python
# Test connection
railway run python -c "from supabase_config import get_django_database_config; print(get_django_database_config())"
```

### Static Files Not Loading
```bash
railway run python manage.py collectstatic --noinput
```

### Migration Errors
```bash
# Reset migrations (careful in production!)
railway run python manage.py migrate --fake-initial
```

### View Logs
```bash
railway logs
```

---

## Architecture Overview

```
┌─────────────────┐
│   GoDaddy       │
│   (DNS)         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Railway       │────▶│   Supabase      │
│                 │     │   PostgreSQL    │
│  ┌───────────┐  │     └─────────────────┘
│  │  Django   │  │
│  │  Backend  │  │     ┌─────────────────┐
│  └───────────┘  │────▶│   Anthropic     │
│                 │     │   (AI API)      │
│  ┌───────────┐  │     └─────────────────┘
│  │   React   │  │
│  │  Frontend │  │     ┌─────────────────┐
│  │  (Static) │  │────▶│   Google Maps   │
│  └───────────┘  │     │   (Tracking)    │
│                 │     └─────────────────┘
└─────────────────┘
```

---

## Estimated Costs

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Railway | $5 credit/month | ~$10-20/month |
| Supabase | 500MB database | $25/month (8GB) |
| Anthropic | Pay per use | ~$5-20/month |
| Google Maps | $200 credit | Pay per use |
| **Total** | **~$0-5/month** | **~$40-65/month** |

---

## Quick Commands

```bash
# Deploy
railway up

# View logs
railway logs

# Run Django command
railway run python manage.py <command>

# Open shell
railway run python manage.py shell

# Connect to database
railway run python manage.py dbshell

# Reset gamification (production)
railway run python manage.py reset_all_gamification --dry-run
```

---

## Support

- Railway Docs: https://docs.railway.app
- Supabase Docs: https://supabase.com/docs
- Django Docs: https://docs.djangoproject.com
