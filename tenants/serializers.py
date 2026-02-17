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
    member_limit = serializers.IntegerField(read_only=True)
    
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
            'business_type',
            'status',
            'subscription_plan',
            'subscription_status',
            'subscription_start',
            'subscription_end',
            'member_limit',
            'created_at',
            'approved_at',
            'notes',
            'domains',
        ]
        read_only_fields = ['id', 'schema_name', 'created_at', 'approved_at', 'member_limit']
    
    def create(self, validated_data):
        """Auto-generate schema_name from slug before creating gym."""
        import re
        slug = validated_data.get('slug', '')
        # Convert slug to valid PostgreSQL schema name:
        # - Replace hyphens with underscores
        # - Remove any non-alphanumeric characters except underscores
        # - Ensure it doesn't start with a number
        schema_name = slug.replace('-', '_')
        schema_name = re.sub(r'[^a-z0-9_]', '', schema_name.lower())
        if schema_name and schema_name[0].isdigit():
            schema_name = 'gym_' + schema_name
        if not schema_name:
            schema_name = 'gym_' + str(validated_data.get('id', 'new'))
        
        validated_data['schema_name'] = schema_name
        return super().create(validated_data)


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

