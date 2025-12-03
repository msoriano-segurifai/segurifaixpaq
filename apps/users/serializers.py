from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class PhoneTokenObtainPairSerializer(serializers.Serializer):
    """Custom serializer that authenticates using phone number instead of email"""

    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        phone = attrs.get('phone', '').strip().replace('-', '').replace(' ', '')
        password = attrs.get('password', '')

        # Remove country code if present
        if phone.startswith('+502'):
            phone = phone[4:]
        elif phone.startswith('502'):
            phone = phone[3:]

        # Try to find user by phone number (with various formats)
        user = None
        phone_formats = [phone, f'+502{phone}', f'502{phone}']

        for phone_format in phone_formats:
            try:
                user = User.objects.get(phone_number__icontains=phone_format[-8:])
                break
            except User.DoesNotExist:
                continue
            except User.MultipleObjectsReturned:
                # If multiple users, try exact match
                try:
                    user = User.objects.get(phone_number=phone_format)
                    break
                except User.DoesNotExist:
                    continue

        if user is None:
            raise serializers.ValidationError({
                'phone': 'No se encontró un usuario con este número de teléfono.'
            })

        if not user.is_active:
            raise serializers.ValidationError({
                'phone': 'Esta cuenta está desactivada.'
            })

        if not user.check_password(password):
            raise serializers.ValidationError({
                'password': 'Contraseña incorrecta.'
            })

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user
        }


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone_number', 'role',
            'address', 'city', 'state', 'postal_code', 'country',
            'emergency_contact_name', 'emergency_contact_phone',
            'paq_wallet_id', 'profile_image', 'is_active', 'is_verified',
            'date_joined', 'updated_at'
        )
        read_only_fields = ('id', 'date_joined', 'updated_at', 'is_active', 'is_verified')


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')

    class Meta:
        model = User
        fields = (
            'email', 'password', 'password2', 'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'gender', 'role', 'address', 'city', 'state', 'postal_code', 'country'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number',
            'date_of_birth', 'gender', 'address', 'city', 'state', 'postal_code', 'country',
            'emergency_contact_name', 'emergency_contact_phone',
            'paq_wallet_id', 'profile_image', 'role', 'date_joined'
        )
        read_only_fields = ('id', 'email', 'role', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm New Password')

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
