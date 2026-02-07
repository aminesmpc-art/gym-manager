"""
Attendance model - one record per member per day.
Enhanced with snapshot fields for Smart Check-In system.
"""

from django.db import models
from django.core.exceptions import ValidationError


class Attendance(models.Model):
    """
    Daily attendance records for members.
    Enforces one check-in per member per day.
    Stores member state snapshot at check-in for auditing.
    """
    
    class CheckInResult(models.TextChoices):
        ALLOWED = 'allowed', 'Allowed'
        WARNING = 'warning', 'Warning'
        BLOCKED = 'blocked', 'Blocked'
    
    class CheckInMethod(models.TextChoices):
        MANUAL = 'manual', 'Manual Entry'
        QR = 'qr', 'QR Code Scan'
        STAFF = 'staff', 'Staff Entry'
    
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text='Member who checked in'
    )
    date = models.DateField(
        help_text='Date of attendance'
    )
    check_in_time = models.TimeField(
        null=True,
        blank=True,
        help_text='Check-in time'
    )
    check_out_time = models.TimeField(
        null=True,
        blank=True,
        help_text='Check-out time'
    )
    
    # Staff who recorded this check-in
    recorded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_attendances',
        help_text='Staff member who recorded this attendance'
    )
    
    # Snapshot fields - capture member state at check-in
    activity_at_entry = models.ForeignKey(
        'gym.ActivityType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances',
        help_text='Activity type at time of check-in'
    )
    status_at_entry = models.CharField(
        max_length=20,
        blank=True,
        help_text='Member status at check-in (ACTIVE/EXPIRED/PENDING)'
    )
    debt_at_entry = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Member debt at time of check-in'
    )
    insurance_paid_at_entry = models.BooleanField(
        default=False,
        help_text='Insurance status at time of check-in'
    )
    
    # Check-in decision result
    checkin_result = models.CharField(
        max_length=20,
        choices=CheckInResult.choices,
        default=CheckInResult.ALLOWED,
        help_text='Decision engine result'
    )
    checkin_reason = models.CharField(
        max_length=50,
        blank=True,
        help_text='Reason for check-in result (ok, debt, insurance, expired)'
    )
    
    # Override fields (admin only)
    override_used = models.BooleanField(
        default=False,
        help_text='Whether admin override was used'
    )
    override_reason = models.TextField(
        blank=True,
        help_text='Reason for override (required if override_used=True)'
    )
    
    # Check-in method
    method = models.CharField(
        max_length=10,
        choices=CheckInMethod.choices,
        default=CheckInMethod.STAFF,
        help_text='How the check-in was performed'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-date', '-check_in_time']
        # Enforce one attendance per member per day
        unique_together = ['member', 'date']
    
    def __str__(self):
        return f"{self.member} - {self.date} ({self.checkin_result})"
    
    def clean(self):
        """Validate attendance record."""
        super().clean()
        
        # Validate check-out is after check-in
        if self.check_in_time and self.check_out_time:
            if self.check_out_time < self.check_in_time:
                raise ValidationError("Check-out time must be after check-in time")
        
        # Validate override requires reason
        if self.override_used and not self.override_reason:
            raise ValidationError("Override reason is required when override is used")

