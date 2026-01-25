#!/usr/bin/env bash
# Factory Reset Script
# WARNING: This deletes all data!

# 1. Delete the database file
if [ -f "db.sqlite3" ]; then
    rm db.sqlite3
    echo "Database deleted."
fi

# 2. Run migrations to create fresh tables
python manage.py migrate
echo "Fresh database created."

# 3. Create a default admin user
# You can customize this or let the user do it manually
# python manage.py createsuperuser --noinput --username admin --email admin@example.com
echo "Please run 'python manage.py createsuperuser' to create your new admin account."
