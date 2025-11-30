from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServicePlanViewSet, UserServiceViewSet, ai_plan_suggestion
from .renewal_views import (
    get_renewal_status,
    toggle_auto_renew,
    initiate_renewal,
    get_my_subscriptions_renewal,
    get_expiring_subscriptions,
    run_renewal_tasks,
)

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'plans', ServicePlanViewSet, basename='service-plan')
router.register(r'user-services', UserServiceViewSet, basename='user-service')
router.register(r'subscriptions', UserServiceViewSet, basename='subscription')  # Alias for frontend

urlpatterns = [
    path('', include(router.urls)),

    # AI Plan Suggestion endpoint
    path('ai/plan-suggestion/', ai_plan_suggestion, name='ai-plan-suggestion'),

    # Subscription Renewal endpoints
    path('renewal/my/', get_my_subscriptions_renewal, name='my-renewals'),
    path('renewal/expiring/', get_expiring_subscriptions, name='expiring-subscriptions'),
    path('renewal/run-tasks/', run_renewal_tasks, name='run-renewal-tasks'),
    path('renewal/<int:subscription_id>/status/', get_renewal_status, name='renewal-status'),
    path('renewal/<int:subscription_id>/auto-renew/', toggle_auto_renew, name='toggle-auto-renew'),
    path('renewal/<int:subscription_id>/renew/', initiate_renewal, name='initiate-renewal'),
]
