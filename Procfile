web: gunicorn gym_management.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --worker-class gthread --timeout 120 --log-level debug --access-logfile - --error-logfile -
