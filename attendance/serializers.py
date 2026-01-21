from rest_framework import serializers
from .models import Attendance
from members.models import Member

class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for daily attendance records.
    Enforces business rules for check-in/out.
    """
    
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'member', 'member_name',
            'date', 'check_in_time', 'check_out_time',
            'recorded_by', 'recorded_by_name',
            'created_at'
        ]
        read_only_fields = ['recorded_by', 'created_at']
        
    def validate(self, data):
        """
        Validate attendance logic:
        1. Check-out must be after check-in.
        2. Member must have active membership (unless overridden by Admin?). 
           (Model clean() method already checks this effectively, but good to check here)
        """
        check_in = data.get('check_in_time')
        check_out = data.get('check_out_time')
        member = data.get('member')
        
        # 1. Time validation
        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError("Check-out time must be after check-in time.")
        
        # 2. Status validation (if member is passed)
        # Note: In partial update (PATCH), member might not be in data.
        if member:
            if member.membership_status != 'ACTIVE':
                raise serializers.ValidationError(
                    f"Member {member.full_name} is {member.membership_status}. Cannot record attendance."
                )
                
        return data
