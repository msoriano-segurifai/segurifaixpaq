from rest_framework import serializers
from .models import Provider, ProviderReview


class ProviderSerializer(serializers.ModelSerializer):
    """Serializer for Provider"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    service_categories_names = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = (
            'id', 'user', 'user_email', 'user_name', 'company_name', 'business_license', 'tax_id',
            'business_phone', 'business_email', 'website', 'address', 'city', 'state',
            'postal_code', 'country', 'latitude', 'longitude', 'service_categories',
            'service_categories_names', 'service_radius_km', 'service_areas', 'is_available',
            'working_hours', 'rating', 'total_reviews', 'total_completed', 'certificate',
            'insurance_policy', 'status', 'verification_notes', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'rating', 'total_reviews', 'total_completed', 'created_at', 'updated_at')

    def get_service_categories_names(self, obj):
        return [cat.name for cat in obj.service_categories.all()]


class ProviderListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Provider list view"""

    service_categories_names = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = (
            'id', 'company_name', 'city', 'state', 'rating', 'total_reviews',
            'is_available', 'status', 'service_categories_names'
        )

    def get_service_categories_names(self, obj):
        return [cat.name for cat in obj.service_categories.all()]


class ProviderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Provider detail view"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    service_categories_details = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = (
            'id', 'user', 'user_email', 'user_name', 'user_phone', 'company_name',
            'business_license', 'business_phone', 'business_email', 'website',
            'address', 'city', 'state', 'postal_code', 'country', 'latitude', 'longitude',
            'service_categories_details', 'service_radius_km', 'service_areas',
            'is_available', 'working_hours', 'rating', 'total_reviews', 'total_completed',
            'status', 'recent_reviews', 'created_at'
        )

    def get_service_categories_details(self, obj):
        from apps.services.serializers import ServiceCategorySerializer
        return ServiceCategorySerializer(obj.service_categories.all(), many=True).data

    def get_recent_reviews(self, obj):
        recent = obj.reviews.all()[:5]
        return ProviderReviewSerializer(recent, many=True).data


class ProviderReviewSerializer(serializers.ModelSerializer):
    """Serializer for Provider Review"""

    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    provider_name = serializers.CharField(source='provider.company_name', read_only=True)

    class Meta:
        model = ProviderReview
        fields = (
            'id', 'provider', 'provider_name', 'user', 'user_name', 'assistance_request',
            'rating', 'comment', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ProviderReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Provider Review"""

    class Meta:
        model = ProviderReview
        fields = ('provider', 'assistance_request', 'rating', 'comment')

    def validate(self, attrs):
        user = self.context['request'].user
        provider = attrs.get('provider')
        assistance_request = attrs.get('assistance_request')

        # Check if user already reviewed this provider for this request
        if assistance_request and ProviderReview.objects.filter(
            provider=provider,
            user=user,
            assistance_request=assistance_request
        ).exists():
            raise serializers.ValidationError("You have already reviewed this provider for this request.")

        return attrs

    def create(self, validated_data):
        from django.db import transaction
        from django.db.models import Avg, Count

        validated_data['user'] = self.context['request'].user

        with transaction.atomic():
            # Create the review
            review = super().create(validated_data)

            # Update provider rating (CRITICAL FIX: was not updating before)
            provider = review.provider
            stats = provider.reviews.aggregate(
                avg_rating=Avg('rating'),
                total=Count('id')
            )
            provider.rating = round(stats['avg_rating'] or 0, 2)
            provider.total_reviews = stats['total']
            provider.save(update_fields=['rating', 'total_reviews'])

            return review
