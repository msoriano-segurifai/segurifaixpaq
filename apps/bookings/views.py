from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import Booking, BookingStatusHistory
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    BookingUpdateSerializer,
    BookingCancelSerializer,
    BookingRatingSerializer,
    BookingStatusUpdateSerializer
)


class BookingViewSet(viewsets.ModelViewSet):
    """
    SegurifAI Booking API ViewSet

    Full CRUD operations for bookings:
    - POST   /api/bookings/           - Create a new booking
    - GET    /api/bookings/           - List user's bookings (paginated)
    - GET    /api/bookings/{id}/      - Get booking details
    - PUT    /api/bookings/{id}/      - Update booking (full update)
    - PATCH  /api/bookings/{id}/      - Partial update booking
    - DELETE /api/bookings/{id}/      - Delete booking (admin only)

    Additional actions:
    - POST /api/bookings/{id}/cancel/       - Cancel a booking
    - POST /api/bookings/{id}/rate/         - Rate a completed booking
    - POST /api/bookings/{id}/status/       - Update status (admin only)
    - GET  /api/bookings/my/                - Get current user's bookings
    - GET  /api/bookings/upcoming/          - Get upcoming bookings
    - GET  /api/bookings/history/           - Get past bookings
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['reference_code', 'service_name', 'location_address']
    ordering_fields = ['scheduled_date', 'created_at', 'status', 'priority']
    ordering = ['-scheduled_date', '-created_at']

    def get_queryset(self):
        """
        Filter bookings based on user role:
        - Admin/Staff: Can see all bookings
        - Providers: Can see assigned bookings
        - Users: Can only see their own bookings
        """
        user = self.request.user

        if user.role in ['ADMIN', 'SEGURIFAI_TEAM', 'MAWDY_ADMIN']:
            queryset = Booking.objects.all()
        elif user.role in ['PROVIDER', 'MAWDY_FIELD_TECH']:
            queryset = Booking.objects.filter(
                Q(assigned_provider=user) | Q(user=user)
            )
        else:
            queryset = Booking.objects.filter(user=user)

        # Optional filters from query params
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        service_type = self.request.query_params.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)

        return queryset.select_related('user', 'assigned_provider')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return BookingListSerializer
        elif self.action == 'create':
            return BookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        return BookingDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create a new booking"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        # Return full details
        detail_serializer = BookingDetailSerializer(booking)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a booking (full or partial)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if user owns the booking or is admin
        if instance.user != request.user and not request.user.role in ['ADMIN', 'SEGURIFAI_TEAM', 'MAWDY_ADMIN']:
            return Response(
                {'error': 'No tienes permiso para modificar esta reserva'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full details
        detail_serializer = BookingDetailSerializer(instance)
        return Response(detail_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a booking (admin only or owner if pending)"""
        instance = self.get_object()

        # Only admin can delete, or owner if still pending
        is_admin = request.user.role in ['ADMIN', 'SEGURIFAI_TEAM', 'MAWDY_ADMIN']
        is_owner_pending = instance.user == request.user and instance.status == Booking.Status.PENDING

        if not (is_admin or is_owner_pending):
            return Response(
                {'error': 'No tienes permiso para eliminar esta reserva'},
                status=status.HTTP_403_FORBIDDEN
            )

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def my(self, request):
        """Get current user's bookings"""
        queryset = Booking.objects.filter(user=request.user).order_by('-scheduled_date', '-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming bookings (scheduled for today or future)"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            scheduled_date__gte=today,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
        ).order_by('scheduled_date', 'scheduled_time')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get past/completed bookings"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            Q(scheduled_date__lt=today) |
            Q(status__in=[Booking.Status.COMPLETED, Booking.Status.CANCELLED, Booking.Status.NO_SHOW])
        ).order_by('-scheduled_date', '-completed_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()

        # Check permission
        if booking.user != request.user and not request.user.role in ['ADMIN', 'SEGURIFAI_TEAM', 'MAWDY_ADMIN']:
            return Response(
                {'error': 'No tienes permiso para cancelar esta reserva'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BookingCancelSerializer(data=request.data, context={'booking': booking})
        serializer.is_valid(raise_exception=True)

        # Track status change
        previous_status = booking.status

        # Cancel the booking
        booking.cancel(reason=serializer.validated_data.get('reason', ''))

        # Log status change
        BookingStatusHistory.objects.create(
            booking=booking,
            previous_status=previous_status,
            new_status=Booking.Status.CANCELLED,
            changed_by=request.user,
            notes=serializer.validated_data.get('reason', 'Cancelado por el usuario')
        )

        detail_serializer = BookingDetailSerializer(booking)
        return Response(detail_serializer.data)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate a completed booking"""
        booking = self.get_object()

        # Only the booking owner can rate
        if booking.user != request.user:
            return Response(
                {'error': 'Solo puedes calificar tus propias reservas'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BookingRatingSerializer(data=request.data, context={'booking': booking})
        serializer.is_valid(raise_exception=True)

        booking.rate(
            rating=serializer.validated_data['rating'],
            comment=serializer.validated_data.get('comment', '')
        )

        detail_serializer = BookingDetailSerializer(booking)
        return Response(detail_serializer.data)

    @action(detail=True, methods=['post'], url_path='status')
    def update_status(self, request, pk=None):
        """Update booking status (admin/provider only)"""
        booking = self.get_object()

        # Check permission
        is_admin = request.user.role in ['ADMIN', 'SEGURIFAI_TEAM', 'MAWDY_ADMIN']
        is_assigned_provider = booking.assigned_provider == request.user

        if not (is_admin or is_assigned_provider):
            return Response(
                {'error': 'No tienes permiso para actualizar el estado de esta reserva'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BookingStatusUpdateSerializer(data=request.data, context={'booking': booking})
        serializer.is_valid(raise_exception=True)

        previous_status = booking.status
        new_status = serializer.validated_data['status']

        # Update status
        booking.status = new_status

        # Handle special status updates
        if new_status == Booking.Status.COMPLETED:
            booking.completed_at = timezone.now()
            booking.completion_notes = serializer.validated_data.get('notes', '')
        elif new_status == Booking.Status.CANCELLED:
            booking.cancelled_at = timezone.now()
            booking.cancellation_reason = serializer.validated_data.get('notes', '')

        # Assign provider if provided
        if 'assigned_provider' in serializer.validated_data:
            from apps.users.models import User
            provider_id = serializer.validated_data['assigned_provider']
            if provider_id:
                booking.assigned_provider = get_object_or_404(User, pk=provider_id)
            else:
                booking.assigned_provider = None

        booking.save()

        # Log status change
        BookingStatusHistory.objects.create(
            booking=booking,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=request.user,
            notes=serializer.validated_data.get('notes', '')
        )

        detail_serializer = BookingDetailSerializer(booking)
        return Response(detail_serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get booking statistics for the current user or all (admin)"""
        user = request.user
        is_admin = user.role in ['ADMIN', 'SEGURIFAI_TEAM', 'MAWDY_ADMIN']

        if is_admin:
            queryset = Booking.objects.all()
        else:
            queryset = Booking.objects.filter(user=user)

        today = timezone.now().date()

        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status=Booking.Status.PENDING).count(),
            'confirmed': queryset.filter(status=Booking.Status.CONFIRMED).count(),
            'in_progress': queryset.filter(status=Booking.Status.IN_PROGRESS).count(),
            'completed': queryset.filter(status=Booking.Status.COMPLETED).count(),
            'cancelled': queryset.filter(status=Booking.Status.CANCELLED).count(),
            'upcoming': queryset.filter(
                scheduled_date__gte=today,
                status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
            ).count(),
            'today': queryset.filter(scheduled_date=today).count(),
        }

        return Response(stats)
