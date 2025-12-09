# Multi-stage Dockerfile for SegurifAI x PAQ
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

# Cache bust: 2025-12-08-v5 - FORCE FRESH BUILD - seed command must run
ARG CACHEBUST=20251208v5
ENV FORCE_REBUILD=20251208v5

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN echo "Building frontend at $(date)" && npm run build

# Stage 2: Python application
FROM python:3.11-slim

# Force rebuild - this ENV change invalidates cache
ENV FORCE_REBUILD=20251208v5

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=segurifai_backend.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create staticfiles directory and collect static files
# Use a dummy SECRET_KEY for collectstatic (only used during build)
RUN mkdir -p /app/staticfiles && \
    SECRET_KEY=build-time-secret-key python manage.py collectstatic --noinput --clear

# Run migrations during build (database must be available)
# Note: This runs at build time - ensure DATABASE_URL is set

# Expose port (Railway will set $PORT)
EXPOSE 8000

# Start command - run migrations, seed plans, then gunicorn
# The seed command will rename existing plans and ensure only 3 SegurifAI plans are active
CMD echo "=== Starting SegurifAI ===" && \
    echo "Running migrations..." && \
    python manage.py migrate --noinput && \
    echo "Seeding subscription plans..." && \
    python manage.py seed_subscription_plans && \
    echo "Checking active plans..." && \
    python manage.py shell -c "from apps.services.models import ServicePlan; plans = ServicePlan.objects.filter(is_active=True); print(f'Active plans: {plans.count()}'); [print(f'  - {p.name} (Q{p.price_monthly})') for p in plans]" && \
    echo "=== Starting Gunicorn ===" && \
    gunicorn segurifai_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --log-level info
