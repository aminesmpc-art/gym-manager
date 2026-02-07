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
    
    # Visual customization
    icon = models.CharField(
        max_length=50,
        blank=True,
        default='fitness_center',
        help_text='Material icon name for UI display'
    )
    color = models.CharField(
        max_length=20,
        blank=True,
        default='#2196F3',
        help_text='Hex color for UI display'
    )
    
    # Multi-language support (FR / AR / EN)
    name_ar = models.CharField(
        max_length=100,
        blank=True,
        help_text='Arabic translation of name'
    )
    name_fr = models.CharField(
        max_length=100,
        blank=True,
        help_text='French translation of name'
    )
    
    is_active = models.BooleanField(default=True)
    
    # Display order for drag & drop reordering
    order = models.PositiveIntegerField(
        default=0,
        help_text='Display order for UI sorting (lower = first)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activity_types'
        verbose_name = 'Activity Type'
        verbose_name_plural = 'Activity Types'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_name(self, lang='en'):
        """Get localized name based on language code."""
        if lang == 'ar' and self.name_ar:
            return self.name_ar
        if lang == 'fr' and self.name_fr:
            return self.name_fr
        return self.name


class MembershipPlan(models.Model):
    """
    Subscription plans belonging to an ActivityType.
    Each plan has a duration and price.
    Enhanced with gender/age filtering and insurance requirements.
    """
    
    class AllowedGender(models.TextChoices):
        MALE = 'male', 'Male Only'
        FEMALE = 'female', 'Female Only'
        ANY = 'any', 'Any Gender'
    
    class AgeCategory(models.TextChoices):
        ADULT = 'adult', 'Adults Only'
        KIDS = 'kids', 'Kids Only'
        ANY = 'any', 'Any Age'
    
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
        help_text='Price in local currency'
    )
    currency = models.CharField(
        max_length=5,
        default='MAD',
        help_text='Currency code (MAD, EUR, USD)'
    )
    
    # Session limits (null = unlimited)
    sessions_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum sessions allowed (null = unlimited)'
    )
    
    # Eligibility filters
    allowed_gender = models.CharField(
        max_length=10,
        choices=AllowedGender.choices,
        default=AllowedGender.ANY,
        help_text='Gender restriction for this plan'
    )
    age_category = models.CharField(
        max_length=10,
        choices=AgeCategory.choices,
        default=AgeCategory.ANY,
        help_text='Age restriction for this plan'
    )
    
    # Insurance requirement
    insurance_required = models.BooleanField(
        default=False,
        help_text='Whether insurance payment is required for check-in'
    )
    
    # Multi-language support
    name_ar = models.CharField(
        max_length=100,
        blank=True,
        help_text='Arabic translation of name'
    )
    name_fr = models.CharField(
        max_length=100,
        blank=True,
        help_text='French translation of name'
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
        unique_together = ['activity_type', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.activity_type.name} ({self.duration_days} days)"
    
    def get_name(self, lang='en'):
        """Get localized name based on language code."""
        if lang == 'ar' and self.name_ar:
            return self.name_ar
        if lang == 'fr' and self.name_fr:
            return self.name_fr
        return self.name

