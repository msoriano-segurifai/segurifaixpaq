# Multi-stage Dockerfile for SegurifAI x PAQ
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

# Cache bust: 2025-12-08-v6 - Use startup script for reliable seeding
ARG CACHEBUST=20251208v6

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
ENV STARTUP_VERSION=20251208v6

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

# Copy startup script and make executable
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Start command - use startup script for reliable execution
CMD ["/bin/bash", "/app/startup.sh"]
