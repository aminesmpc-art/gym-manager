"""
Django management command to create superuser from environment variables.
Used for Railway deployment with django-tenants.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = 'Create superuser from environment variables if not exists'

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gym.local')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        
        # Create superuser in public schema (shared across all tenants)
        try:
            with schema_context('public'):
                if not User.objects.filter(username=username).exists():
                    self.stdout.write(f'Creating superuser: {username}')
                    User.objects.create_superuser(
                        username=username,
                        email=email,
                        password=password
                    )
                    self.stdout.write(self.style.SUCCESS(f'Superuser {username} created!'))
                else:
                    self.stdout.write(f'Superuser {username} already exists')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
            # Try without schema context as fallback
            try:
                if not User.objects.filter(username=username).exists():
                    User.objects.create_superuser(
                        username=username,
                        email=email,
                        password=password
                    )
                    self.stdout.write(self.style.SUCCESS(f'Superuser {username} created (fallback)!'))
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f'Fallback also failed: {e2}'))
