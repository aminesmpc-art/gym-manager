"""
Django management command to create public tenant with Railway domain.
This is required for django-tenants to route requests properly.
"""
import os
from django.core.management.base import BaseCommand
from django.db import connection
from tenants.models import Gym, Domain


class Command(BaseCommand):
    help = 'Create public tenant with Railway domain if not exists'

    def handle(self, *args, **options):
        # Get Railway domain from environment or use default
        railway_domain = os.environ.get(
            'RAILWAY_PUBLIC_DOMAIN', 
            'gym-backend-production-2b99.up.railway.app'
        )
        
        self.stdout.write(f'Setting up public tenant for domain: {railway_domain}')
        
        try:
            # Check if public tenant exists
            public_tenant = Gym.objects.filter(schema_name='public').first()
            
            if not public_tenant:
                self.stdout.write('Creating public tenant...')
                public_tenant = Gym.objects.create(
                    schema_name='public',
                    name='Public Tenant',
                    slug='public',
                    owner_name='System Admin',
                    owner_email='admin@gym.local',
                    owner_phone='0000000000',
                    status='approved'
                )
                self.stdout.write(self.style.SUCCESS('Public tenant created!'))
            else:
                self.stdout.write('Public tenant already exists.')
            
            # Check if Railway domain exists
            domain_exists = Domain.objects.filter(domain=railway_domain).exists()
            
            if not domain_exists:
                self.stdout.write(f'Adding domain: {railway_domain}')
                Domain.objects.create(
                    domain=railway_domain,
                    tenant=public_tenant,
                    is_primary=True
                )
                self.stdout.write(self.style.SUCCESS(f'Domain {railway_domain} added!'))
            else:
                self.stdout.write(f'Domain {railway_domain} already exists.')
            
            # Also add localhost for development
            if not Domain.objects.filter(domain='localhost').exists():
                Domain.objects.create(
                    domain='localhost',
                    tenant=public_tenant,
                    is_primary=False
                )
                self.stdout.write('Added localhost domain for development.')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise
