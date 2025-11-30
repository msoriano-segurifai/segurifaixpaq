from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WalletTransactionViewSet,
    get_wallet_balance,
    get_wallet_transactions,
    generate_payment_token,
    check_token_status,
    process_paqgo_payment,
    test_payment_flow,
)
from .webhooks import (
    paq_payment_webhook,
    paq_notification_webhook,
    webhook_health_check,
)

router = DefaultRouter()
router.register(r'transactions', WalletTransactionViewSet, basename='wallet-transaction')

urlpatterns = [
    # Existing endpoints
    path('balance/', get_wallet_balance, name='wallet-balance'),
    path('history/', get_wallet_transactions, name='wallet-history'),

    # PAQ-GO Payment Flow endpoints
    path('generate-token/', generate_payment_token, name='generate-token'),
    path('check-token/', check_token_status, name='check-token'),
    path('paqgo/', process_paqgo_payment, name='paqgo-payment'),
    path('test-flow/', test_payment_flow, name='test-payment-flow'),

    # Webhook endpoints (for PAQ callbacks)
    path('webhook/paq/', paq_payment_webhook, name='paq-webhook'),
    path('webhook/paq/notification/', paq_notification_webhook, name='paq-notification'),
    path('webhook/health/', webhook_health_check, name='webhook-health'),

    # Router URLs
    path('', include(router.urls)),
]
