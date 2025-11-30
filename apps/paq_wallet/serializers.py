from rest_framework import serializers
from .models import WalletTransaction


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for Wallet Transaction"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    assistance_request_number = serializers.CharField(source='assistance_request.request_number', read_only=True, allow_null=True)

    class Meta:
        model = WalletTransaction
        fields = (
            'id', 'user', 'user_email', 'user_name', 'transaction_type', 'amount', 'currency',
            'reference_number', 'external_transaction_id', 'assistance_request',
            'assistance_request_number', 'status', 'status_message', 'metadata',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'reference_number', 'created_at', 'updated_at')


class WalletTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Wallet Transaction"""

    class Meta:
        model = WalletTransaction
        fields = (
            'user', 'transaction_type', 'amount', 'currency', 'assistance_request',
            'external_transaction_id', 'metadata'
        )

    def create(self, validated_data):
        # Generate reference number
        import uuid
        reference_number = f'TXN-{uuid.uuid4().hex[:12].upper()}'
        validated_data['reference_number'] = reference_number
        return super().create(validated_data)


class WalletBalanceSerializer(serializers.Serializer):
    """Serializer for Wallet Balance"""

    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    status = serializers.CharField(required=False)
