"""
Subscriptions (Payments) Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payments - source of income reports."""
    
    list_display = (
        'member',
        'membership_plan',
        'amount_display',
        'payment_method_badge',
        'payment_date',
        'period_display',
        'created_by',
    )
    list_filter = (
        'payment_method',
        'payment_date',
        'membership_plan__activity_type',
        'membership_plan',
    )
    search_fields = (
        'member__first_name',
        'member__last_name',
        'member__phone',
        'notes',
    )
    ordering = ('-payment_date', '-created_at')
    list_per_page = 25
    date_hierarchy = 'payment_date'
    
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['member', 'membership_plan', 'created_by']
    
    @admin.display(description='Amount')
    def amount_display(self, obj):
        return format_html(
            '<strong style="color: #28a745;">{:,.0f} DA</strong>',
            obj.amount
        )
    
    @admin.display(description='Method')
    def payment_method_badge(self, obj):
        colors = {
            'CASH': '#28a745',
            'CARD': '#007bff',
            'TRANSFER': '#6f42c1',
        }
        color = colors.get(obj.payment_method, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_payment_method_display()
        )
    
    @admin.display(description='Period')
    def period_display(self, obj):
        return f"{obj.period_start} → {obj.period_end}"
    
    fieldsets = (
        ('Payment Info', {
            'fields': (
                ('member', 'membership_plan'),
                ('amount', 'payment_method'),
                'payment_date',
            )
        }),
        ('Subscription Period', {
            'fields': (
                ('period_start', 'period_end'),
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'member', 'membership_plan', 'membership_plan__activity_type', 'created_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
