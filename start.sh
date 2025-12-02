#!/bin/sh
set -e

echo "=== SegurifAI x PAQ Starting ===" >&2
echo "PORT is: $PORT" >&2

echo "=== Running migrations ===" >&2
python manage.py migrate --noinput

echo "=== Migrations complete ===" >&2

PORT="${PORT:-8000}"
echo "=== Starting Gunicorn on port $PORT ===" >&2

gunicorn segurifai_backend.wsgi:application \
    --bind "0.0.0.0:$PORT" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug
