from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RegisterView
from .paq_auth_views import (
    paq_sso_authenticate,
    paq_sso_redirect,
    paq_phone_login,
    paq_quick_login,
    paq_link_account,
)
from .profile_views import user_full_profile

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # PAQ SSO - Main entry point (button click from PAQ app)
    path('auth/paq/sso/', paq_sso_authenticate, name='paq-sso'),
    path('auth/paq/sso/redirect/', paq_sso_redirect, name='paq-sso-redirect'),

    # PAQ Phone Login (when embedded in PAQ Wallet app)
    path('auth/paq/phone-login/', paq_phone_login, name='paq-phone-login'),

    # Development only
    path('auth/paq/quick-login/', paq_quick_login, name='paq-quick-login'),

    # Account linking (existing users)
    path('auth/paq/link/', paq_link_account, name='paq-link-account'),

    # Note: Register is kept for internal/admin use only
    path('register/', RegisterView.as_view(), name='register'),

    # Full profile with e-learning and subscription
    path('full-profile/', user_full_profile, name='user-full-profile'),

    path('', include(router.urls)),
]
