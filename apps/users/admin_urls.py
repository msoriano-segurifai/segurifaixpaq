"""
Admin Management URL Configuration

Endpoints for managing team accounts across organizations.
"""
from django.urls import path
from .admin_views import (
    # SegurifAI Admin
    segurifai_list_team,
    segurifai_create_team_member,
    segurifai_list_all_admins,
    # MAWDY Admin
    mawdy_list_team,
    mawdy_create_team_member,
    # PAQ Admin
    paq_list_team,
    paq_create_admin,
    # Common
    toggle_user_status,
)

urlpatterns = [
    # SegurifAI Admin (Super Admin)
    path('segurifai/team/', segurifai_list_team, name='segurifai-list-team'),
    path('segurifai/team/create/', segurifai_create_team_member, name='segurifai-create-team'),
    path('segurifai/all-admins/', segurifai_list_all_admins, name='segurifai-list-all-admins'),

    # MAWDY Admin
    path('mawdy/team/', mawdy_list_team, name='mawdy-list-team'),
    path('mawdy/team/create/', mawdy_create_team_member, name='mawdy-create-team'),

    # PAQ Admin
    path('paq/team/', paq_list_team, name='paq-list-team'),
    path('paq/team/create/', paq_create_admin, name='paq-create-admin'),

    # Common Admin Actions
    path('users/<int:user_id>/toggle-status/', toggle_user_status, name='toggle-user-status'),
]
