from rest_framework import serializers
from .models import Gym, ActivityType, MembershipPlan

class ActivityTypeSerializer(serializers.ModelSerializer):
    plan_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityType
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'name_ar', 'name_fr', 'is_active', 'order',
            'plan_count', 'member_count'
        ]
        read_only_fields = ['plan_count', 'member_count']
    
    def get_plan_count(self, obj):
        return obj.plans.filter(is_active=True).count()
    
    def get_member_count(self, obj):
        return obj.members.count()

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
