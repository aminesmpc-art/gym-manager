"""Create superuser in public schema for Super Admin login."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_management.settings')
django.setup()

from django.db import connection
from users.models import User

# Switch to public schema
connection.set_schema('public')

# Create or update superuser
try:
    user = User.objects.get(username='admin')
    print('Admin user exists, updating password...')
except User.DoesNotExist:
    user = User(username='admin', email='admin@superadmin.com')
    print('Creating new admin user...')

user.is_superuser = True
user.is_staff = True
user.role = 'ADMIN'
user.set_password('admin123')
user.save()

print(f'Done! Admin user ready in public schema.')
print(f'Username: admin')
print(f'Password: admin123')
