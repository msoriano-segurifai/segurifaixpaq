# SegurifAI x PAQ - Production Dockerfile
# Multi-stage build for smaller production image

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r segurifai && useradd -r -g segurifai segurifai

# Copy application code
COPY --chown=segurifai:segurifai . .

# Create required directories
RUN mkdir -p /app/logs /app/staticfiles /app/media && \
    chown -R segurifai:segurifai /app/logs /app/staticfiles /app/media

# Switch to non-root user
USER segurifai

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=segurifai_backend.settings

# Collect static files
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Expose port (Railway provides $PORT)
EXPOSE ${PORT:-8000}

# Start script that handles migrations and dynamic port
CMD python manage.py migrate --noinput && \
    python manage.py seed_subscription_plans || true && \
    gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 120 segurifai_backend.wsgi:application
