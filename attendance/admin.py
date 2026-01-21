"""
Attendance Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin for Attendance - daily check-ins."""
    
    list_display = (
        'member',
        'date',
        'check_in_time',
        'check_out_time',
        'duration_display',
        'member_status',
        'recorded_by',
    )
    list_filter = (
        'date',
        'member__activity_type',
    )
    search_fields = (
        'member__first_name',
        'member__last_name',
        'member__phone',
    )
    ordering = ('-date', '-check_in_time')
    list_per_page = 30
    date_hierarchy = 'date'
    
    readonly_fields = ('created_at',)
    autocomplete_fields = ['member', 'recorded_by']
    
    @admin.display(description='Duration')
    def duration_display(self, obj):
        if obj.check_in_time and obj.check_out_time:
            # Calculate duration
            from datetime import datetime, timedelta
            check_in = datetime.combine(obj.date, obj.check_in_time)
            check_out = datetime.combine(obj.date, obj.check_out_time)
            duration = check_out - check_in
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return "-"
    
    @admin.display(description='Member Status')
    def member_status(self, obj):
        status = obj.member.membership_status
        colors = {
            'ACTIVE': '#28a745',
            'EXPIRED': '#dc3545',
            'PENDING': '#ffc107',
        }
        color = colors.get(status, '#6c757d')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            status
        )
    
    fieldsets = (
        ('Attendance Info', {
            'fields': (
                'member',
                'date',
                ('check_in_time', 'check_out_time'),
            )
        }),
        ('Metadata', {
            'fields': ('recorded_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'member', 'member__activity_type', 'recorded_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Auto-set recorded_by to current user on creation."""
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_changeform_initial_data(self, request):
        """Pre-fill date with today."""
        return {'date': timezone.now().date()}
