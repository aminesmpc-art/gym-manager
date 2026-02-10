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
        
        # Super Admin fallback - return tenants dashboard data
        if user.is_superuser:
            from django_tenants.utils import schema_context, get_public_schema_name
            from django.db import connection
            
            # Check if we're in public schema
            if connection.schema_name == get_public_schema_name():
                from tenants.models import Gym
                with schema_context('public'):
                    total_gyms = Gym.objects.count()
                    active_gyms = Gym.objects.filter(status='approved').count()
                    pending_gyms = Gym.objects.filter(status='pending').count()
                    
                return Response({
                    'overview': {
                        'total_members': total_gyms,  # Map to expected frontend field
                        'active_members': active_gyms,
                        'expired_members': 0,
                        'pending_members': pending_gyms,
                        'new_members_this_month': 0,
                        'monthly_revenue': 0,
                        'monthly_checkins': 0,
                        'average_daily_checkins': 0,
                    },
                    'demographics': {'genders': {}, 'ages': {}},
                    'recent_activity': [],
                    'is_super_admin': True,
                    'message': 'Super Admin Dashboard - Use /api/tenants/dashboard/ for detailed gym data'
                })
        
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

            # Calculate highest monthly income for progress bar
            from django.db.models.functions import TruncMonth
            highest_month = Payment.objects.annotate(
                month=TruncMonth('payment_date')
            ).values('month').annotate(
                total=Sum('amount')
            ).order_by('-total').first()
            
            highest_monthly_income = highest_month['total'] if highest_month else 0
            if highest_monthly_income < income_month:
                highest_monthly_income = income_month
            
            # Calculate highest daily income (best day ever) for revenue card progress bar
            from django.db.models.functions import TruncDate
            highest_day_income = Payment.objects.annotate(
                day=TruncDate('payment_date')
            ).values('day').annotate(
                total=Sum('amount')
            ).order_by('-total').first()
            
            highest_daily_income = float(highest_day_income['total']) if highest_day_income else 0
            if highest_daily_income < float(income_today):
                highest_daily_income = float(income_today)
        else:
            # Staff cannot see financials
            income_today = 0
            income_month = 0
            total_income = 0
            highest_monthly_income = 0
            highest_daily_income = 0
        
        # 2b. Debt & Payment Tracking
        active_member_list = members.filter(subscription_end__gte=today)
        active_member_ids = list(active_member_list.values_list('id', flat=True))
        
        # Revenue card shows THIS MONTH's collected revenue
        collected_revenue = float(income_month)
        
        # Total debt = sum of remaining_debt for all active members
        total_expected = sum(
            float(m.membership_plan.price) if m.membership_plan else 0
            for m in active_member_list.select_related('membership_plan')
        )
        total_paid_all = float(
            Payment.objects.filter(
                member_id__in=active_member_ids
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        total_debt = max(total_expected - total_paid_all, 0)
        
        # Count members with/without debt
        members_with_debt = 0
        paid_members_count = 0
        for m in active_member_list:
            plan_price = float(m.membership_plan.price) if m.membership_plan else 0
            member_payments = float(
                Payment.objects.filter(
                    member=m,
                    period_start=m.subscription_start,
                    period_end=m.subscription_end,
                ).aggregate(total=Sum('amount'))['total'] or 0
            )
            if member_payments >= plan_price:
                paid_members_count += 1
            else:
                members_with_debt += 1
        
        # 2c. Insurance Tracking
        insurance_paid_count = members.filter(insurance_paid=True).count()
        insurance_unpaid_count = members.filter(insurance_paid=False).count()
        
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
        
        # 5. Demographic Counts (filtered for staff, active members only)
        try:
            men_count = active_member_list.filter(gender='M').count()
            women_count = active_member_list.filter(gender='F').count()
            kids_count = active_member_list.filter(age_category='CHILD').count()
        except Exception:
            men_count = 0
            women_count = 0
            kids_count = 0
        
        # 6. Recent Activity (check-ins, signups, renewals)
        def time_ago(dt):
            """Convert datetime to human-readable 'time ago' string."""
            now = timezone.now()
            if hasattr(dt, 'date') and not hasattr(dt, 'hour'):
                # It's a date, convert to datetime
                dt = timezone.make_aware(timezone.datetime.combine(dt, timezone.datetime.min.time()))
            diff = now - dt
            seconds = diff.total_seconds()
            if seconds < 60:
                return "Just now"
            elif seconds < 3600:
                mins = int(seconds // 60)
                return f"{mins} min ago" if mins == 1 else f"{mins} mins ago"
            elif seconds < 86400:
                hours = int(seconds // 3600)
                return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
            elif seconds < 604800:
                days = int(seconds // 86400)
                return f"{days} day ago" if days == 1 else f"{days} days ago"
            else:
                return dt.strftime("%b %d")
        
        def get_member_status(member):
            """Determine member's subscription status."""
            if member.subscription_end is None:
                return "active"
            if member.subscription_end < today:
                return "expired"
            if member.subscription_end <= today + timedelta(days=7):
                return "expiring"
            return "active"
        
        recent_activity = []
        
        # Recent check-ins (last 10)
        if user.is_admin:
            recent_checkins = Attendance.objects.select_related('member').order_by('-check_in_time')[:10]
        else:
            member_ids = members.values_list('id', flat=True)
            recent_checkins = Attendance.objects.filter(
                member_id__in=member_ids
            ).select_related('member').order_by('-check_in_time')[:10]
        
        for checkin in recent_checkins:
            member = checkin.member
            # Combine attendance date and check_in_time
            if checkin.check_in_time:
                checkin_dt = timezone.make_aware(
                    timezone.datetime.combine(checkin.date, checkin.check_in_time)
                )
            else:
                # Fallback if no check_in_time
                checkin_dt = timezone.make_aware(
                    timezone.datetime.combine(checkin.date, timezone.datetime.min.time())
                )
                
            recent_activity.append({
                'name': member.full_name,
                'time': time_ago(checkin_dt),
                'type': 'Check-in',
                'status': get_member_status(member),
                'gender': member.gender or 'M',
                'photo_url': member.photo.url if member.photo else None,
                'member_id': member.id,
                'action_type': 'checkin',
            })
        
        # Recent signups (members created in last 7 days)
        recent_signups = members.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:5]
        
        for member in recent_signups:
            recent_activity.append({
                'name': member.full_name,
                'time': time_ago(member.created_at),
                'type': 'New Signup',
                'status': get_member_status(member),
                'gender': member.gender or 'M',
                'photo_url': member.photo.url if member.photo else None,
                'member_id': member.id,
                'action_type': 'signup',
            })
        
        # Sort by recency (approximation using time string - could be improved)
        # For now, keep check-ins first as they're usually more recent
        
        # 7. Trends Calculation (Merged from TrendsView)
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        def calc_trend(current, previous):
            if previous == 0:
                return {'value': '+0%', 'positive': True} if current == 0 else {'value': '+100%', 'positive': True}
            pct = ((current - previous) / previous) * 100
            sign = '+' if pct >= 0 else ''
            return {'value': f'{sign}{pct:.1f}%', 'positive': pct >= 0}
        
        # ACTIVE MEMBERS TREND (This month vs Last month)
        last_month_date = today - timedelta(days=30)
        active_last_month = Payment.objects.filter(
            period_start__lte=last_month_date, 
            period_end__gte=last_month_date
        ).values('member').distinct().count()
        
        members_trend = calc_trend(active_members, active_last_month)

        # REVENUE Trend (Admin only)
        if user.is_admin:
            current_revenue = Payment.objects.filter(
                payment_date__gte=current_month_start,
                payment_date__lte=today
            ).aggregate(total=Sum('amount'))['total'] or 0

            prev_revenue = Payment.objects.filter(
                payment_date__gte=prev_month_start,
                payment_date__lt=current_month_start
            ).aggregate(total=Sum('amount'))['total'] or 0
            revenue_trend = calc_trend(current_revenue, prev_revenue)
        else:
            revenue_trend = None

        # ATTENDANCE Trend (Today vs Yesterday)
        yesterday = today - timedelta(days=1)
        attendance_yesterday = Attendance.objects.filter(date=yesterday).count()
        attendance_trend = calc_trend(attendance_today, attendance_yesterday)

        # EXPIRING Trend (Risk Indicator: Expiring Next 7 Days / Total Active Members)
        # Display as negative (Red) to indicate risk
        if active_members > 0:
            expiring_risk_pct = (expiring_soon / active_members) * 100
            expiring_trend = {
                'value': f'{expiring_risk_pct:.1f}%',
                'positive': False # Always red/down as requested
            }
        else:
             expiring_trend = {
                'value': '0%',
                'positive': True # Neutral/Green if no risk
            }
        
        # Calculate Highest Daily Attendance (All-time peak)
        highest_day = Attendance.objects.values('date').annotate(
            count=Count('id')
        ).order_by('-count').first()
        highest_daily_attendance = highest_day['count'] if highest_day else 0
        
        # Ensure current today count is considered if it's the peak
        if attendance_today > highest_daily_attendance:
            highest_daily_attendance = attendance_today

        # Calculate Highest Active Member Count (Last 12 months peak)
        highest_active_member_count = 0
        
        # Helper to subtract months
        def subtract_months(dt, months):
            year = dt.year
            month = dt.month
            for _ in range(months):
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
            return dt.replace(year=year, month=month)
        
        check_date = current_month_start
        for _ in range(12):
            count = Payment.objects.filter(
                period_start__lte=check_date,
                period_end__gte=check_date
            ).values('member').distinct().count()
            if count > highest_active_member_count:
                highest_active_member_count = count
            check_date = subtract_months(check_date, 1)
        
        # Ensure current count is considered if it's the peak
        if active_members > highest_active_member_count:
            highest_active_member_count = active_members

        data = {
            'overview': {
                'total_members': total_members,
                'active_members': active_members,
                'suspended_members': suspended_members,
                'expired_members': expired_members,
                'pending_members': pending_members,
                'expiring_soon_7_days': expiring_soon,
                'attendance_today': attendance_today,
                'highest_active_member_count': highest_active_member_count,
                'highest_daily_attendance': highest_daily_attendance,
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
                'highest_monthly_income': highest_monthly_income,
                'highest_daily_income': highest_daily_income if user.is_admin else 0,
                'currency': 'DH'
            },
            'debt': {
                'collected_revenue': collected_revenue,
                'total_debt': total_debt,
                'members_with_debt': members_with_debt,
                'paid_members_count': paid_members_count,
            },
            'insurance': {
                'paid_count': insurance_paid_count,
                'unpaid_count': insurance_unpaid_count,
            },
            'trends': {
                'revenue': revenue_trend,
                'active_members': members_trend, # Note: this is actually new member growth
                'attendance': attendance_trend,
                'expiring': expiring_trend,
            },
            'activity_breakdown': {item['activity_type__name'] or 'Unknown': item['count'] for item in activity_breakdown},
            'recent_activity': recent_activity
        }
        
        return Response(data)


class RevenueChartView(views.APIView):
    """
    Revenue Chart API - returns aggregated data for charts.
    Query params:
      - period: 'week', 'month', 'year' (default: 'month')
      - type: 'income', 'attendance', 'members' (default: 'income')
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

    def get(self, request):
        period = request.query_params.get('period', 'month')
        chart_type = request.query_params.get('type', 'income')
        today = timezone.now().date()

        labels = []
        values = []
        paid_values = []
        unpaid_values = []

        # Get active member IDs for filtering (consistent with dashboard)
        active_member_ids = list(
            Member.objects.filter(subscription_end__gte=today).values_list('id', flat=True)
        )

        if period == 'week':
            # Last 7 days - show actual dates
            for i in range(6, -1, -1):
                day = today - timedelta(days=i)
                # Show day with date: "Mon 3" or "Feb 3"
                labels.append(day.strftime('%b %d'))  # e.g., "Feb 03"
                if chart_type == 'income':
                    # Get payments for active members only (consistent with dashboard)
                    payments = Payment.objects.filter(
                        payment_date=day,
                        member_id__in=active_member_ids
                    ).select_related('member')
                    # All received payments = Paid (green bar)
                    paid_val = sum(float(p.amount) for p in payments if p.amount)
                    # Pending = outstanding debts of members who paid this period
                    seen_members = {}
                    for p in payments:
                        if p.member and p.member_id not in seen_members:
                            seen_members[p.member_id] = float(p.member.remaining_debt)
                    unpaid_val = sum(seen_members.values())
                    total_val = paid_val + unpaid_val
                    values.append(total_val)
                    paid_values.append(paid_val)
                    unpaid_values.append(unpaid_val)
                elif chart_type == 'attendance':
                    val = Attendance.objects.filter(date=day).count()
                    values.append(float(val))
                    paid_values.append(float(val))
                    unpaid_values.append(0)
                else:  # members
                    val = Member.objects.filter(created_at__date=day).count()
                    values.append(float(val))
                    paid_values.append(float(val))
                    unpaid_values.append(0)

        elif period == 'year':
            # Last 12 months
            for i in range(11, -1, -1):
                month_date = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
                next_month = (month_date + timedelta(days=32)).replace(day=1)
                labels.append(month_date.strftime('%b'))
                if chart_type == 'income':
                    payments = Payment.objects.filter(
                        payment_date__gte=month_date,
                        payment_date__lt=next_month,
                        member_id__in=active_member_ids
                    ).select_related('member')
                    # All received payments = Paid (green bar)
                    paid_val = sum(float(p.amount) for p in payments if p.amount)
                    # Pending = outstanding debts of members who paid this period
                    seen_members = {}
                    for p in payments:
                        if p.member and p.member_id not in seen_members:
                            seen_members[p.member_id] = float(p.member.remaining_debt)
                    unpaid_val = sum(seen_members.values())
                    total_val = paid_val + unpaid_val
                    values.append(total_val)
                    paid_values.append(paid_val)
                    unpaid_values.append(unpaid_val)
                elif chart_type == 'attendance':
                    val = Attendance.objects.filter(
                        date__gte=month_date,
                        date__lt=next_month
                    ).count()
                    values.append(float(val))
                    paid_values.append(float(val))
                    unpaid_values.append(0)
                else:
                    val = Member.objects.filter(
                        created_at__date__gte=month_date,
                        created_at__date__lt=next_month
                    ).count()
                    values.append(float(val))
                    paid_values.append(float(val))
                    unpaid_values.append(0)

        else:  # month (default) - last 4 weeks including current week
            for i in range(3, -1, -1):
                week_end = today - timedelta(days=i * 7)
                week_start = week_end - timedelta(days=6)
                # Show actual date range, handling cross-month properly
                if week_start.month == week_end.month:
                    labels.append(f'{week_start.strftime("%b %d")}-{week_end.strftime("%d")}')
                else:
                    labels.append(f'{week_start.strftime("%b %d")} - {week_end.strftime("%b %d")}')
                if chart_type == 'income':
                    payments = Payment.objects.filter(
                        payment_date__gte=week_start,
                        payment_date__lte=week_end,
                        member_id__in=active_member_ids
                    ).select_related('member')
                    # All received payments = Paid (green bar)
                    paid_val = sum(float(p.amount) for p in payments if p.amount)
                    # Pending = outstanding debts of members who paid this period
                    seen_members = {}
                    for p in payments:
                        if p.member and p.member_id not in seen_members:
                            seen_members[p.member_id] = float(p.member.remaining_debt)
                    unpaid_val = sum(seen_members.values())
                    total_val = paid_val + unpaid_val
                    values.append(total_val)
                    paid_values.append(paid_val)
                    unpaid_values.append(unpaid_val)
                elif chart_type == 'attendance':
                    val = Attendance.objects.filter(
                        date__gte=week_start,
                        date__lte=week_end
                    ).count()
                    values.append(float(val))
                    paid_values.append(float(val))
                    unpaid_values.append(0)
                else:
                    val = Member.objects.filter(
                        created_at__date__gte=week_start,
                        created_at__date__lte=week_end
                    ).count()
                    values.append(float(val))
                    paid_values.append(float(val))
                    unpaid_values.append(0)

        total = sum(values)
        total_paid = sum(paid_values)
        total_unpaid = sum(unpaid_values)
        
        # Calculate trend (compare current period to previous)
        trend_percent = 0.0
        if len(values) >= 2 and values[-2] > 0:
            trend_percent = ((values[-1] - values[-2]) / values[-2]) * 100

        return Response({
            'period': period,
            'type': chart_type,
            'labels': labels,
            'values': values,
            'paid_values': paid_values,
            'unpaid_values': unpaid_values,
            'total': total,
            'total_paid': total_paid,
            'total_unpaid': total_unpaid,
            'trend_percent': round(trend_percent, 1),
            'trend_positive': trend_percent >= 0
        })


class TrendsView(views.APIView):
    """
    Trends API - returns percentage changes for dashboard KPIs.
    Compares current month to previous month.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

    def get(self, request):
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        def calc_trend(current, previous):
            if previous == 0:
                return {'value': '+0%', 'positive': True} if current == 0 else {'value': '+100%', 'positive': True}
            pct = ((current - previous) / previous) * 100
            sign = '+' if pct >= 0 else ''
            return {'value': f'{sign}{pct:.1f}%', 'positive': pct >= 0}

        # Revenue trend
        current_revenue = Payment.objects.filter(
            payment_date__gte=current_month_start,
            payment_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        prev_revenue = Payment.objects.filter(
            payment_date__gte=prev_month_start,
            payment_date__lt=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Members trend (new members)
        current_members = Member.objects.filter(
            created_at__date__gte=current_month_start
        ).count()
        prev_members = Member.objects.filter(
            created_at__date__gte=prev_month_start,
            created_at__date__lt=current_month_start
        ).count()

        # Attendance trend
        current_attendance = Attendance.objects.filter(
            date__gte=current_month_start
        ).count()
        prev_attendance = Attendance.objects.filter(
            date__gte=prev_month_start,
            date__lt=current_month_start
        ).count()

        # Expiring trend (members expiring this month vs last)
        next_month = (current_month_start + timedelta(days=32)).replace(day=1)
        current_expiring = Member.objects.filter(
            subscription_end__gte=current_month_start,
            subscription_end__lt=next_month
        ).count()
        prev_expiring = Member.objects.filter(
            subscription_end__gte=prev_month_start,
            subscription_end__lt=current_month_start
        ).count()

        return Response({
            'revenue_trend': calc_trend(current_revenue, prev_revenue),
            'members_trend': calc_trend(current_members, prev_members),
            'attendance_trend': calc_trend(current_attendance, prev_attendance),
            'expiring_trend': calc_trend(current_expiring, prev_expiring),
        })
