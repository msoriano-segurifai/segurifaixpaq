# Multi-stage Dockerfile for SegurifAI x PAQ
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

# Cache bust: 2025-12-04-v6 - Force rebrand ALL plans to SegurifAI
ARG CACHEBUST=1

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN echo "Building frontend at $(date)" && npm run build

# Stage 2: Python application
FROM python:3.11-slim

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

# Start command - run migrations, then gunicorn (other commands run via Railway cron or manually)
CMD python manage.py migrate --noinput && gunicorn segurifai_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --log-level info
