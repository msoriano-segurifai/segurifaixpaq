from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet

# Create router and register viewset
router = DefaultRouter()
router.register(r'', BookingViewSet, basename='booking')

app_name = 'bookings'

urlpatterns = [
    path('', include(router.urls)),
]

"""
API Endpoints:

# CRUD Operations
POST   /api/bookings/                  - Create a new booking
GET    /api/bookings/                  - List bookings (filtered by role)
GET    /api/bookings/{id}/             - Get booking details
PUT    /api/bookings/{id}/             - Full update booking
PATCH  /api/bookings/{id}/             - Partial update booking
DELETE /api/bookings/{id}/             - Delete booking (admin only)

# Custom Actions
GET    /api/bookings/my/               - Get current user's bookings
GET    /api/bookings/upcoming/         - Get upcoming bookings
GET    /api/bookings/history/          - Get past/completed bookings
GET    /api/bookings/stats/            - Get booking statistics
POST   /api/bookings/{id}/cancel/      - Cancel a booking
POST   /api/bookings/{id}/rate/        - Rate a completed booking
POST   /api/bookings/{id}/status/      - Update status (admin/provider)

# Query Parameters for listing:
- status: Filter by status (PENDING, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED)
- service_type: Filter by service type (ROADSIDE, HEALTH, etc.)
- date_from: Filter by scheduled date (>=)
- date_to: Filter by scheduled date (<=)
- search: Search in reference_code, service_name, location_address
- ordering: Order by scheduled_date, created_at, status, priority
"""
