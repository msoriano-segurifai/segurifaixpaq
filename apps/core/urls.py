"""
Core URL Configuration
======================

Health check, system status, and Google Maps endpoints.

Author: SegurifAI Development Team
"""

from django.urls import path
from .views import (
    health_check,
    health_check_simple,
    readiness_check,
    liveness_check,
)
from .maps_views import (
    geocode,
    reverse_geocode_view,
    directions,
    eta,
    autocomplete,
    distance,
)

app_name = 'core'

urlpatterns = [
    # Health check endpoints (for load balancers/monitoring)
    path('', health_check, name='health-check'),
    path('ping/', health_check_simple, name='health-ping'),
    path('ready/', readiness_check, name='readiness-check'),
    path('live/', liveness_check, name='liveness-check'),
]

# Maps URL patterns (to be included at /api/maps/)
maps_urlpatterns = [
    path('geocode/', geocode, name='maps-geocode'),
    path('reverse-geocode/', reverse_geocode_view, name='maps-reverse-geocode'),
    path('directions/', directions, name='maps-directions'),
    path('eta/', eta, name='maps-eta'),
    path('autocomplete/', autocomplete, name='maps-autocomplete'),
    path('distance/', distance, name='maps-distance'),
]
