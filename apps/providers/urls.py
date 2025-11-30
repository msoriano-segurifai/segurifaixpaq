from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProviderViewSet, ProviderReviewViewSet
from .mawdy_views import (
    get_mawdy_plans,
    get_plan_services,
    get_my_usage,
    check_vehicle_eligibility,
    check_service_availability,
    request_service,
    get_contact_info,
    get_business_rules,
)
from .dispatch_views import (
    get_my_profile,
    go_online,
    go_offline,
    update_location,
    get_available_jobs,
    accept_job,
    decline_job,
    get_active_job,
    mark_arrived,
    start_service,
    complete_job,
    get_earnings,
    get_job_history,
)
from apps.users.profile_views import field_tech_profile

# Create separate routers to avoid path conflicts
provider_router = DefaultRouter()
provider_router.register(r'', ProviderViewSet, basename='provider')

review_router = DefaultRouter()
review_router.register(r'', ProviderReviewViewSet, basename='provider-review')

urlpatterns = [
    # MAWDY Assistance Endpoints
    path('mawdy/plans/', get_mawdy_plans, name='mawdy-plans'),
    path('mawdy/plans/<str:plan_type>/services/', get_plan_services, name='mawdy-plan-services'),
    path('mawdy/plans/<str:plan_type>/my-usage/', get_my_usage, name='mawdy-my-usage'),
    path('mawdy/check-vehicle/', check_vehicle_eligibility, name='mawdy-check-vehicle'),
    path('mawdy/check-service/', check_service_availability, name='mawdy-check-service'),
    path('mawdy/request-service/', request_service, name='mawdy-request-service'),
    path('mawdy/contact/', get_contact_info, name='mawdy-contact'),
    path('mawdy/business-rules/', get_business_rules, name='mawdy-business-rules'),

    # Field Tech Dispatch (Delivery-app style)
    path('dispatch/profile/', get_my_profile, name='dispatch-profile'),
    path('dispatch/my-profile/', field_tech_profile, name='dispatch-my-profile'),
    path('dispatch/online/', go_online, name='dispatch-go-online'),
    path('dispatch/offline/', go_offline, name='dispatch-go-offline'),
    path('dispatch/location/', update_location, name='dispatch-update-location'),
    path('dispatch/jobs/available/', get_available_jobs, name='dispatch-available-jobs'),
    path('dispatch/jobs/active/', get_active_job, name='dispatch-active-job'),
    path('dispatch/jobs/<int:offer_id>/accept/', accept_job, name='dispatch-accept-job'),
    path('dispatch/jobs/<int:offer_id>/decline/', decline_job, name='dispatch-decline-job'),
    path('dispatch/jobs/<int:offer_id>/arrived/', mark_arrived, name='dispatch-mark-arrived'),
    path('dispatch/jobs/<int:offer_id>/start/', start_service, name='dispatch-start-service'),
    path('dispatch/jobs/<int:offer_id>/complete/', complete_job, name='dispatch-complete-job'),
    path('dispatch/earnings/', get_earnings, name='dispatch-earnings'),
    path('dispatch/jobs/history/', get_job_history, name='dispatch-job-history'),

    # Provider Reviews and General
    path('reviews/', include(review_router.urls)),
    path('', include(provider_router.urls)),
]
