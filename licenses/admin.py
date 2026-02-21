from django.contrib import admin
from .models import License


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = [
        'license_key', 'gym_name', 'tier', 'status',
        'owner_name', 'expires_at', 'device_id', 'created_at',
    ]
    list_filter = ['tier', 'status']
    search_fields = ['license_key', 'gym_name', 'owner_name', 'owner_email']
    readonly_fields = ['license_key', 'created_at', 'last_verified_at']
    ordering = ['-created_at']
