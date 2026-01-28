"""
Member model with calculated membership status.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Member(models.Model):
    """
    Gym member profile linked to a User account.
    Membership status is calculated, not stored.
    """
    
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
    
    class AgeCategory(models.TextChoices):
        ADULT = 'ADULT', 'Adult'
        CHILD = 'CHILD', 'Child'
    
    class MembershipStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRED = 'EXPIRED', 'Expired'
        PENDING = 'PENDING', 'Pending'
    
    # Link to User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='member_profile'
    )
    
    # Personal information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        blank=True
    )
    age_category = models.CharField(
        max_length=10,
        choices=AgeCategory.choices,
        blank=True,
        help_text='Age category: Adult or Child'
    )
    phone = models.CharField(
        max_length=20,
        help_text='Phone number (parent phone for kids)'
    )
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Activity and Plan
    activity_type = models.ForeignKey(
        'gym.ActivityType',
        on_delete=models.PROTECT,
        related_name='members',
        help_text='Activity type the member is enrolled in'
    )
    membership_plan = models.ForeignKey(
        'gym.MembershipPlan',
        on_delete=models.PROTECT,
        related_name='members',
        help_text='Current membership plan'
    )
    
    # Subscription dates
    subscription_start = models.DateField(
        null=True,
        blank=True,
        help_text='Start date of current subscription'
    )
    subscription_end = models.DateField(
        null=True,
        blank=True,
        help_text='End date of current subscription (calculated on payment)'
    )
    
    # Metadata
    notes = models.TextField(blank=True, help_text='Internal notes about the member')
    is_active = models.BooleanField(default=True, help_text='Whether the member account is active')
    is_archived = models.BooleanField(default=False, help_text='Archived members are hidden but not deleted')
    archived_at = models.DateTimeField(null=True, blank=True, help_text='When the member was archived')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'members'
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def membership_status(self):
        """
        Calculate membership status based on subscription dates.
        ACTIVE: Current date is before subscription_end
        EXPIRED: Current date is after subscription_end
        PENDING: No subscription dates set (no payment)
        """
        if not self.subscription_start or not self.subscription_end:
            return self.MembershipStatus.PENDING
        
        today = timezone.now().date()
        
        if today <= self.subscription_end:
            return self.MembershipStatus.ACTIVE
        else:
            return self.MembershipStatus.EXPIRED
    
    @property
    def days_remaining(self):
        """Calculate days remaining in subscription."""
        if not self.subscription_end:
            return 0
        
        today = timezone.now().date()
        remaining = (self.subscription_end - today).days
        return max(0, remaining)
    
    @property
    def is_kid(self):
        """Check if member is a minor (under 18)."""
        if not self.date_of_birth:
            return False
        
        today = timezone.now().date()
        age = (today - self.date_of_birth).days // 365
        return age < 18
    
    def renew_subscription(self, start_date=None):
        """
        Renew the subscription based on the current plan.
        Called after payment is recorded.
        """
        if start_date is None:
            start_date = timezone.now().date()
        
        self.subscription_start = start_date
        self.subscription_end = start_date + timedelta(days=self.membership_plan.duration_days)
        self.save(update_fields=['subscription_start', 'subscription_end', 'updated_at'])
