from rest_framework import serializers
from .models import Attendance
from members.models import Member


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for daily attendance records.
    Includes snapshot fields from Smart Check-In system.
    """
    
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)
    activity_name = serializers.CharField(source='activity_at_entry.name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'member', 'member_name',
            'date', 'check_in_time', 'check_out_time',
            'recorded_by', 'recorded_by_name',
            # Snapshot fields
            'activity_at_entry', 'activity_name',
            'status_at_entry', 'debt_at_entry', 'insurance_paid_at_entry',
            # Decision fields
            'checkin_result', 'checkin_reason',
            # Override fields
            'override_used', 'override_reason',
            'created_at'
        ]
        read_only_fields = [
            'recorded_by', 'created_at',
            'activity_at_entry', 'status_at_entry', 
            'debt_at_entry', 'insurance_paid_at_entry',
            'checkin_result', 'checkin_reason',
            'override_used', 'override_reason'
        ]
        
    def validate(self, data):
        """
        Validate attendance logic.
        Note: Most validation moved to CheckInDecisionEngine.
        """
        check_in = data.get('check_in_time')
        check_out = data.get('check_out_time')
        
        # Time validation
        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError("Check-out time must be after check-in time.")
                
        return data

