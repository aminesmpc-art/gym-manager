from rest_framework import viewsets, filters, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Attendance
from .serializers import AttendanceSerializer
from .services import CheckInDecisionEngine, perform_checkin
from members.models import Member
from subscriptions.views import IsAdminOrStaff  # Reuse helper permission


class SmartCheckInView(APIView):
    """
    Smart Check-In API - Staff-controlled entrance control.
    
    POST /api/attendance/checkin/
    
    Request:
    {
        "member_id": <int>,
        "override": <bool>,  # Optional, admin only
        "override_reason": <str>  # Required if override=true
    }
    
    Response:
    {
        "result": "allowed | warning | blocked",
        "reason": "ok | expired | debt | insurance | already_checked_in | inactive",
        "message": "Human readable message",
        "member_snapshot": { ... },
        "attendance_id": <int> | null
    }
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]
    
    def post(self, request):
        member_id = request.data.get('member_id')
        override = request.data.get('override', False)
        override_reason = request.data.get('override_reason', '')
        
        # Validate member_id
        if not member_id:
            return Response(
                {'error': 'member_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get member
        member = get_object_or_404(Member, id=member_id)
        
        # Run decision engine
        engine = CheckInDecisionEngine(member, request.user)
        decision = engine.evaluate()
        
        # Prepare response
        response_data = {
            'result': decision.result,
            'reason': decision.reason,
            'message': decision.message,
            'member_snapshot': decision.member_snapshot,
            'can_override': decision.can_override,
            'attendance_id': None
        }
        
        # If blocked, return decision without creating record
        if decision.result == 'blocked' and not override:
            return Response(response_data, status=status.HTTP_200_OK)
        
        # Create check-in record (for allowed, warning, or override)
        try:
            attendance, final_decision = perform_checkin(
                member=member,
                staff_user=request.user,
                override=override,
                override_reason=override_reason
            )
            
            if attendance:
                response_data['attendance_id'] = attendance.id
                response_data['result'] = final_decision.result
                response_data['message'] = final_decision.message
            else:
                response_data['message'] = final_decision.message
                
        except Exception as e:
            # Handle unique constraint violation (already checked in)
            if 'unique' in str(e).lower():
                response_data['result'] = 'blocked'
                response_data['reason'] = 'already_checked_in'
                response_data['message'] = f'{member.full_name} has already checked in today.'
            else:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(response_data, status=status.HTTP_200_OK)


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    API for managing daily attendance.
    
    Permissions:
    - ADMIN/STAFF: Full CRUD (Check-in members).
    - MEMBER: Read-only access to OWN attendance history.
    """
    
    serializer_class = AttendanceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtering
    filterset_fields = ['member', 'date', 'member__activity_type', 'checkin_result']
    search_fields = ['member__first_name', 'member__last_name', 'member__phone']
    ordering_fields = ['date', 'check_in_time']
    ordering = ['-date', '-check_in_time']
    
    def get_permissions(self):
        """
        Restrict creation/modification to Admin/Staff.
        Members can only List/Retrieve.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Filter attendance based on role.
        """
        user = self.request.user
        
        if user.is_admin or user.is_staff_member:
            return Attendance.objects.select_related(
                'member', 'recorded_by', 'activity_at_entry'
            ).all()
            
        if user.is_gym_member:
            # Member sees only their own attendance
            return Attendance.objects.select_related('member').filter(member__user=user)
            
        return Attendance.objects.none()

    def perform_create(self, serializer):
        """
        Auto-assign recorded_by to current staff member.
        """
        from django.utils import timezone
        serializer.save(
            recorded_by=self.request.user,
            check_in_time=timezone.now().time()
        )

