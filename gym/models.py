"""
Core gym models: Gym, ActivityType, MembershipPlan
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Gym(models.Model):
    """
    Single gym instance (V1 supports only one gym).
    Stores basic gym information.
    """
    
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    
    # Operating hours (optional for V1)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'gym'
        verbose_name = 'Gym'
        verbose_name_plural = 'Gym'
    
    def __str__(self):
        return self.name


class ActivityType(models.Model):
    """
    Types of activities offered by the gym.
    Examples: Bodybuilding, EMM Adults, Kids
    """
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activity_types'
        verbose_name = 'Activity Type'
        verbose_name_plural = 'Activity Types'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class MembershipPlan(models.Model):
    """
    Subscription plans belonging to an ActivityType.
    Each plan has a duration and price.
    """
    
    name = models.CharField(max_length=100)
    activity_type = models.ForeignKey(
        ActivityType,
        on_delete=models.PROTECT,
        related_name='plans',
        help_text='Activity type this plan belongs to'
    )
    duration_days = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Duration of the plan in days'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price in local currency (DA)'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'membership_plans'
        verbose_name = 'Membership Plan'
        verbose_name_plural = 'Membership Plans'
        ordering = ['activity_type', 'duration_days']
        # Ensure unique plan names within the same activity type
        unique_together = ['activity_type', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.activity_type.name} ({self.duration_days} days)"
