"""
Serializers for tenant models.
"""

from rest_framework import serializers
from .models import Gym, Domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['id', 'domain', 'is_primary']


class GymSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)
    
    class Meta:
        model = Gym
        fields = [
            'id',
            'schema_name',
            'name',
            'slug',
            'owner_name',
            'owner_email',
            'owner_phone',
            'status',
            'created_at',
            'approved_at',
            'notes',
            'domains',
        ]
        read_only_fields = ['id', 'schema_name', 'created_at', 'approved_at']


class GymRegistrationSerializer(serializers.Serializer):
    """Serializer for public gym registration."""
    name = serializers.CharField(max_length=100)
    slug = serializers.SlugField(max_length=50)
    owner_name = serializers.CharField(max_length=100)
    owner_email = serializers.EmailField()
    owner_phone = serializers.CharField(max_length=20)
    
    def validate_slug(self, value):
        """Ensure slug is unique."""
        if Gym.objects.filter(slug=value).exists():
            raise serializers.ValidationError('A gym with this slug already exists.')
        return value

