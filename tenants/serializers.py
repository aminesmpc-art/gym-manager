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
