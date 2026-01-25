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
    Read-only.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]
    
    def get(self, request):
        date_param = request.query_params.get('date')
        if date_param:
            from django.utils.dateparse import parse_date
            today = parse_date(date_param) or timezone.now().date()
        else:
            today = timezone.now().date()
            
        month_start = today.replace(day=1)
        
        # 1. Member Counts
        total_members = Member.objects.count()
        
        active_members = Member.objects.filter(
            subscription_end__gte=today
        ).count()
        
        expired_members = Member.objects.filter(
            subscription_end__lt=today
        ).count()
        
        pending_members = Member.objects.filter(
            subscription_end__isnull=True
        ).count()
        
        # Members expiring in next 7 days (including today)
        expiring_soon = Member.objects.filter(
            subscription_end__range=[today, today + timedelta(days=7)]
        ).count()
        
        # Suspended Members
        suspended_members = Member.objects.filter(is_active=False).count()
        
        # 2. Financials (Cash Only)
        income_today = Payment.objects.filter(
            payment_date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        income_month = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Total Revenue (All Time)
        total_income = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # 3. Attendance
        attendance_today = Attendance.objects.filter(
            date=today
        ).count()
        
        # 4. Activity Breakdown
        activity_breakdown = Member.objects.values(
            'activity_type__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 5. Demographic Counts
        try:
            men_count = Member.objects.filter(gender='M', age_category='ADULT').count()
            women_count = Member.objects.filter(gender='F', age_category='ADULT').count()
            kids_count = Member.objects.filter(age_category='CHILD').count()
        except Exception:
            # Fallback if migration hasn't run yet
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
