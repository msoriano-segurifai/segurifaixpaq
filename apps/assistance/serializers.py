from rest_framework import serializers
from .models import AssistanceRequest, RequestUpdate, RequestDocument
from apps.services.models import UserService


class RequestDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Request Document"""

    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = RequestDocument
        fields = (
            'id', 'request', 'uploaded_by', 'uploaded_by_name', 'document_type',
            'file', 'description', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class RequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for Request Update"""

    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = RequestUpdate
        fields = (
            'id', 'request', 'user', 'user_name', 'update_type', 'message',
            'metadata', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class AssistanceRequestSerializer(serializers.ModelSerializer):
    """Serializer for Assistance Request"""

    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    service_category_name = serializers.CharField(source='service_category.name', read_only=True)
    provider_name = serializers.CharField(source='provider.company_name', read_only=True, allow_null=True)
    assigned_tech_name = serializers.CharField(source='assigned_tech.get_full_name', read_only=True, allow_null=True)
    assigned_tech_phone = serializers.CharField(source='assigned_tech.phone_number', read_only=True, allow_null=True)
    updates = RequestUpdateSerializer(many=True, read_only=True)
    documents = RequestDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = AssistanceRequest
        fields = (
            'id', 'request_number', 'user', 'user_name', 'user_email', 'user_phone',
            'user_service', 'service_category', 'service_category_name', 'provider', 'provider_name',
            'assigned_tech', 'assigned_tech_name', 'assigned_tech_phone', 'assigned_at',
            'title', 'description', 'priority', 'location_address', 'location_city',
            'location_state', 'location_latitude', 'location_longitude',
            'vehicle_make', 'vehicle_model', 'vehicle_year', 'vehicle_plate',
            'patient_name', 'patient_age', 'symptoms', 'card_last_four', 'incident_type',
            'status', 'estimated_arrival_time', 'actual_arrival_time', 'completion_time',
            'estimated_cost', 'actual_cost', 'admin_notes', 'cancellation_reason',
            'updates', 'documents', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'request_number', 'assigned_tech', 'assigned_at', 'created_at', 'updated_at')


class AssistanceRequestListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Assistance Request list view"""

    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    service_category_name = serializers.CharField(source='service_category.name', read_only=True)
    provider_name = serializers.CharField(source='provider.company_name', read_only=True, allow_null=True)
    assigned_tech_name = serializers.CharField(source='assigned_tech.get_full_name', read_only=True, allow_null=True)
    assigned_tech_phone = serializers.CharField(source='assigned_tech.phone_number', read_only=True, allow_null=True)

    class Meta:
        model = AssistanceRequest
        fields = (
            'id', 'request_number', 'user_name', 'service_category_name', 'provider_name',
            'assigned_tech_name', 'assigned_tech_phone', 'assigned_at', 'estimated_arrival_time',
            'title', 'priority', 'status', 'location_address', 'location_city', 'location_state',
            'location_latitude', 'location_longitude', 'created_at'
        )


class AssistanceRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Assistance Request"""

    class Meta:
        model = AssistanceRequest
        fields = (
            'user_service', 'service_category', 'title', 'description', 'priority',
            'location_address', 'location_city', 'location_state', 'location_latitude', 'location_longitude',
            'vehicle_make', 'vehicle_model', 'vehicle_year', 'vehicle_plate',
            'patient_name', 'patient_age', 'symptoms', 'card_last_four', 'incident_type'
        )

    def validate(self, attrs):
        user_service = attrs.get('user_service')
        service_category = attrs.get('service_category')
        request_user = self.context['request'].user

        if not service_category:
            raise serializers.ValidationError("Service category is required.")

        # If the client didn't send a subscription, try to attach the user's active one for this category
        if not user_service:
            user_service = (
                UserService.objects
                .filter(
                    user=request_user,
                    status=UserService.Status.ACTIVE,
                    plan__category=service_category
                )
                .order_by('-start_date')
                .first()
            )
            if user_service:
                attrs['user_service'] = user_service

        # If we still don't have a subscription, block the request to keep plan logic intact
        if not user_service:
            raise serializers.ValidationError("Necesitas una suscripcion activa para solicitar asistencia en esta categoria.")

        # Verify user_service belongs to the request user
        if user_service.user != request_user:
            raise serializers.ValidationError("Invalid user service.")

        # Verify user can request service
        if not user_service.can_request_service:
            raise serializers.ValidationError("You have reached the maximum number of requests for this service.")

        # Verify service category matches user service plan category
        if user_service.plan.category != service_category:
            raise serializers.ValidationError("Service category does not match your service plan.")

        return attrs

    def create(self, validated_data):
        from django.db import transaction
        from django.utils import timezone
        from apps.providers.models import Provider, ProviderLocation
        from math import radians, cos, sin, asin, sqrt
        import logging

        logger = logging.getLogger(__name__)

        def haversine(lon1, lat1, lon2, lat2):
            """Calculate distance between two points in km using Haversine formula"""
            lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            km = 6371 * c  # Earth's radius in km
            return km

        validated_data['user'] = self.context['request'].user

        with transaction.atomic():
            # Create the assistance request
            request = super().create(validated_data)

            # Update user service counter (CRITICAL FIX: was not updating before)
            user_service = request.user_service
            if user_service:
                user_service.requests_this_month += 1
                user_service.total_requests += 1
                user_service.save(update_fields=['requests_this_month', 'total_requests'])

            # AUTO-ASSIGN NEAREST MAWDY TECH based on distance
            user_lat = validated_data.get('location_latitude')
            user_lon = validated_data.get('location_longitude')
            service_category = validated_data.get('service_category')

            if user_lat and user_lon:
                try:
                    # Find active providers that serve this category
                    available_providers = Provider.objects.filter(
                        status=Provider.Status.ACTIVE,
                        is_available=True,
                        service_categories=service_category
                    ).select_related('current_location', 'user')

                    # Calculate distance to each provider
                    provider_distances = []
                    for provider in available_providers:
                        # Try current location first, fall back to base location
                        try:
                            if hasattr(provider, 'current_location') and provider.current_location:
                                p_lat = provider.current_location.latitude
                                p_lon = provider.current_location.longitude
                            elif provider.latitude and provider.longitude:
                                p_lat = provider.latitude
                                p_lon = provider.longitude
                            else:
                                continue

                            distance = haversine(user_lon, user_lat, p_lon, p_lat)

                            # Check if within service radius
                            if distance <= provider.service_radius_km:
                                provider_distances.append((provider, distance))
                        except Exception as e:
                            logger.warning(f"Error calculating distance for provider {provider.id}: {e}")
                            continue

                    # Sort by distance and assign nearest
                    if provider_distances:
                        provider_distances.sort(key=lambda x: x[1])
                        nearest_provider, distance = provider_distances[0]

                        request.provider = nearest_provider
                        request.assigned_tech = nearest_provider.user
                        request.assigned_at = timezone.now()
                        request.status = 'ASSIGNED'

                        # Estimate arrival time (assume 30km/h average in city)
                        estimated_minutes = int((distance / 30) * 60) + 5  # +5 for preparation
                        request.estimated_arrival_time = timezone.now() + timezone.timedelta(minutes=estimated_minutes)

                        request.save(update_fields=[
                            'provider', 'assigned_tech', 'assigned_at', 'status', 'estimated_arrival_time'
                        ])

                        logger.info(
                            f"AUTO-ASSIGNED: Request {request.request_number} -> "
                            f"Provider {nearest_provider.company_name} ({distance:.2f}km away)"
                        )

                        # Create update record
                        from .models import RequestUpdate
                        RequestUpdate.objects.create(
                            request=request,
                            user=nearest_provider.user,
                            update_type='STATUS_CHANGE',
                            message=f'Técnico MAWDY asignado automáticamente: {nearest_provider.company_name}. '
                                    f'Distancia: {distance:.1f}km. Tiempo estimado: {estimated_minutes} min.'
                        )
                    else:
                        logger.warning(f"No available providers found for request {request.request_number}")

                except Exception as e:
                    logger.error(f"Auto-assignment error for request {request.request_number}: {e}")

            return request


class AssistanceRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Assistance Request"""

    class Meta:
        model = AssistanceRequest
        fields = (
            'status', 'priority', 'provider', 'estimated_arrival_time', 'actual_arrival_time',
            'completion_time', 'estimated_cost', 'actual_cost', 'admin_notes', 'cancellation_reason'
        )


class RequestUpdateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Request Update"""

    class Meta:
        model = RequestUpdate
        fields = ('request', 'update_type', 'message', 'metadata')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RequestDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Request Document"""

    class Meta:
        model = RequestDocument
        fields = ('request', 'document_type', 'file', 'description')

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)
