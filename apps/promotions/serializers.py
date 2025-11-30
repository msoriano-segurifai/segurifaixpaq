"""
Serializers for Promo Codes and Campaigns
"""
from rest_framework import serializers
from .models import PromoCode, PromoCodeUsage, Campaign


class PromoCodeSerializer(serializers.ModelSerializer):
    """Serializer for PromoCode model"""

    discount_type_display = serializers.CharField(
        source='get_discount_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_valid = serializers.BooleanField(read_only=True)
    remaining_uses = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = [
            'id',
            'code',
            'name',
            'description',
            'discount_type',
            'discount_type_display',
            'discount_value',
            'max_discount_amount',
            'max_uses',
            'max_uses_per_user',
            'current_uses',
            'remaining_uses',
            'valid_from',
            'valid_until',
            'minimum_purchase',
            'first_purchase_only',
            'new_users_only',
            'status',
            'status_display',
            'is_valid',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'current_uses', 'created_at', 'updated_at']

    def get_remaining_uses(self, obj):
        if obj.max_uses:
            return max(0, obj.max_uses - obj.current_uses)
        return None


class PromoCodeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating promo codes"""

    class Meta:
        model = PromoCode
        fields = [
            'code',
            'name',
            'description',
            'discount_type',
            'discount_value',
            'max_discount_amount',
            'max_uses',
            'max_uses_per_user',
            'valid_from',
            'valid_until',
            'minimum_purchase',
            'applicable_plans',
            'applicable_categories',
            'first_purchase_only',
            'new_users_only',
            'status'
        ]

    def validate_code(self, value):
        """Ensure code is uppercase and unique"""
        code = value.upper().strip()
        if PromoCode.objects.filter(code__iexact=code).exists():
            raise serializers.ValidationError('Ya existe un codigo con este nombre')
        return code

    def validate(self, data):
        """Validate dates"""
        if data.get('valid_from') and data.get('valid_until'):
            if data['valid_from'] >= data['valid_until']:
                raise serializers.ValidationError({
                    'valid_until': 'La fecha de fin debe ser posterior a la fecha de inicio'
                })
        return data


class PromoCodeUsageSerializer(serializers.ModelSerializer):
    """Serializer for PromoCodeUsage model"""

    promo_code_info = serializers.SerializerMethodField()

    class Meta:
        model = PromoCodeUsage
        fields = [
            'id',
            'promo_code_info',
            'original_price',
            'discount_amount',
            'final_price',
            'used_at'
        ]

    def get_promo_code_info(self, obj):
        return {
            'code': obj.promo_code.code,
            'name': obj.promo_code.name,
            'discount_type': obj.promo_code.discount_type
        }


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for Campaign model"""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    promo_codes_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'id',
            'name',
            'description',
            'promo_codes',
            'promo_codes_count',
            'start_date',
            'end_date',
            'target_audience',
            'budget',
            'status',
            'status_display',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_promo_codes_count(self, obj):
        return obj.promo_codes.count()


class ValidateCodeSerializer(serializers.Serializer):
    """Serializer for code validation request"""

    code = serializers.CharField(max_length=50)
    plan_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
