"""
Core Views for SegurifAI x PAQ
==============================

Health check and system status endpoints for production monitoring.

ISO 27001 Controls:
- A.12.1.3: Capacity management
- A.17.1.1: Information security continuity planning

Author: SegurifAI Development Team
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import time
import logging

logger = logging.getLogger('segurifai.health')


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for load balancers and monitoring systems.

    Returns overall system health status and component checks.

    GET /api/health/

    Response:
    {
        "status": "healthy",
        "timestamp": "2025-01-21T12:00:00Z",
        "version": "1.0.0",
        "checks": {
            "database": "ok",
            "cache": "ok"
        }
    }
    """
    checks = {}
    overall_healthy = True

    # Database check
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_time = round((time.time() - start) * 1000, 2)
        checks['database'] = {
            'status': 'ok',
            'response_time_ms': db_time
        }
    except Exception as e:
        logger.error(f"Health check - Database error: {e}")
        checks['database'] = {
            'status': 'error',
            'error': 'Database connection failed'
        }
        overall_healthy = False

    # Cache check
    try:
        start = time.time()
        cache_key = 'health_check_test'
        cache.set(cache_key, 'ok', 10)
        cache_result = cache.get(cache_key)
        cache_time = round((time.time() - start) * 1000, 2)

        if cache_result == 'ok':
            checks['cache'] = {
                'status': 'ok',
                'response_time_ms': cache_time
            }
        else:
            checks['cache'] = {
                'status': 'degraded',
                'message': 'Cache read/write mismatch'
            }
    except Exception as e:
        logger.warning(f"Health check - Cache error: {e}")
        checks['cache'] = {
            'status': 'unavailable',
            'message': 'Using default cache backend'
        }

    # Build response
    status_code = 200 if overall_healthy else 503

    return JsonResponse({
        'status': 'healthy' if overall_healthy else 'unhealthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'environment': 'production' if not settings.DEBUG else 'development',
        'checks': checks,
    }, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_simple(request):
    """
    Simple health check for basic load balancer probes.

    GET /api/health/ping/

    Returns: 200 OK with minimal response
    """
    return JsonResponse({'status': 'ok'})


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check - indicates if the service is ready to receive traffic.

    Checks:
    - Database connectivity
    - Required configuration present

    GET /api/health/ready/
    """
    ready = True
    details = {}

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        details['database'] = 'ready'
    except Exception:
        details['database'] = 'not_ready'
        ready = False

    # Check required settings
    required_settings = ['SECRET_KEY', 'PAQ_WALLET_EMITE_URL']
    for setting_name in required_settings:
        if not getattr(settings, setting_name, None):
            details[f'config_{setting_name.lower()}'] = 'missing'
            ready = False

    return JsonResponse({
        'ready': ready,
        'details': details,
    }, status=200 if ready else 503)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check - indicates if the service is running.

    GET /api/health/live/

    Always returns 200 if the application is responding.
    """
    return JsonResponse({
        'alive': True,
        'timestamp': timezone.now().isoformat(),
    })
