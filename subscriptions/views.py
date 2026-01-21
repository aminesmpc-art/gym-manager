from rest_framework import viewsets, filters, permissions
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment
from .serializers import PaymentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    """
    API for managing payments (Internal Tracking Only).
    
    Permissions:
    - ADMIN/STAFF: Full CRUD.
    - MEMBER: Read-only access to OWN payments.
    """
    
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtering
    filterset_fields = ['member', 'membership_plan', 'payment_method', 'payment_date']
    search_fields = ['member__first_name', 'member__last_name', 'member__phone', 'notes']
    ordering_fields = ['payment_date', 'created_at', 'amount']
    ordering = ['-payment_date']
    
    def get_permissions(self):
        """
        Restrict creation/modification to Admin/Staff.
        Members can only List/Retrieve.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Must be Admin or Staff
            return [permissions.IsAuthenticated(), IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Filter payments based on role.
        """
        user = self.request.user
        
        if user.is_admin or user.is_staff_member:
            return Payment.objects.select_related('member', 'membership_plan', 'created_by').all()
            
        if user.is_gym_member:
            # Member sees only their own payments
            return Payment.objects.select_related('member', 'membership_plan').filter(member__user=user)
            
        return Payment.objects.none()

    def perform_create(self, serializer):
        """
        Auto-assign created_by to current user.
        """
        serializer.save(created_by=self.request.user)


class IsAdminOrStaff(permissions.BasePermission):
    """
    Helper permission: Only Admin or Staff can write.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_admin or request.user.is_staff_member)
