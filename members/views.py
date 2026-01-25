from rest_framework import viewsets, filters 
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
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

    def perform_create(self, serializer):
        """
        Auto-create a User account for the new member.
        Username: first_name.last_name (lowercase) + random suffix if needed
        Default password: 'member123'
        Role: MEMBER
        """
        from django.contrib.auth import get_user_model
        from django.utils.text import slugify
        import random

        User = get_user_model()
        
        # Generate username
        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')
        base_username = slugify(f"{first_name}.{last_name}")
        username = base_username
        
        # Ensure unique username
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{random.randint(100, 999)}"
        
        # Create User
        user = User.objects.create_user(
            username=username,
            password='member123',  # Default password
            role='MEMBER',
            first_name=first_name,
            last_name=last_name
        )
        
        
        # Calculate subscription dates
        subscription_start = serializer.validated_data.get('subscription_start')
        if not subscription_start:
            # If not provided, default to today
            from django.utils import timezone
            subscription_start = timezone.now().date()
            
        membership_plan = serializer.validated_data.get('membership_plan')
        from datetime import timedelta
        subscription_end = subscription_start + timedelta(days=membership_plan.duration_days)
        
        # Save Member with the new User and subscription dates
        # Save Member with the new User and subscription dates
        member = serializer.save(
            user=user,
            subscription_start=subscription_start,
            subscription_end=subscription_end
        )
        
        # Create Payment Record
        if membership_plan.price > 0:
            from subscriptions.models import Payment
            from django.utils import timezone
            
            Payment.objects.create(
                member=member,
                membership_plan=membership_plan,
                amount=membership_plan.price,
                payment_date=timezone.now().date(),
                payment_method='CASH', # Default
                period_start=subscription_start,
                period_end=subscription_end,
                notes=f"Initial subscription: {membership_plan.name}",
                created_by=self.request.user
            )

    def perform_destroy(self, instance):
        """Delete related records before deleting member."""
        # Delete related payments
        instance.payments.all().delete()
        # Delete related attendances
        instance.attendances.all().delete()
        # Delete associated user account
        if instance.user:
            instance.user.delete()
        # Now delete the member
        instance.delete()

    @action(detail=True, methods=['post'])
    def renew_subscription(self, request, pk=None):
        member = self.get_object()
        plan = member.membership_plan
        
        if not plan:
             return Response({'error': 'Member has no plan assigned'}, status=400)
             
        # Determine start date
        from django.utils import timezone
        from datetime import timedelta
        from subscriptions.models import Payment

        today = timezone.now().date()
        
        # If active, extend. If expired, restart.
        if member.subscription_end and member.subscription_end >= today:
             start_date = member.subscription_end + timedelta(days=1)
        else:
             start_date = today
             
        end_date = start_date + timedelta(days=plan.duration_days)
        
        # Create Payment
        if plan.price > 0:
            Payment.objects.create(
                member=member,
                membership_plan=plan,
                amount=plan.price,
                payment_date=today,
                payment_method='CASH',
                period_start=start_date,
                period_end=end_date,
                notes=f"Renewal: {plan.name}",
                created_by=request.user
            )
        
        # Update Member
        member.subscription_start = start_date
        member.subscription_end = end_date
        member.save()
        
        return Response({
            'status': 'success',
            'message': f'Renewed until {end_date}',
            'subscription_end': end_date
        })

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Suspend or reactivate a member."""
        member = self.get_object()
        member.is_active = not member.is_active
        member.save(update_fields=['is_active', 'updated_at'])
        
        status_text = 'activated' if member.is_active else 'suspended'
        return Response({
            'status': 'success',
            'message': f'Member {status_text}',
            'is_active': member.is_active
        })
