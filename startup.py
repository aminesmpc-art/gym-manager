#!/usr/bin/env python
"""
Startup script for Railway deployment.
Creates the public tenant if it doesn't exist and runs migrations.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_management.settings')
django.setup()

from django_tenants.utils import schema_context
from django.db import connection
from tenants.models import Gym, Domain


def ensure_public_tenant():
    """Create the public tenant if it doesn't exist."""
    try:
        with schema_context('public'):
            # Check if public tenant exists
            if not Gym.objects.filter(schema_name='public').exists():
                print("Creating public tenant...")
                public_gym = Gym.objects.create(
                    schema_name='public',
                    name='Public Tenant',
                    slug='public',
                    owner_name='System',
                    owner_email='admin@gym.local',
                    owner_phone='0000000000',
                    status='approved'
                )
                
                # Create domain for Railway
                Domain.objects.create(
                    domain='gym-backend-production-2.up.railway.app',
                    tenant=public_gym,
                    is_primary=True
                )
                print("Public tenant created successfully!")
            else:
                print("Public tenant already exists.")
    except Exception as e:
        print(f"Error creating public tenant: {e}")
        # Don't fail - migrations might not have run yet


if __name__ == '__main__':
    ensure_public_tenant()
