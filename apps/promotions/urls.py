"""
Promotions URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    validate_promo_code,
    apply_promo_code,
    get_available_codes,
    get_my_usage_history,
    PromoCodeViewSet,
    CampaignViewSet,
)

router = DefaultRouter()
router.register(r'codes', PromoCodeViewSet, basename='promo-code')
router.register(r'campaigns', CampaignViewSet, basename='campaign')

urlpatterns = [
    # User endpoints
    path('validate/', validate_promo_code, name='validate-promo'),
    path('apply/', apply_promo_code, name='apply-promo'),
    path('available/', get_available_codes, name='available-promos'),
    path('my-usage/', get_my_usage_history, name='my-promo-usage'),

    # Admin endpoints (via router)
    path('', include(router.urls)),
]
