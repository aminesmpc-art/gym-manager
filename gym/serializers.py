from rest_framework import serializers
from .models import Gym, ActivityType, MembershipPlan

class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = ['id', 'name', 'description', 'is_active']

class MembershipPlanSerializer(serializers.ModelSerializer):
    activity_type_name = serializers.CharField(source='activity_type.name', read_only=True)
    
    class Meta:
        model = MembershipPlan
        fields = [
            'id', 'activity_type', 'activity_type_name', 
            'name', 'duration_days', 'price', 
            'is_active', 'description'
        ]

class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ['id', 'name', 'address', 'phone', 'email', 'website', 'logo']
