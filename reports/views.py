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
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # 1. Member Counts
        active_members = Member.objects.filter(
            subscription_end__gte=today
        ).count()
        
        expired_members = Member.objects.filter(
            subscription_end__lt=today
        ).count()
        
        # Members expiring in next 7 days (including today)
        expiring_soon = Member.objects.filter(
            subscription_end__range=[today, today + timedelta(days=7)]
        ).count()
        
        # 2. Financials (Cash Only)
        income_today = Payment.objects.filter(
            payment_date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        income_month = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
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
        
        data = {
            'overview': {
                'active_members': active_members,
                'expired_members': expired_members,
                'expiring_soon_7_days': expiring_soon,
                'attendance_today': attendance_today,
            },
            'financials': {
                'income_today': income_today,
                'income_this_month': income_month,
                'currency': 'DA'
            },
            'activity_breakdown': activity_breakdown
        }
        
        return Response(data)
