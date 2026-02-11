FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Default superuser credentials (can be overridden by Railway env vars)
ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=admin@gym.local
ENV DJANGO_SUPERUSER_PASSWORD=admin123

# Railway domain for tenant setup
ENV RAILWAY_PUBLIC_DOMAIN=gym-backend-production-1547.up.railway.app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE $PORT

# Start script:
# 1. Run migrations
# 2. Setup public tenant with Railway domain
# 3. Create superuser
# 4. Start gunicorn
CMD sh -c "python manage.py migrate_schemas --shared && \
    python manage.py migrate_schemas && \
    python manage.py setup_public_tenant && \
    python manage.py create_superuser_if_needed && \
    gunicorn gym_management.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class gthread --timeout 120 --preload --log-level info --access-logfile - --error-logfile -"
