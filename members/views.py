from rest_framework import viewsets, filters 
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Member
from .serializers import MemberSerializer
from gym_management.permissions import MemberAccessPolicy, IsAdminOrStaff

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
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAuthenticated, MemberAccessPolicy]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields
    filterset_fields = ['activity_type', 'membership_plan', 'is_active', 'is_archived', 'gender']
    search_fields = ['first_name', 'last_name', 'phone', 'email', 'user__username']
    ordering_fields = ['created_at', 'last_name', 'subscription_end', 'archived_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter queryset based on user role and apply advanced filters.
        """
        user = self.request.user
        base_queryset = Member.objects.select_related('user', 'activity_type', 'membership_plan')
        
        # 1. Access Control
        if user.is_staff_member and user.allowed_gender:
            if user.allowed_gender == 'CHILD':
                base_queryset = base_queryset.filter(age_category='CHILD')
            else:
                base_queryset = base_queryset.filter(gender=user.allowed_gender).exclude(age_category='CHILD')
        elif user.is_gym_member:
             return base_queryset.filter(user=user)
        # Admin sees all (no extra filter)

        # 2. Annotation for calculations (Debt, Days Left, Status Helpers)
        from django.db.models import F, Q, ExpressionWrapper, DateField, DecimalField, Case, When, Value, CharField, IntegerField
        from django.db.models.functions import Now, Coalesce
        from django.utils import timezone
        
        today = timezone.now().date()
        
        # Annotate DB-side calculations for filtering
        base_queryset = base_queryset.annotate(
            plan_price=F('membership_plan__price'),
            paid_amount=F('amount_paid'),
            debt_amount=ExpressionWrapper(
                F('membership_plan__price') - F('amount_paid'), 
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            end_date_annotated=F('subscription_end')
        )

        # 3. Filters
        
        # Archived
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        base_queryset = base_queryset.filter(is_archived=show_archived)

        # Activity
        activity_id = self.request.query_params.get('activity')
        if activity_id and activity_id != 'null': # Handle 'null' string just in case
            base_queryset = base_queryset.filter(activity_type_id=activity_id)

        # Category
        category = self.request.query_params.get('category')
        if category:
            if category.lower() == 'adult':
                 base_queryset = base_queryset.filter(age_category='ADULT')
            elif category.lower() == 'kids' or category.lower() == 'child':
                 base_queryset = base_queryset.filter(age_category='CHILD')

        # Payment (paid | dabt)
        payment_filter = self.request.query_params.get('payment')
        if payment_filter:
            if payment_filter.lower() == 'dabt':
                base_queryset = base_queryset.filter(debt_amount__gt=0)
            elif payment_filter.lower() == 'paid':
                base_queryset = base_queryset.filter(debt_amount__lte=0)

        # Insurance
        insurance_filter = self.request.query_params.get('insurance')
        if insurance_filter:
            if insurance_filter.lower() == 'paid':
                base_queryset = base_queryset.filter(insurance_paid=True)
            elif insurance_filter.lower() == 'unpaid':
                base_queryset = base_queryset.filter(insurance_paid=False)

        # Plan ID filter
        plan_id = self.request.query_params.get('plan_id')
        if plan_id:
            try:
                base_queryset = base_queryset.filter(membership_plan_id=int(plan_id))
            except ValueError:
                pass

        # Has Debt filter (true | false)
        has_debt = self.request.query_params.get('has_debt')
        if has_debt is not None:
            if has_debt.lower() == 'true':
                base_queryset = base_queryset.filter(debt_amount__gt=0)
            elif has_debt.lower() == 'false':
                base_queryset = base_queryset.filter(debt_amount__lte=0)

        # Expires In filter (7 | 3 | expired)
        expires_in = self.request.query_params.get('expires_in')
        if expires_in:
            from datetime import timedelta
            if expires_in.lower() == 'expired':
                base_queryset = base_queryset.filter(subscription_end__lt=today)
            else:
                try:
                    days = int(expires_in)
                    expiry_limit = today + timedelta(days=days)
                    base_queryset = base_queryset.filter(
                        subscription_end__gte=today,
                        subscription_end__lte=expiry_limit
                    )
                except ValueError:
                    pass
        
        # Legacy expiring_in filter (for backward compatibility)
        expiring_in = self.request.query_params.get('expiring_in')
        if expiring_in and not expires_in:  # Only if expires_in not used
            try:
                days = int(expiring_in)
                from datetime import timedelta
                expiry_limit = today + timedelta(days=days)
                base_queryset = base_queryset.filter(
                    subscription_end__gte=today,
                    subscription_end__lte=expiry_limit
                )
            except ValueError:
                pass
        
        # Status Filter (active | expired | pending | expiring | suspended)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            status = status_filter.lower()
            from datetime import timedelta
            if status == 'pending':
                base_queryset = base_queryset.filter(debt_amount__gt=0)
            elif status == 'expired':
                base_queryset = base_queryset.filter(subscription_end__lt=today)
            elif status == 'active':
                base_queryset = base_queryset.filter(
                    subscription_end__gte=today
                )
            elif status == 'expiring':
                next_week = today + timedelta(days=7)
                base_queryset = base_queryset.filter(
                    subscription_end__gte=today,
                    subscription_end__lte=next_week
                )
            elif status == 'suspended':
                base_queryset = base_queryset.filter(is_active=False, is_archived=False)

        return base_queryset.order_by('-created_at')

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
        # Ensure new members are always active (not suspended)
        member = serializer.save(
            user=user,
            subscription_start=subscription_start,
            subscription_end=subscription_end,
            is_active=True
        )
        
        # Create Payment Record
        if membership_plan.price > 0:
            from subscriptions.models import Payment
            from django.utils import timezone
            
            # IMPORTANT: Reset amount_paid BEFORE creating Payment
            # Payment.save() will set it to the correct value
            # This prevents doubling when frontend sends amount_paid
            member.amount_paid = 0
            member.save(update_fields=['amount_paid'])
            
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
        
        # Optional: Update activity type and plan if provided
        new_activity_id = request.data.get('activity_type_id')
        new_plan_id = request.data.get('plan_id')
        
        if new_activity_id:
            from gym.models import ActivityType
            try:
                new_activity = ActivityType.objects.get(id=new_activity_id)
                member.activity_type = new_activity
            except ActivityType.DoesNotExist:
                return Response({'error': 'Invalid activity type'}, status=400)
        
        if new_plan_id:
            from gym.models import MembershipPlan
            try:
                new_plan = MembershipPlan.objects.get(id=new_plan_id)
                member.membership_plan = new_plan
                plan = new_plan
            except MembershipPlan.DoesNotExist:
                return Response({'error': 'Invalid membership plan'}, status=400)
        else:
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
        
        # Use plan duration
        duration_days = plan.duration_days
        end_date = start_date + timedelta(days=duration_days)
        
        # Create Payment
        if plan.price > 0:
            # Use custom amount if provided, otherwise use plan price
            custom_amount = request.data.get('amount')
            if custom_amount:
                try:
                    amount = float(custom_amount)
                except (ValueError, TypeError):
                    amount = plan.price
            else:
                amount = plan.price
                
            Payment.objects.create(
                member=member,
                membership_plan=plan,
                amount=amount,
                payment_date=today,
                payment_method='CASH',
                period_start=start_date,
                period_end=end_date,
                notes=f"Renewal: {plan.name}",
                created_by=request.user
            )
        
        # Update Member subscription dates and save activity/plan changes
        # Reset payment tracking for new renewal period
        member.subscription_start = start_date
        member.subscription_end = end_date
        member.total_price = plan.price
        member.amount_paid = amount if plan.price > 0 else 0
        member.remaining_debt = max(0, plan.price - amount) if plan.price > 0 else 0
        member.save()
        
        return Response({
            'status': 'success',
            'message': f'Renewed until {end_date}',
            'subscription_end': end_date,
            'activity_type': member.activity_type.name if member.activity_type else None,
            'membership_plan': plan.name
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

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a member (soft delete)."""
        from django.utils import timezone
        member = self.get_object()
        
        if member.is_archived:
            return Response({
                'status': 'error',
                'message': 'Member is already archived'
            }, status=400)
        
        member.is_archived = True
        member.archived_at = timezone.now()
        member.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
        
        return Response({
            'status': 'success',
            'message': 'Member archived successfully',
            'is_archived': True,
            'archived_at': member.archived_at
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived member."""
        member = self.get_object()
        
        if not member.is_archived:
            return Response({
                'status': 'error',
                'message': 'Member is not archived'
            }, status=400)
        
        member.is_archived = False
        member.archived_at = None
        member.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
        
        return Response({
            'status': 'success',
            'message': 'Member restored successfully',
            'is_archived': False
        })


class NotificationBotView(viewsets.ViewSet):
    """
    API Control Panel for WhatsApp Notification Bot.
    """
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get today's notification statistics."""
        from .models import NotificationLog
        from django.utils import timezone
        
        today = timezone.now().date()
        logs = NotificationLog.objects.filter(sent_at__date=today)
        
        stats = {
            'total_today': logs.count(),
            'reminders': logs.filter(notification_type='REMINDER_3_DAYS').count(),
            'expired_alerts': logs.filter(notification_type='EXPIRED_UNPAID').count(),
            'last_run': logs.first().sent_at if logs.exists() else None
        }
        return Response(stats)

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Manually trigger the bot."""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        try:
            # Run the management command and capture output
            call_command('run_whatsapp_bot', stdout=out)
            output = out.getvalue()
            
            return Response({
                'status': 'success',
                'message': 'Bot executed successfully',
                'log': output
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=500)
