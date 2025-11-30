"""
Admin Dashboard URL Configuration

Includes:
- SegurifAI Admin dashboard (full access to all data)
- PAQ Admin dashboard (payment/transaction data)
- MAWDY Admin dashboard (dispatch/technician data)
"""
from django.urls import path
from .views import (
    dashboard_overview,
    revenue_report,
    user_report,
    assistance_report,
    subscription_report,
    provider_report,
    recent_activity,
)
from .dashboard_views import (
    live_provider_map,
    segurifai_full_dashboard,
    paq_dashboard_overview,
    paq_transaction_history,
    mawdy_dashboard_overview,
    mawdy_tech_list,
    mawdy_job_history,
    active_dispatch_realtime,
    dispatch_action_logs,
)

urlpatterns = [
    # SegurifAI Admin - Main Dashboard
    path('overview/', dashboard_overview, name='dashboard-overview'),
    path('activity/', recent_activity, name='recent-activity'),
    path('full/', segurifai_full_dashboard, name='full-dashboard'),
    path('providers/map/', live_provider_map, name='live-provider-map'),

    # SegurifAI Admin - Reports
    path('revenue/', revenue_report, name='revenue-report'),
    path('users/', user_report, name='user-report'),
    path('assistance/', assistance_report, name='assistance-report'),
    path('subscriptions/', subscription_report, name='subscription-report'),
    path('providers/', provider_report, name='provider-report'),

    # PAQ Admin Dashboard
    path('paq/overview/', paq_dashboard_overview, name='paq-overview'),
    path('paq/transactions/', paq_transaction_history, name='paq-transactions'),

    # MAWDY Admin Dashboard
    path('mawdy/overview/', mawdy_dashboard_overview, name='mawdy-overview'),
    path('mawdy/technicians/', mawdy_tech_list, name='mawdy-technicians'),
    path('mawdy/jobs/', mawdy_job_history, name='mawdy-jobs'),

    # Real-Time Dispatch (All Admin Types)
    path('dispatch/active/', active_dispatch_realtime, name='dispatch-active'),
    path('dispatch/logs/', dispatch_action_logs, name='dispatch-logs'),
]
