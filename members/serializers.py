from rest_framework import serializers
from .models import Member
from gym.models import ActivityType, MembershipPlan
from users.serializers import UserSerializer  # You might need to create this first, or just use a simple one inline

class MemberSerializer(serializers.ModelSerializer):
    """
    Serializer for Member model.
    Includes nested details for read operations and validation for write operations.
    """
    
    # Read-only fields to show details
    activity_type_name = serializers.CharField(source='activity_type.name', read_only=True)
    activity_name = serializers.CharField(source='activity_type.name', read_only=True) # Alias
    plan_name = serializers.CharField(source='membership_plan.name', read_only=True)
    dabt = serializers.DecimalField(source='remaining_debt', max_digits=10, decimal_places=2, read_only=True)
    days_left = serializers.IntegerField(source='days_remaining', read_only=True)
    status = serializers.CharField(source='membership_status', read_only=True) # Alias
    photo_url = serializers.ImageField(source='photo', read_only=True)
    
    # Debt tracking fields
    payment_status = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(source='membership_plan.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Member
        fields = [
            'id', 'user', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'place_of_birth', 'gender', 'age_category', 'phone', 'whatsapp', 'email', 'address',
            'cin', 'member_code', 'photo', 'photo_url',
            'insurance_paid', 'insurance_year', 'amount_paid', 'remaining_debt', 'dabt', 'payment_status', 'total_price',
            'emergency_contact_name', 'emergency_contact_phone',
            'activity_type', 'activity_type_name', 'activity_name',
            'membership_plan', 'plan_name',
            'subscription_start', 'start_date', # We need to check if we can alias this easily or just expose explicit field
            'subscription_end', 'end_date',
            'membership_status', 'status', 'days_remaining', 'days_left',
            'is_kid', 'is_active', 'is_archived', 'archived_at', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'subscription_end', 
            'membership_status', 'days_remaining', 'remaining_debt',
            'is_kid', 'created_at', 'updated_at'
        ]
    
    # Aliases for start/end date as requested
    start_date = serializers.DateField(source='subscription_start', read_only=True)
    end_date = serializers.DateField(source='subscription_end', read_only=True)
        
    def validate(self, data):
        """
        Business rule validation:
        1. Plan must belong to the selected ActivityType.
        """
        activity_type = data.get('activity_type')
        membership_plan = data.get('membership_plan')
        
        if activity_type and membership_plan:
            if membership_plan.activity_type != activity_type:
                raise serializers.ValidationError(
                    f"Plan '{membership_plan.name}' does not belong to activity '{activity_type.name}'."
                )
        
        return data
