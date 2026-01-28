from rest_framework import serializers
from .models import User, StaffPayment


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - read operations."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'allowed_gender', 'monthly_salary', 'is_active', 'is_archived', 'archived_at', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (staff)."""
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'allowed_gender', 'monthly_salary', 'is_active']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users."""
    password = serializers.CharField(write_only=True, min_length=6, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'allowed_gender', 'monthly_salary', 'is_active']
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class StaffPaymentSerializer(serializers.ModelSerializer):
    """Serializer for StaffPayment - read operations."""
    staff_username = serializers.CharField(source='staff.username', read_only=True)
    period_display = serializers.CharField(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StaffPayment
        fields = [
            'id', 'staff', 'staff_username', 'amount', 'payment_date',
            'period_month', 'period_year', 'period_display',
            'payment_method', 'notes', 'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'created_by']


class StaffPaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating staff payments."""
    
    class Meta:
        model = StaffPayment
        fields = ['staff', 'amount', 'payment_date', 'period_month', 'period_year', 'payment_method', 'notes']
    
    def validate_period_month(self, value):
        if not 1 <= value <= 12:
            raise serializers.ValidationError("Month must be between 1 and 12")
        return value
    
    def validate_period_year(self, value):
        if value < 2000 or value > 2100:
            raise serializers.ValidationError("Year must be between 2000 and 2100")
        return value
    
    def validate(self, attrs):
        # Check if payment for this period already exists
        staff = attrs.get('staff')
        month = attrs.get('period_month')
        year = attrs.get('period_year')
        
        if StaffPayment.objects.filter(staff=staff, period_month=month, period_year=year).exists():
            raise serializers.ValidationError(
                f"Payment for {staff.username} for {month}/{year} already exists"
            )
        return attrs
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
