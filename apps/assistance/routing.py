"""
WebSocket URL routing for assistance app
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Location tracking for users watching a specific request
    re_path(
        r'ws/tracking/request/(?P<request_id>\d+)/$',
        consumers.LocationTrackingConsumer.as_asgi()
    ),
    # Location tracking for providers broadcasting their location
    re_path(
        r'ws/tracking/provider/(?P<provider_id>\d+)/$',
        consumers.LocationTrackingConsumer.as_asgi()
    ),
    # Assistance request updates (chat, status changes, etc.)
    re_path(
        r'ws/assistance/(?P<request_id>\d+)/$',
        consumers.AssistanceRequestConsumer.as_asgi()
    ),
]
