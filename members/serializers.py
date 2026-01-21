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
    plan_name = serializers.CharField(source='membership_plan.name', read_only=True)
    
    class Meta:
        model = Member
        fields = [
            'id', 'user', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'gender', 'phone', 'email', 'address',
            'emergency_contact_name', 'emergency_contact_phone',
            'activity_type', 'activity_type_name',
            'membership_plan', 'plan_name',
            'subscription_start', 'subscription_end',
            'membership_status', 'days_remaining',
            'is_kid', 'is_active', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'subscription_start', 'subscription_end', 
            'membership_status', 'days_remaining',
            'is_kid', 'created_at', 'updated_at'
        ]
        
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
