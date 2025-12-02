# Multi-stage Dockerfile for SegurifAI x PAQ
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

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

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port (Railway will set $PORT)
EXPOSE 8000

# Start command - Railway sets $PORT environment variable
CMD python manage.py migrate --noinput && gunicorn segurifai_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
