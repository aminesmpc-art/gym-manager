from rest_framework import viewsets, permissions, filters
from .models import Gym, ActivityType, MembershipPlan
from .serializers import GymSerializer, ActivityTypeSerializer, MembershipPlanSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read access to authenticated users.
    Write access only to Admin.
    """
    def has_permission(self, request, view):
        if request.user.is_superuser or request.user.role == 'ADMIN':
            return True
        return request.method in permissions.SAFE_METHODS

class ActivityTypeViewSet(viewsets.ModelViewSet):
    """
    API for listing available activities (e.g., Bodybuilding, Cardio).
    """
    queryset = ActivityType.objects.filter(is_active=True)
    serializer_class = ActivityTypeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

class MembershipPlanViewSet(viewsets.ModelViewSet):
    """
    API for listing available membership plans.
    """
    queryset = MembershipPlan.objects.filter(is_active=True)
    serializer_class = MembershipPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'activity_type__name']

class GymViewSet(viewsets.ModelViewSet):
    """
    API to retrieve Gym details.
    """
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
