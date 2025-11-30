from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .rewards_views import get_my_rewards, claim_available_rewards, get_rewards_tiers

router = DefaultRouter()
router.register(r'modulos', views.EducationalModuleViewSet, basename='modulos')
router.register(r'modules', views.EducationalModuleViewSet, basename='modules')  # English alias

urlpatterns = [
    # Spanish endpoints
    path('mi-progreso/', views.mi_progreso, name='mi-progreso'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('logros/', views.logros_disponibles, name='logros'),

    # English aliases for frontend
    path('progress/', views.mi_progreso, name='progress'),
    path('points/', views.mi_progreso, name='points'),  # Returns points data
    path('achievements/', views.logros_disponibles, name='achievements'),

    # Rewards (automated promo codes based on points)
    path('rewards/', get_my_rewards, name='my-rewards'),
    path('rewards/claim/', claim_available_rewards, name='claim-rewards'),
    path('rewards/tiers/', get_rewards_tiers, name='rewards-tiers'),

    # E-learning discount credits
    path('creditos/', views.mis_creditos, name='mis-creditos'),
    path('creditos/historial/', views.historial_creditos, name='historial-creditos'),
    path('creditos/resumen/', views.resumen_creditos, name='resumen-creditos'),

    # English aliases for credits
    path('credits/', views.mis_creditos, name='credits'),
    path('credits/history/', views.historial_creditos, name='credits-history'),

    # My achievements alias
    path('achievements/my/', views.logros_disponibles, name='my-achievements'),

    # Test/Admin: Reset gamification for a user
    path('reset/', views.reset_gamification, name='reset-gamification'),

    path('', include(router.urls)),
]
