"""
Members Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin for Gym Members."""
    
    list_display = (
        'full_name',
        'phone',
        'activity_type',
        'membership_plan',
        'status_badge',
        'days_remaining_display',
        'subscription_end',
    )
    list_filter = (
        'activity_type', 
        'membership_plan', 
        'gender',
        'is_active',
        'created_at'
    )
    search_fields = (
        'first_name', 
        'last_name', 
        'phone', 
        'email',
        'user__username'
    )
    ordering = ('-created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    readonly_fields = (
        'membership_status', 
        'days_remaining', 
        'is_kid',
        'created_at', 
        'updated_at'
    )
    
    # Autocomplete for related fields
    autocomplete_fields = ['user', 'activity_type', 'membership_plan']
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        status = obj.membership_status
        colors = {
            'ACTIVE': '#28a745',
            'EXPIRED': '#dc3545',
            'PENDING': '#ffc107',
        }
        color = colors.get(status, '#6c757d')
        text_color = '#000' if status == 'PENDING' else '#fff'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            status
        )
    
    @admin.display(description='Days Left')
    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days == 0:
            return format_html('<span style="color: #dc3545;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: #ffc107;">{} days</span>', days)
        return format_html('<span style="color: #28a745;">{} days</span>', days)
    
    fieldsets = (
        ('Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name'),
                ('date_of_birth', 'gender'),
                ('phone', 'email'),
                'address'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                ('emergency_contact_name', 'emergency_contact_phone'),
            ),
            'classes': ('collapse',)
        }),
        ('Membership', {
            'fields': (
                ('activity_type', 'membership_plan'),
                ('subscription_start', 'subscription_end'),
                ('membership_status', 'days_remaining'),
            )
        }),
        ('Status & Notes', {
            'fields': ('is_active', 'is_kid', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'user', 'activity_type', 'membership_plan'
        )
