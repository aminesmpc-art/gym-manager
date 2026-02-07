"""
Django management command to create superuser from environment variables.
Used for Railway deployment with django-tenants.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = 'Create or update superuser from environment variables'

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gym.local')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        
        # Create or update superuser in public schema
        try:
            with schema_context('public'):
                user, created = User.objects.update_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                        'role': 'ADMIN',
                    }
                )
                user.set_password(password)
                user.save()
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Superuser {username} created!'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Superuser {username} updated!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            # Fallback without schema context
            try:
                user, created = User.objects.update_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                        'role': 'ADMIN',
                    }
                )
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Superuser {username} {"created" if created else "updated"} (fallback)!'))
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f'Fallback failed: {e2}'))
