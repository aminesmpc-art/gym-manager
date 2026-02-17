"""
School-specific views.
Separate API endpoints for the school Flutter app.
Gym endpoints remain untouched at /api/users/ and /api/members/.
School endpoints live at /api/school/staff/ and /api/school/students/.
"""
from rest_framework import viewsets, filters, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from users.models import User, StaffPayment
from users.views import IsAdminUser
from users.serializers import (
    StaffPaymentSerializer, StaffPaymentCreateSerializer,
    ChangePasswordSerializer,
)
from members.models import Member
from gym_management.permissions import MemberAccessPolicy, IsAdminOrStaff
from .models import Grade
from .serializers import (
    SchoolStaffSerializer,
    SchoolStaffCreateSerializer,
    SchoolStaffUpdateSerializer,
    SchoolStudentSerializer,
    GradeSerializer,
)


# ─── Grades / Classes ViewSet ─────────────────────────────────────────────

class GradeViewSet(viewsets.ModelViewSet):
    """
    CRUD for predefined grade/class levels.
    GET    /api/school/grades/          → list all grades
    POST   /api/school/grades/          → create { "name": "...", "order": 0 }
    PATCH  /api/school/grades/{id}/     → rename (also updates member.grade_level)
    DELETE /api/school/grades/{id}/     → delete (clears member.grade_level)
    """
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def perform_update(self, serializer):
        """When a grade is renamed, update all members that reference the old name."""
        old_name = serializer.instance.name
        grade = serializer.save()
        new_name = grade.name
        if old_name != new_name:
            updated = Member.objects.filter(grade_level=old_name).update(grade_level=new_name)
            # Attach count to response for info
            grade._members_updated = updated

    def perform_destroy(self, instance):
        """Clear grade_level for all members in this grade before deleting."""
        Member.objects.filter(grade_level=instance.name).update(grade_level='')
        instance.delete()


# ─── School Staff (Teachers) ViewSet ───────────────────────────────────────

class SchoolStaffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing school staff (teachers).
    Same logic as UserViewSet but with teacher-specific serializers
    that include subject, classes_taught, qualification.
    Only admins can access.
    """
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return SchoolStaffCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SchoolStaffUpdateSerializer
        return SchoolStaffSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role.upper())

        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        if show_archived:
            queryset = queryset.filter(is_archived=True)
        else:
            queryset = queryset.filter(is_archived=False)

        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            return Response(
                {'error': 'Cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get all payments for a specific staff member."""
        user = self.get_object()
        payments = StaffPayment.objects.filter(staff=user)
        serializer = StaffPaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a user (soft delete)."""
        user = self.get_object()
        if user.id == request.user.id:
            return Response(
                {'status': 'error', 'message': 'Cannot archive your own account'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_archived:
            return Response(
                {'status': 'error', 'message': 'User is already archived'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_archived = True
        user.archived_at = timezone.now()
        user.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
        return Response({
            'status': 'success',
            'message': 'User archived successfully',
            'is_archived': True,
            'archived_at': user.archived_at,
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived user."""
        user = self.get_object()
        if not user.is_archived:
            return Response(
                {'status': 'error', 'message': 'User is not archived'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_archived = False
        user.archived_at = None
        user.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
        return Response({
            'status': 'success',
            'message': 'User restored successfully',
            'is_archived': False,
        })

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current authenticated user's profile."""
        serializer = SchoolStaffSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change the current user's password."""
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save(update_fields=['password', 'updated_at'])
            return Response({
                'status': 'success',
                'message': 'Password changed successfully',
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── School Students ViewSet ──────────────────────────────────────────────

class SchoolStudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing school students.
    Same logic as MemberViewSet but with school-specific serializer
    that includes grade_level, parent_name, parent_phone, parent_email.
    """
    queryset = Member.objects.all()
    serializer_class = SchoolStudentSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAuthenticated, MemberAccessPolicy]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['activity_type', 'membership_plan', 'is_active', 'is_archived', 'gender']
    search_fields = ['first_name', 'last_name', 'phone', 'email', 'user__username']
    ordering_fields = ['created_at', 'last_name', 'subscription_end', 'archived_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on user role and apply advanced filters."""
        user = self.request.user
        base_queryset = Member.objects.select_related('user', 'activity_type', 'membership_plan')

        # Access control
        if user.is_staff_member and user.allowed_gender:
            genders = [g.strip() for g in user.allowed_gender.split(',')]
            from django.db.models import Q
            q = Q()
            if 'CHILD' in genders:
                q |= Q(age_category='CHILD')
            adult_genders = [g for g in genders if g != 'CHILD']
            if adult_genders:
                q |= Q(gender__in=adult_genders, age_category__in=['ADULT', ''])
            base_queryset = base_queryset.filter(q) if q else base_queryset.none()
        elif user.is_gym_member:
            return base_queryset.filter(user=user)

        # Annotations
        from django.db.models import F, ExpressionWrapper, DecimalField
        base_queryset = base_queryset.annotate(
            plan_price=F('membership_plan__price'),
            paid_amount=F('amount_paid'),
            debt_amount=ExpressionWrapper(
                F('membership_plan__price') - F('amount_paid'),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
            end_date_annotated=F('subscription_end'),
        )

        today = timezone.now().date()

        # Filters (identical logic to MemberViewSet)
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        base_queryset = base_queryset.filter(is_archived=show_archived)

        activity_id = self.request.query_params.get('activity')
        if activity_id and activity_id != 'null':
            base_queryset = base_queryset.filter(activity_type_id=activity_id)

        category = self.request.query_params.get('category')
        if category:
            if category.lower() == 'adult':
                base_queryset = base_queryset.filter(age_category='ADULT')
            elif category.lower() in ('kids', 'child'):
                base_queryset = base_queryset.filter(age_category='CHILD')

        payment_filter = self.request.query_params.get('payment')
        if payment_filter:
            if payment_filter.lower() == 'dabt':
                base_queryset = base_queryset.filter(debt_amount__gt=0)
            elif payment_filter.lower() == 'paid':
                base_queryset = base_queryset.filter(debt_amount__lte=0)

        insurance_filter = self.request.query_params.get('insurance')
        if insurance_filter:
            if insurance_filter.lower() == 'paid':
                base_queryset = base_queryset.filter(insurance_paid=True)
            elif insurance_filter.lower() == 'unpaid':
                base_queryset = base_queryset.filter(insurance_paid=False)

        plan_id = self.request.query_params.get('plan_id')
        if plan_id:
            try:
                base_queryset = base_queryset.filter(membership_plan_id=int(plan_id))
            except ValueError:
                pass

        has_debt = self.request.query_params.get('has_debt')
        if has_debt is not None:
            if has_debt.lower() == 'true':
                base_queryset = base_queryset.filter(debt_amount__gt=0)
            elif has_debt.lower() == 'false':
                base_queryset = base_queryset.filter(debt_amount__lte=0)

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
                        subscription_end__lte=expiry_limit,
                    )
                except ValueError:
                    pass

        status_filter = self.request.query_params.get('status')
        if status_filter:
            st = status_filter.lower()
            from datetime import timedelta
            if st == 'pending':
                base_queryset = base_queryset.filter(debt_amount__gt=0)
            elif st == 'expired':
                base_queryset = base_queryset.filter(subscription_end__lt=today)
            elif st == 'active':
                base_queryset = base_queryset.filter(subscription_end__gte=today)
            elif st == 'expiring':
                next_week = today + timedelta(days=7)
                base_queryset = base_queryset.filter(
                    subscription_end__gte=today,
                    subscription_end__lte=next_week,
                )
            elif st == 'suspended':
                base_queryset = base_queryset.filter(is_active=False, is_archived=False)

        return base_queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Auto-create User account for new student."""
        from django.contrib.auth import get_user_model
        from django.utils.text import slugify
        from datetime import timedelta
        import random

        UserModel = get_user_model()

        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')
        base_username = slugify(f"{first_name}.{last_name}")
        username = base_username

        while UserModel.objects.filter(username=username).exists():
            username = f"{base_username}{random.randint(100, 999)}"

        user = UserModel.objects.create_user(
            username=username,
            password='member123',
            role='MEMBER',
            first_name=first_name,
            last_name=last_name,
        )

        subscription_start = serializer.validated_data.get('subscription_start')
        if not subscription_start:
            subscription_start = timezone.now().date()

        membership_plan = serializer.validated_data.get('membership_plan')
        subscription_end = subscription_start + timedelta(days=membership_plan.duration_days)

        member = serializer.save(
            user=user,
            subscription_start=subscription_start,
            subscription_end=subscription_end,
            is_active=True,
        )

        # Create initial payment
        if membership_plan.price > 0:
            from subscriptions.models import Payment
            from decimal import Decimal

            user_amount_paid = serializer.validated_data.get('amount_paid')
            if user_amount_paid is None or user_amount_paid == '':
                payment_amount = membership_plan.price
            else:
                try:
                    payment_amount = Decimal(str(user_amount_paid))
                except Exception:
                    payment_amount = membership_plan.price

            member.amount_paid = 0
            member.save(update_fields=['amount_paid'])

            Payment.objects.create(
                member=member,
                membership_plan=membership_plan,
                amount=payment_amount,
                payment_date=timezone.now().date(),
                payment_method='CASH',
                period_start=subscription_start,
                period_end=subscription_end,
                notes=f"Initial enrollment: {membership_plan.name}",
                created_by=self.request.user,
            )

    def perform_destroy(self, instance):
        """Delete related records before deleting student."""
        instance.payments.all().delete()
        instance.attendances.all().delete()
        if instance.user:
            instance.user.delete()
        instance.delete()

    @action(detail=True, methods=['post'])
    def renew_subscription(self, request, pk=None):
        """Renew a student's enrollment."""
        member = self.get_object()
        from datetime import timedelta
        from subscriptions.models import Payment

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
                return Response({'error': 'Invalid plan'}, status=400)
        else:
            plan = member.membership_plan

        if not plan:
            return Response({'error': 'Student has no plan assigned'}, status=400)

        today = timezone.now().date()
        if member.subscription_end and member.subscription_end >= today:
            start_date = member.subscription_end + timedelta(days=1)
        else:
            start_date = today

        end_date = start_date + timedelta(days=plan.duration_days)

        if plan.price > 0:
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
                created_by=request.user,
            )

        member.subscription_start = start_date
        member.subscription_end = end_date
        member.amount_paid = 0
        member.save(update_fields=[
            'activity_type', 'membership_plan',
            'subscription_start', 'subscription_end',
            'amount_paid', 'updated_at',
        ])

        serializer = self.get_serializer(member)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle student active/suspended status."""
        member = self.get_object()
        member.is_active = not member.is_active
        member.save(update_fields=['is_active', 'updated_at'])
        serializer = self.get_serializer(member)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a student."""
        member = self.get_object()
        if member.is_archived:
            return Response(
                {'status': 'error', 'message': 'Student is already archived'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member.is_archived = True
        member.archived_at = timezone.now()
        member.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
        return Response({
            'status': 'success',
            'message': 'Student archived successfully',
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived student."""
        member = self.get_object()
        if not member.is_archived:
            return Response(
                {'status': 'error', 'message': 'Student is not archived'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member.is_archived = False
        member.archived_at = None
        member.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
        return Response({
            'status': 'success',
            'message': 'Student restored successfully',
        })
