#!/bin/bash
set -e

echo "Starting GYM Backend..."

# Run migrations in background so gunicorn can start immediately
echo "Running migrations in background..."
(
    sleep 5  # Give gunicorn time to start
    python manage.py migrate_schemas --shared
    python manage.py migrate_schemas
    python manage.py setup_public_tenant
    python manage.py create_superuser_if_needed
    # Create demo gym with --reset to fix member count (remove --reset after first deploy)
    echo "Creating demo gym with reset..."
    python manage.py create_demo_gym --reset
    echo "Migrations and demo setup completed!"
) &

# Start gunicorn immediately so health check passes
echo "Starting gunicorn..."
exec gunicorn gym_management.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2 --log-file -

