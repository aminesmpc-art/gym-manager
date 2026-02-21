"""
License model for offline app activation.
Stored in the public schema (shared across all tenants).
"""

import secrets
import string
from django.db import models
from django.utils import timezone


def generate_license_key():
    """Generate a unique license key in format MOL-XXXX-XXXX-XXXX."""
    chars = string.ascii_uppercase + string.digits
    # Remove confusing characters: O, 0, I, 1, L
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('L', '')
    segment = lambda: ''.join(secrets.choice(chars) for _ in range(4))
    return f"MOL-{segment()}-{segment()}-{segment()}"


class License(models.Model):
    """
    License key for offline app activation.
    
    Flow:
    1. Super admin generates a key (via this model)
    2. Customer enters key in local app setup wizard
    3. Local app calls /api/licenses/verify/ to validate
    4. Local app periodically re-verifies (every 7 days)
    5. Super admin can revoke/renew/unbind from the dashboard
    """

    class Tier(models.TextChoices):
        TRIAL = 'trial', 'Trial (14 days)'
        MONTHLY = 'monthly', 'Monthly (30 days)'
        YEARLY = 'yearly', 'Yearly (365 days)'
        LIFETIME = 'lifetime', 'Lifetime'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        REVOKED = 'revoked', 'Revoked'

    # Key
    license_key = models.CharField(
        max_length=20,
        unique=True,
        default=generate_license_key,
        help_text='Auto-generated license key (MOL-XXXX-XXXX-XXXX)',
    )

    # Tier & Status
    tier = models.CharField(
        max_length=20,
        choices=Tier.choices,
        default=Tier.YEARLY,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    # Customer info
    gym_name = models.CharField(max_length=200, blank=True, default='')
    owner_name = models.CharField(max_length=200, blank=True, default='')
    owner_email = models.EmailField(blank=True, default='')
    owner_phone = models.CharField(max_length=30, blank=True, default='')

    # Limits
    max_members = models.IntegerField(default=500)

    # Device binding
    device_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text='Bound device identifier (set on first activation)',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Null = never expires (lifetime)',
    )
    last_verified_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'licenses'
        ordering = ['-created_at']
        verbose_name = 'License'
        verbose_name_plural = 'Licenses'

    def __str__(self):
        return f"{self.license_key} ({self.gym_name or 'Unassigned'})"

    def save(self, *args, **kwargs):
        """Auto-set expiry based on tier if not already set."""
        if not self.expires_at and self.tier != self.Tier.LIFETIME:
            now = timezone.now()
            if self.tier == self.Tier.TRIAL:
                self.expires_at = now + timezone.timedelta(days=14)
            elif self.tier == self.Tier.MONTHLY:
                self.expires_at = now + timezone.timedelta(days=30)
            elif self.tier == self.Tier.YEARLY:
                self.expires_at = now + timezone.timedelta(days=365)

        # Auto-expire if past expiry date
        if self.expires_at and self.expires_at < timezone.now() and self.status == self.Status.ACTIVE:
            self.status = self.Status.EXPIRED

        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Check if this license is currently valid."""
        if self.status == self.Status.REVOKED:
            return False
        if self.status == self.Status.EXPIRED:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def renew(self, new_tier=None):
        """Renew/extend the license."""
        tier = new_tier or self.tier
        now = timezone.now()

        if tier == self.Tier.LIFETIME:
            self.expires_at = None
        elif tier == self.Tier.MONTHLY:
            self.expires_at = now + timezone.timedelta(days=30)
        elif tier == self.Tier.YEARLY:
            self.expires_at = now + timezone.timedelta(days=365)
        elif tier == self.Tier.TRIAL:
            self.expires_at = now + timezone.timedelta(days=14)

        self.tier = tier
        self.status = self.Status.ACTIVE
        self.save()
