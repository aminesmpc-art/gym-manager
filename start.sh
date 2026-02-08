#!/bin/bash
set -e

echo "Starting GYM Backend..."

# Run migrations in background so gunicorn can start immediately
echo "Running migrations in background..."
(
    # Wait longer for database to be ready (Railway takes time)
    echo "Waiting 20 seconds for database to be ready..."
    sleep 20
    
    # Retry logic for migrations
    for i in 1 2 3; do
        echo "Attempt $i: Running migrations..."
        if python manage.py migrate_schemas --shared 2>&1; then
            echo "Shared migrations successful"
            break
        else
            echo "Migration attempt $i failed, waiting 10 seconds..."
            sleep 10
        fi
    done
    
    python manage.py migrate_schemas
    python manage.py setup_public_tenant
    python manage.py create_superuser_if_needed
    
    # Create demo gym with --reset to fix member count
    echo "Creating demo gym with reset..."
    python manage.py create_demo_gym --reset
    
    echo "Migrations and demo setup completed!"
) &

# Start gunicorn immediately so health check passes
echo "Starting gunicorn..."
exec gunicorn gym_management.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2 --log-file -
