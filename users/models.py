"""
Custom User model with role-based access.
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
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text='User role determining permissions'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone number'
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
