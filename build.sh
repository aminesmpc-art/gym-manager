#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create a default superuser on deploy when credentials are provided via env vars.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  # Try to create; if it already exists, update its password and ensure role is ADMIN.
  python manage.py createsuperuser \
    --noinput \
    --username "$DJANGO_SUPERUSER_USERNAME" \
    --email "$DJANGO_SUPERUSER_EMAIL" \
  || python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
u, _ = User.objects.get_or_create(
    username='$DJANGO_SUPERUSER_USERNAME',
    defaults={'email': '$DJANGO_SUPERUSER_EMAIL', 'role': 'ADMIN'}
)
u.email = '$DJANGO_SUPERUSER_EMAIL'
u.role = getattr(User, 'Role', None).ADMIN if hasattr(User, 'Role') else 'ADMIN'
u.set_password('$DJANGO_SUPERUSER_PASSWORD')
u.is_staff = True
u.is_superuser = True
u.save()
print('Superuser ensured:', u.username)
"
fi
