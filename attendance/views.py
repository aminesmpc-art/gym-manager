from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Attendance
from .serializers import AttendanceSerializer
from subscriptions.views import IsAdminOrStaff # Reuse helper permission

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
    filterset_fields = ['member', 'date', 'member__activity_type']
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
            return Attendance.objects.select_related('member', 'recorded_by').all()
            
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
