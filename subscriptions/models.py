"""
Payment model - source of all income reports.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Payment(models.Model):
    """
    Payment records for membership subscriptions.
    Source of truth for income reports.
    """
    
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'
        TRANSFER = 'TRANSFER', 'Bank Transfer'
    
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='payments',
        help_text='Member who made the payment'
    )
    membership_plan = models.ForeignKey(
        'gym.MembershipPlan',
        on_delete=models.PROTECT,
        related_name='payments',
        help_text='Plan paid for'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Amount paid in local currency (DA)'
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    payment_date = models.DateField(
        help_text='Date of payment'
    )
    
    # Subscription period this payment covers
    period_start = models.DateField(
        help_text='Start date of subscription period'
    )
    period_end = models.DateField(
        help_text='End date of subscription period'
    )
    
    notes = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_payments',
        help_text='Staff member who recorded this payment'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date', '-created_at']
    
    def __str__(self):
        return f"{self.member} - {self.amount} DA ({self.payment_date})"
    
    def save(self, *args, **kwargs):
        """After saving payment, update member's subscription dates."""
        super().save(*args, **kwargs)
        
        # Update member subscription dates
        self.member.subscription_start = self.period_start
        self.member.subscription_end = self.period_end
        self.member.save(update_fields=['subscription_start', 'subscription_end', 'updated_at'])
