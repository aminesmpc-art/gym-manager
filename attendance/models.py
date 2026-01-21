"""
Attendance model - one record per member per day.
"""

from django.db import models
from django.core.exceptions import ValidationError


class Attendance(models.Model):
    """
    Daily attendance records for members.
    Enforces one check-in per member per day.
    """
    
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
    
    # Metadata
    recorded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_attendances',
        help_text='Staff member who recorded this attendance'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-date', '-check_in_time']
        # Enforce one attendance per member per day
        unique_together = ['member', 'date']
    
    def __str__(self):
        return f"{self.member} - {self.date}"
    
    def clean(self):
        """Validate attendance record."""
        super().clean()
        
        # Check if member has active subscription
        if self.member.membership_status != 'ACTIVE':
            raise ValidationError(
                f"Cannot record attendance for {self.member}: membership is {self.member.membership_status}"
            )
        
        # Validate check-out is after check-in
        if self.check_in_time and self.check_out_time:
            if self.check_out_time < self.check_in_time:
                raise ValidationError("Check-out time must be after check-in time")
