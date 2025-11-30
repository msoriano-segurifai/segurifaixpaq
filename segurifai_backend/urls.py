"""
URL configuration for segurifai_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.core.urls import maps_urlpatterns

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health Check (must be accessible without auth for load balancers)
    path('api/health/', include('apps.core.urls')),

    # Google Maps API endpoints
    path('api/maps/', include((maps_urlpatterns, 'maps'))),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication (JWT)
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # API Endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/services/', include('apps.services.urls')),
    path('api/providers/', include('apps.providers.urls')),
    path('api/assistance/', include('apps.assistance.urls')),
    path('api/wallet/', include('apps.paq_wallet.urls')),
    path('api/educacion/', include('apps.gamification.urls')),
    path('api/gamification/', include('apps.gamification.urls')),  # English alias
    path('api/admin/dashboard/', include('apps.admin_dashboard.urls')),
    path('api/admin/', include('apps.users.admin_urls')),
    path('api/promotions/', include('apps.promotions.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
