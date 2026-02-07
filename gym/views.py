from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
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
    API for managing activity types.
    Admins see all activities (including disabled).
    Staff see only active activities.
    """
    serializer_class = ActivityTypeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    def get_queryset(self):
        """Admin sees all activities, others see only active ones."""
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', None) == 'ADMIN':
            return ActivityType.objects.all().order_by('order', 'name')
        return ActivityType.objects.filter(is_active=True).order_by('order', 'name')
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Bulk update activity order.
        Expects: { "order": [id1, id2, id3, ...] }
        """
        from rest_framework.response import Response
        from django.db import transaction
        
        order_list = request.data.get('order', [])
        if not order_list:
            return Response({'error': 'Order list required'}, status=400)
        
        try:
            with transaction.atomic():
                for index, activity_id in enumerate(order_list):
                    ActivityType.objects.filter(id=activity_id).update(order=index)
            return Response({'success': True, 'message': 'Order updated'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

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
