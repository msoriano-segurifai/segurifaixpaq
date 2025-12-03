"""
URL configuration for segurifai_backend project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.core.urls import maps_urlpatterns
import os


def serve_react_app(request):
    """Serve the React frontend index.html"""
    index_path = os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html')
    try:
        with open(index_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse(
            '<h1>Frontend not built</h1><p>Run npm run build in frontend directory</p>',
            content_type='text/html',
            status=404
        )

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

# Catch-all route for React frontend SPA routing (must be last)
# Handles client-side routes like /dashboard, /login, etc.
# WhiteNoise serves index.html at root and /assets/* files
urlpatterns += [
    re_path(r'^(?!api/|admin/|static/|media/|assets/).*$', serve_react_app, name='react-app'),
]
