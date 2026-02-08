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
        FREE_TRIAL = 'free_trial', 'Free Trial (14 days)'
        BASIC = 'basic', 'Basic - 200 DH/mo'
        PRO = 'pro', 'Pro - 500 DH/mo'
        ENTERPRISE = 'enterprise', 'Enterprise - Custom'
    
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAST_DUE = 'past_due', 'Past Due'
        CANCELLED = 'cancelled', 'Cancelled'
        TRIAL = 'trial', 'Trial'
    
    # Gym details
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text='URL-friendly name (e.g., powerhouse-gym)')
    owner_name = models.CharField(max_length=100)
    owner_email = models.EmailField()
    owner_phone = models.CharField(max_length=20)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Subscription / Billing
    subscription_plan = models.CharField(
        max_length=20,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.FREE_TRIAL
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL
    )
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)
    
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
        limits = {
            'free_trial': 50,
            'basic': 100,
            'pro': 500,
            'enterprise': None,  # Unlimited
        }
        return limits.get(self.subscription_plan)


class Domain(DomainMixin):
    """
    Domain mapping for each gym.
    Examples: gym1.yourdomain.com or gym1.localhost
    """
    
    class Meta:
        db_table = 'domains'
    
    def __str__(self):
        return self.domain
