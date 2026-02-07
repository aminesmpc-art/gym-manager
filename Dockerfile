FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

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

# Start server - use migrate_schemas for django-tenants
CMD ["sh", "-c", "python manage.py migrate_schemas --shared && python manage.py migrate_schemas && gunicorn gym_management.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class gthread --log-level info --access-logfile - --error-logfile -"]
