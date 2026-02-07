from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from decimal import Decimal
from .models import Payment
from .serializers import PaymentSerializer
from members.models import Member

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
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'add_payment']:
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

    @action(detail=False, methods=['post'], url_path='add-payment')
    def add_payment(self, request):
        """
        Manual cash payment endpoint.
        Creates payment record and updates member debt.
        
        POST /api/subscriptions/payments/add-payment/
        {
            "member_id": 123,
            "amount": 100.00,
            "note": "Cash payment"
        }
        """
        member_id = request.data.get('member_id')
        amount = request.data.get('amount')
        note = request.data.get('note', '')
        
        # Validation
        if not member_id:
            return Response(
                {'error': 'member_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not amount:
            return Response(
                {'error': 'amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response(
                    {'error': 'amount must be positive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            member = Member.objects.select_related('membership_plan').get(pk=member_id)
        except Member.DoesNotExist:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not member.membership_plan:
            return Response(
                {'error': 'Member has no active plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        today = timezone.now().date()
        
        # Create payment record
        payment = Payment.objects.create(
            member=member,
            membership_plan=member.membership_plan,
            amount=amount,
            payment_method=Payment.PaymentMethod.CASH,
            payment_date=today,
            period_start=member.subscription_start or today,
            period_end=member.subscription_end or today,
            notes=note,
            created_by=request.user
        )
        
        # Refresh member to get updated debt
        member.refresh_from_db()
        
        return Response({
            'success': True,
            'payment_id': payment.id,
            'member': {
                'id': member.id,
                'name': member.full_name,
                'total_price': float(member.membership_plan.price),
                'amount_paid': float(member.amount_paid),
                'remaining_debt': float(member.remaining_debt),
                'payment_status': member.payment_status,
            }
        }, status=status.HTTP_201_CREATED)


class IsAdminOrStaff(permissions.BasePermission):
    """
    Helper permission: Only Admin or Staff can write.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_admin or request.user.is_staff_member)
