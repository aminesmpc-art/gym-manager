from rest_framework import serializers
from .models import License


class LicenseSerializer(serializers.ModelSerializer):
    """Full license serializer for super admin."""

    class Meta:
        model = License
        fields = [
            'id', 'license_key', 'tier', 'status',
            'gym_name', 'owner_name', 'owner_email', 'owner_phone',
            'max_members', 'device_id',
            'created_at', 'expires_at', 'last_verified_at',
            'notes',
        ]
        read_only_fields = ['id', 'license_key', 'created_at', 'last_verified_at']


class GenerateLicenseSerializer(serializers.Serializer):
    """Serializer for license generation request."""
    tier = serializers.ChoiceField(choices=License.Tier.choices, default='yearly')
    gym_name = serializers.CharField(max_length=200)
    owner_name = serializers.CharField(max_length=200, required=False, default='')
    owner_email = serializers.EmailField(required=False, default='', allow_blank=True)
    owner_phone = serializers.CharField(max_length=30, required=False, default='')
    max_members = serializers.IntegerField(default=500, required=False)
    notes = serializers.CharField(required=False, default='', allow_blank=True)


class VerifyLicenseSerializer(serializers.Serializer):
    """Serializer for license verification from local app."""
    license_key = serializers.CharField(max_length=20)
    device_id = serializers.CharField(max_length=200, required=False, default='')
