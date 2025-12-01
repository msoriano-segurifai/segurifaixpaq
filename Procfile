# Procfile for Railway deployment
# This defines the processes to run

# Web process - Django backend with Gunicorn
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn segurifai_paq.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120

# Worker process (optional - for background tasks)
# worker: celery -A segurifai_paq worker --loglevel=info

# Release phase - runs before deployment
release: python manage.py migrate && python manage.py seed_subscription_plans && python manage.py seed_elearning
