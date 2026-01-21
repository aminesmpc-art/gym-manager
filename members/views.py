from rest_framework import viewsets, filters 
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Member
from .serializers import MemberSerializer
from gym_management.permissions import MemberAccessPolicy

class MemberViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing members.
    
    Permissions:
    - ADMIN: Full access (CRUD)
    - STAFF: List, Create, Retrieve, Update (No Delete)
    - MEMBER: Retrieve own profile only
    """
    
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, MemberAccessPolicy]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields
    filterset_fields = ['activity_type', 'membership_plan', 'is_active', 'gender']
    search_fields = ['first_name', 'last_name', 'phone', 'email', 'user__username']
    ordering_fields = ['created_at', 'last_name', 'subscription_end']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter queryset based on user role.
        - Admin/Staff: See all members
        - Member: See ONLY their own record
        """
        user = self.request.user
        
        if user.is_admin or user.is_staff_member:
            return Member.objects.select_related('user', 'activity_type', 'membership_plan').all()
            
        if user.is_gym_member:
            return Member.objects.select_related('user', 'activity_type', 'membership_plan').filter(user=user)
            
        return Member.objects.none()
