"""
Gym Admin Configuration - Gym, ActivityType, MembershipPlan
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Gym, ActivityType, MembershipPlan


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    """Admin for single Gym instance."""
    
    list_display = ('name', 'phone', 'email', 'operating_hours', 'updated_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    @admin.display(description='Operating Hours')
    def operating_hours(self, obj):
        if obj.opening_time and obj.closing_time:
            return f"{obj.opening_time.strftime('%H:%M')} - {obj.closing_time.strftime('%H:%M')}"
        return "Not set"
    
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'description')}),
        ('Contact', {'fields': ('address', 'phone', 'email')}),
        ('Hours', {'fields': ('opening_time', 'closing_time')}),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one gym instance
        if Gym.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of gym
        return False


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    """Admin for Activity Types (Bodybuilding, EMM Adults, Kids, etc.)"""
    
    list_display = ('name', 'status_badge', 'plans_count', 'members_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at')
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745;">● Active</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">● Inactive</span>'
        )
    
    @admin.display(description='Plans')
    def plans_count(self, obj):
        return obj.plans.count()
    
    @admin.display(description='Members')
    def members_count(self, obj):
        return obj.members.count()
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'is_active')}),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    """Admin for Membership Plans."""
    
    list_display = (
        'name', 
        'activity_type', 
        'duration_display', 
        'price_display',
        'members_count',
        'status_badge'
    )
    list_filter = ('activity_type', 'is_active', 'duration_days')
    search_fields = ('name', 'activity_type__name', 'description')
    ordering = ('activity_type', 'duration_days')
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at')
    
    @admin.display(description='Duration')
    def duration_display(self, obj):
        if obj.duration_days == 30:
            return "1 Month"
        elif obj.duration_days == 90:
            return "3 Months"
        elif obj.duration_days == 180:
            return "6 Months"
        elif obj.duration_days == 365:
            return "1 Year"
        return f"{obj.duration_days} days"
    
    @admin.display(description='Price')
    def price_display(self, obj):
        return format_html(
            '<strong>{:,.0f} DA</strong>',
            obj.price
        )
    
    @admin.display(description='Members')
    def members_count(self, obj):
        return obj.members.count()
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #28a745;">● Active</span>')
        return format_html('<span style="color: #dc3545;">● Inactive</span>')
    
    fieldsets = (
        (None, {'fields': ('name', 'activity_type')}),
        ('Pricing', {'fields': ('duration_days', 'price')}),
        ('Details', {'fields': ('description', 'is_active')}),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
