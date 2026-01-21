from rest_framework import serializers
from .models import Payment
from members.models import Member
from gym.models import MembershipPlan

class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment records (Internal Tracking).
    NOTE: All payments are manual. 'payment_method' tracks the offline method used.
    """
    
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    plan_name = serializers.CharField(source='membership_plan.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'member', 'member_name', 
            'membership_plan', 'plan_name',
            'amount', 'payment_method', 
            'payment_date', 
            'period_start', 'period_end', 
            'notes', 
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
        
    def validate(self, data):
        """
        Validation:
        1. Member and Plan must belong to same activity type?
           (Technically enforced by Member model but good to check)
        2. Amount must be positive.
        """
        if data.get('amount') <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
            
        return data
