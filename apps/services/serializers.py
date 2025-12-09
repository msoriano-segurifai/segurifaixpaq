from rest_framework import serializers
from .models import ServiceCategory, ServicePlan, UserService


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for Service Category"""

    class Meta:
        model = ServiceCategory
        fields = ('id', 'name', 'category_type', 'description', 'icon', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class ServicePlanSerializer(serializers.ModelSerializer):
    """Serializer for Service Plan"""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.category_type', read_only=True)

    class Meta:
        model = ServicePlan
        fields = (
            'id', 'category', 'category_name', 'category_type', 'name', 'description',
            'features', 'price_monthly', 'price_yearly', 'max_requests_per_month',
            'coverage_amount', 'is_active', 'is_featured', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ServicePlanListSerializer(serializers.ModelSerializer):
    """Serializer for Service Plan list view - includes all fields frontend needs"""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.category_type', read_only=True)

    class Meta:
        model = ServicePlan
        fields = (
            'id', 'category_type', 'category_name', 'name', 'description',
            'price_monthly', 'price_yearly', 'features', 'is_active', 'is_featured',
            'terms_and_conditions', 'max_requests_per_month', 'coverage_amount'
        )


class UserServiceSerializer(serializers.ModelSerializer):
    """Serializer for User Service"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_category = serializers.CharField(source='plan.category.category_type', read_only=True)
    plan_price = serializers.DecimalField(source='plan.price_monthly', max_digits=10, decimal_places=2, read_only=True)
    plan_features = serializers.JSONField(source='plan.features', read_only=True)
    can_request = serializers.BooleanField(source='can_request_service', read_only=True)

    class Meta:
        model = UserService
        fields = (
            'id', 'user', 'user_email', 'user_name', 'plan', 'plan_name', 'plan_category',
            'plan_price', 'plan_features',
            'status', 'start_date', 'end_date', 'last_renewal_date', 'next_renewal_date',
            'requests_this_month', 'total_requests', 'can_request', 'notes',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'requests_this_month', 'total_requests', 'created_at', 'updated_at')


class UserServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating User Service"""

    class Meta:
        model = UserService
        fields = ('user', 'plan', 'start_date', 'end_date', 'status', 'notes')

    def validate(self, attrs):
        # Check if user already has an active service for the same plan
        user = attrs.get('user')
        plan = attrs.get('plan')

        if UserService.objects.filter(user=user, plan=plan, status=UserService.Status.ACTIVE).exists():
            raise serializers.ValidationError("User already has an active subscription for this plan.")

        return attrs
