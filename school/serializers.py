"""
School-specific serializers.
These extend the base gym serializers with school-specific fields
(teacher fields for staff, student fields for members).
"""
from rest_framework import serializers
from users.models import User, StaffPayment
from members.models import Member
from gym.models import ActivityType, MembershipPlan


# ─── Staff / Teacher Serializers ───────────────────────────────────────────

class SchoolStaffSerializer(serializers.ModelSerializer):
    """Read serializer for school staff (teachers). Includes teacher fields."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'allowed_gender',
            'monthly_salary', 'phone', 'subject', 'classes_taught',
            'qualification', 'is_active', 'is_archived', 'archived_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class SchoolStaffCreateSerializer(serializers.ModelSerializer):
    """Create serializer for school staff (teachers)."""
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'role',
            'allowed_gender', 'monthly_salary', 'phone',
            'subject', 'classes_taught', 'qualification', 'is_active',
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SchoolStaffUpdateSerializer(serializers.ModelSerializer):
    """Update serializer for school staff (teachers)."""
    password = serializers.CharField(write_only=True, min_length=6, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'role', 'allowed_gender',
            'monthly_salary', 'phone', 'subject', 'classes_taught',
            'qualification', 'is_active',
        ]
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# ─── Student Serializers ───────────────────────────────────────────────────

class SchoolStudentSerializer(serializers.ModelSerializer):
    """
    Read serializer for school students.
    Includes school-specific fields: grade_level, parent_name, parent_phone, parent_email.
    """
    
    # Read-only computed fields
    activity_type_name = serializers.CharField(source='activity_type.name', read_only=True)
    activity_name = serializers.CharField(source='activity_type.name', read_only=True)
    plan_name = serializers.CharField(source='membership_plan.name', read_only=True)
    dabt = serializers.DecimalField(source='remaining_debt', max_digits=10, decimal_places=2, read_only=True)
    days_left = serializers.IntegerField(source='days_remaining', read_only=True)
    status = serializers.CharField(source='membership_status', read_only=True)
    photo_url = serializers.ImageField(source='photo', read_only=True)
    payment_status = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(source='membership_plan.price', max_digits=10, decimal_places=2, read_only=True)
    start_date = serializers.DateField(source='subscription_start', read_only=True)
    end_date = serializers.DateField(source='subscription_end', read_only=True)

    class Meta:
        model = Member
        fields = [
            'id', 'user', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'place_of_birth', 'gender', 'age_category',
            'phone', 'whatsapp', 'email', 'address',
            # School-specific fields
            'grade_level', 'parent_name', 'parent_phone', 'parent_email',
            # Standard fields
            'cin', 'member_code', 'photo', 'photo_url',
            'insurance_paid', 'insurance_year', 'amount_paid',
            'remaining_debt', 'dabt', 'payment_status', 'total_price',
            'emergency_contact_name', 'emergency_contact_phone',
            'activity_type', 'activity_type_name', 'activity_name',
            'membership_plan', 'plan_name',
            'subscription_start', 'start_date',
            'subscription_end', 'end_date',
            'membership_status', 'status', 'days_remaining', 'days_left',
            'is_kid', 'is_active', 'is_archived', 'archived_at', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'user', 'subscription_end',
            'membership_status', 'days_remaining', 'remaining_debt',
            'is_kid', 'created_at', 'updated_at',
        ]
    
    def validate(self, data):
        """Validate plan belongs to selected activity type."""
        activity_type = data.get('activity_type')
        membership_plan = data.get('membership_plan')
        
        if activity_type and membership_plan:
            if membership_plan.activity_type != activity_type:
                raise serializers.ValidationError(
                    f"Plan '{membership_plan.name}' does not belong to activity '{activity_type.name}'."
                )
        return data
