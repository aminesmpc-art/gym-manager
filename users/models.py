"""
Custom User model with role-based access and Staff Payment tracking.
"""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "ADMIN")
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    objects = CustomUserManager()
    """
    Custom User model with roles for the Gym Management System.
    Roles: ADMIN, STAFF, MEMBER
    """
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        STAFF = 'STAFF', 'Staff'
        MEMBER = 'MEMBER', 'Member'
    
    class AllowedGender(models.TextChoices):
        MEN = 'M', 'Men'
        WOMEN = 'F', 'Women'
        CHILDREN = 'CHILD', 'Children'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text='User role determining permissions'
    )
    allowed_gender = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text='Gender categories this staff can manage, comma-separated (e.g. "M,F" or "CHILD"). Null = all.'
    )
    monthly_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Fixed monthly salary for staff members'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone number'
    )
    is_archived = models.BooleanField(
        default=False,
        help_text='Archived users are hidden but not deleted'
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the user was archived'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF
    
    @property
    def is_gym_member(self):
        return self.role == self.Role.MEMBER


class StaffPayment(models.Model):
    """
    Track monthly salary payments to staff members.
    """
    
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK = 'BANK', 'Bank Transfer'
        CHECK = 'CHECK', 'Check'
    
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='salary_payments',
        limit_choices_to={'role': 'STAFF'}
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Payment amount'
    )
    payment_date = models.DateField(
        help_text='Date payment was made'
    )
    period_month = models.IntegerField(
        help_text='Month this payment covers (1-12)'
    )
    period_year = models.IntegerField(
        help_text='Year this payment covers'
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    notes = models.TextField(
        blank=True,
        help_text='Optional notes about the payment'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_staff_payments',
        help_text='Admin who recorded this payment'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'staff_payments'
        verbose_name = 'Staff Payment'
        verbose_name_plural = 'Staff Payments'
        ordering = ['-payment_date', '-created_at']
        # Prevent duplicate payments for same staff/month/year
        unique_together = ['staff', 'period_month', 'period_year']
    
    def __str__(self):
        return f"{self.staff.username} - {self.period_month}/{self.period_year} - {self.amount}"
    
    @property
    def period_display(self):
        """Return formatted period string."""
        import calendar
        month_name = calendar.month_name[self.period_month]
        return f"{month_name} {self.period_year}"
