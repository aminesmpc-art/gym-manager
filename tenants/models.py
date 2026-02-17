"""
Tenant models for multi-gym SaaS.
Each Gym is a tenant with its own database schema.
"""

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Gym(TenantMixin):
    """
    Each Gym is a tenant with isolated data.
    The schema_name is auto-created from the gym's slug.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        SUSPENDED = 'suspended', 'Suspended'
    
    class SubscriptionPlan(models.TextChoices):
        TRIAL = 'trial', 'Trial (14 days)'
        PRO = 'pro', 'Pro - 200 DH/month'
        LIFETIME = 'lifetime', 'Lifetime - 2000 DH'
    
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        TRIAL = 'trial', 'Trial'
    
    class BusinessType(models.TextChoices):
        GYM = 'gym', 'Gym'
        SCHOOL = 'school', 'School'
    
    # Gym details
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text='URL-friendly name (e.g., powerhouse-gym)')
    owner_name = models.CharField(max_length=100)
    owner_email = models.EmailField()
    owner_phone = models.CharField(max_length=20)
    
    # Business type
    business_type = models.CharField(
        max_length=10,
        choices=BusinessType.choices,
        default=BusinessType.GYM,
        help_text='Type of business: gym or school'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Subscription / Billing (Cash-based)
    subscription_plan = models.CharField(
        max_length=20,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.TRIAL
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL
    )
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)  # Null for lifetime
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text='Admin notes')
    
    # Required by django-tenants
    auto_create_schema = True
    
    class Meta:
        db_table = 'gyms'
        verbose_name = 'Gym'
        verbose_name_plural = 'Gyms'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def member_limit(self):
        """Return member limit based on subscription plan."""
        # All plans have unlimited members
        return None
    
    @property
    def is_lifetime(self):
        """Check if gym has lifetime subscription."""
        return self.subscription_plan == 'lifetime'
    
    @property
    def is_subscription_active(self):
        """Check if subscription is valid."""
        if self.subscription_status != 'active':
            return False
        if self.is_lifetime:
            return True  # Lifetime never expires
        if self.subscription_end:
            from django.utils import timezone
            return self.subscription_end >= timezone.now().date()
        return False


class Domain(DomainMixin):
    """
    Domain mapping for each gym.
    Examples: gym1.yourdomain.com or gym1.localhost
    """
    
    class Meta:
        db_table = 'domains'
    
    def __str__(self):
        return self.domain
