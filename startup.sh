#!/bin/bash
set -e

echo "=== SegurifAI Startup Script ==="
echo "Version: 2025-12-09-v1"

echo ""
echo "1. Running database migrations..."
python manage.py migrate --noinput

echo ""
echo "2. Seeding subscription plans..."
python manage.py seed_subscription_plans

echo ""
echo "3. Verifying active plans..."
python manage.py shell -c "
from apps.services.models import ServicePlan
plans = ServicePlan.objects.filter(is_active=True)
print(f'Active plans: {plans.count()}')
for p in plans:
    print(f'  - {p.name} ({p.category.category_type}) - Q{p.price_monthly}')
"

echo ""
echo "4. Starting Gunicorn server..."
exec gunicorn segurifai_backend.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --log-level info
