from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from members.models import Member
from subscriptions.models import Payment
from attendance.models import Attendance
from subscriptions.views import IsAdminOrStaff

class DashboardView(views.APIView):
    """
    Dashboard API for Gym Management System.
    Provides aggregated business metrics for Admin and Staff.
    Read-only. Staff users see filtered data based on their allowed_gender.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]
    
    def get_member_queryset(self, user):
        """Get member queryset filtered by user's permissions."""
        if user.is_admin:
            return Member.objects.all()
        
        if user.is_staff_member and user.allowed_gender:
            if user.allowed_gender == 'CHILD':
                return Member.objects.filter(age_category='CHILD')
            else:
                return Member.objects.filter(gender=user.allowed_gender).exclude(age_category='CHILD')
        
        return Member.objects.all()
    
    def get(self, request):
        user = request.user
        date_param = request.query_params.get('date')
        if date_param:
            from django.utils.dateparse import parse_date
            today = parse_date(date_param) or timezone.now().date()
        else:
            today = timezone.now().date()
            
        month_start = today.replace(day=1)
        
        # Get filtered member queryset
        members = self.get_member_queryset(user)
        
        # 1. Member Counts (filtered for staff)
        total_members = members.count()
        
        active_members = members.filter(
            subscription_end__gte=today
        ).count()
        
        expired_members = members.filter(
            subscription_end__lt=today
        ).count()
        
        pending_members = members.filter(
            subscription_end__isnull=True
        ).count()
        
        # Members expiring in next 7 days (including today)
        expiring_soon = members.filter(
            subscription_end__range=[today, today + timedelta(days=7)]
        ).count()
        
        # Suspended Members
        suspended_members = members.filter(is_active=False).count()
        
        # 2. Financials (Admin Only - hide for staff)
        if user.is_admin:
            income_today = Payment.objects.filter(
                payment_date=today
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            income_month = Payment.objects.filter(
                payment_date__gte=month_start,
                payment_date__lte=today
            ).aggregate(total=Sum('amount'))['total'] or 0

            total_income = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        else:
            # Staff cannot see financials
            income_today = 0
            income_month = 0
            total_income = 0
        
        # 3. Attendance (filtered for staff)
        if user.is_admin:
            attendance_today = Attendance.objects.filter(date=today).count()
        else:
            # Filter attendance by staff's allowed members
            member_ids = members.values_list('id', flat=True)
            attendance_today = Attendance.objects.filter(
                date=today,
                member_id__in=member_ids
            ).count()
        
        # 4. Activity Breakdown (filtered for staff)
        activity_breakdown = members.values(
            'activity_type__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 5. Demographic Counts (filtered for staff)
        try:
            men_count = members.filter(gender='M', age_category='ADULT').count()
            women_count = members.filter(gender='F', age_category='ADULT').count()
            kids_count = members.filter(age_category='CHILD').count()
        except Exception:
            men_count = 0
            women_count = 0
            kids_count = 0
        
        data = {
            'overview': {
                'total_members': total_members,
                'active_members': active_members,
                'suspended_members': suspended_members,
                'expired_members': expired_members,
                'pending_members': pending_members,
                'expiring_soon_7_days': expiring_soon,
                'attendance_today': attendance_today,
            },
            'demographics': {
                'men': men_count,
                'women': women_count,
                'kids': kids_count,
            },
            'financials': {
                'income_today': income_today,
                'income_this_month': income_month,
                'total_income': total_income,
                'currency': 'DH'
            },
            'activity_breakdown': activity_breakdown
        }
        
        return Response(data)
