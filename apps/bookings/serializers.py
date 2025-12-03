from rest_framework import serializers
from django.utils import timezone
from .models import Booking, BookingStatusHistory


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for booking status history"""
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = BookingStatusHistory
        fields = [
            'id', 'previous_status', 'new_status',
            'changed_by', 'changed_by_name', 'notes', 'created_at'
        ]
        read_only_fields = fields

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return obj.changed_by.get_full_name()
        return None


class BookingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing bookings"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'reference_code', 'service_type', 'service_type_display',
            'service_name', 'status', 'status_display', 'priority', 'priority_display',
            'scheduled_date', 'scheduled_time', 'location_address',
            'user_name', 'created_at'
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        return obj.user.get_full_name()


class BookingDetailSerializer(serializers.ModelSerializer):
    """Full serializer for booking details"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    user_name = serializers.SerializerMethodField()
    assigned_provider_name = serializers.SerializerMethodField()
    status_history = BookingStatusHistorySerializer(many=True, read_only=True)
    is_cancellable = serializers.BooleanField(read_only=True)
    is_ratable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'reference_code',
            'user', 'user_name',
            'service_type', 'service_type_display',
            'service_name', 'description',
            'status', 'status_display',
            'priority', 'priority_display',
            'scheduled_date', 'scheduled_time', 'estimated_duration_minutes',
            'location_address', 'location_latitude', 'location_longitude', 'location_notes',
            'assigned_provider', 'assigned_provider_name',
            'contact_name', 'contact_phone',
            'user_notes', 'admin_notes',
            'cancelled_at', 'cancellation_reason',
            'completed_at', 'completion_notes',
            'rating', 'rating_comment',
            'is_cancellable', 'is_ratable',
            'status_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reference_code', 'user', 'user_name',
            'status_display', 'service_type_display', 'priority_display',
            'assigned_provider_name', 'cancelled_at', 'completed_at',
            'is_cancellable', 'is_ratable', 'status_history',
            'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_assigned_provider_name(self, obj):
        if obj.assigned_provider:
            return obj.assigned_provider.get_full_name()
        return None


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new booking"""

    class Meta:
        model = Booking
        fields = [
            'service_type', 'service_name', 'description',
            'priority',
            'scheduled_date', 'scheduled_time', 'estimated_duration_minutes',
            'location_address', 'location_latitude', 'location_longitude', 'location_notes',
            'contact_name', 'contact_phone',
            'user_notes'
        ]

    def validate_scheduled_date(self, value):
        """Ensure scheduled date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError('La fecha programada no puede ser en el pasado')
        return value

    def validate_scheduled_time(self, value):
        """Validate scheduled time if provided"""
        return value

    def create(self, validated_data):
        """Create booking with the requesting user"""
        user = self.context['request'].user
        validated_data['user'] = user

        # Default contact info from user if not provided
        if not validated_data.get('contact_name'):
            validated_data['contact_name'] = user.get_full_name()
        if not validated_data.get('contact_phone'):
            validated_data['contact_phone'] = user.phone_number

        booking = Booking.objects.create(**validated_data)

        # Create initial status history entry
        BookingStatusHistory.objects.create(
            booking=booking,
            previous_status='',
            new_status=Booking.Status.PENDING,
            changed_by=user,
            notes='Reserva creada'
        )

        return booking


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a booking"""

    class Meta:
        model = Booking
        fields = [
            'service_type', 'service_name', 'description',
            'priority',
            'scheduled_date', 'scheduled_time', 'estimated_duration_minutes',
            'location_address', 'location_latitude', 'location_longitude', 'location_notes',
            'contact_name', 'contact_phone',
            'user_notes'
        ]

    def validate_scheduled_date(self, value):
        """Ensure scheduled date is not in the past for new dates"""
        instance = self.instance
        if instance and instance.scheduled_date != value:
            if value < timezone.now().date():
                raise serializers.ValidationError('La fecha programada no puede ser en el pasado')
        return value

    def validate(self, data):
        """Validate that booking can be updated"""
        instance = self.instance
        if instance and instance.status not in [Booking.Status.PENDING, Booking.Status.CONFIRMED]:
            raise serializers.ValidationError(
                'Solo se pueden modificar reservas pendientes o confirmadas'
            )
        return data


class BookingCancelSerializer(serializers.Serializer):
    """Serializer for cancelling a booking"""
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        booking = self.context.get('booking')
        if booking and not booking.is_cancellable:
            raise serializers.ValidationError(
                'Esta reserva no puede ser cancelada'
            )
        return data


class BookingRatingSerializer(serializers.Serializer):
    """Serializer for rating a completed booking"""
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        booking = self.context.get('booking')
        if booking and not booking.is_ratable:
            raise serializers.ValidationError(
                'Esta reserva no puede ser calificada'
            )
        return data


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating booking status (admin only)"""
    status = serializers.ChoiceField(choices=Booking.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)
    assigned_provider = serializers.IntegerField(required=False, allow_null=True)

    def validate_status(self, value):
        booking = self.context.get('booking')
        if not booking:
            return value

        # Define valid status transitions
        valid_transitions = {
            Booking.Status.PENDING: [
                Booking.Status.CONFIRMED,
                Booking.Status.CANCELLED
            ],
            Booking.Status.CONFIRMED: [
                Booking.Status.IN_PROGRESS,
                Booking.Status.CANCELLED,
                Booking.Status.NO_SHOW,
                Booking.Status.RESCHEDULED
            ],
            Booking.Status.IN_PROGRESS: [
                Booking.Status.COMPLETED,
                Booking.Status.CANCELLED
            ],
            Booking.Status.RESCHEDULED: [
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
                Booking.Status.CANCELLED
            ],
        }

        allowed = valid_transitions.get(booking.status, [])
        if value not in allowed:
            raise serializers.ValidationError(
                f'No se puede cambiar de {booking.get_status_display()} a {dict(Booking.Status.choices)[value]}'
            )

        return value
