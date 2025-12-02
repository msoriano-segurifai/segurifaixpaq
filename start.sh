#!/bin/bash
set -e

echo "=== SegurifAI x PAQ Starting ==="
echo "PORT is: $PORT"

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Migrations complete ==="
echo "=== Starting Gunicorn on port ${PORT:-8000} ==="

exec gunicorn segurifai_backend.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
