"""
Django settings for gym_management project.
Configured for multi-tenant SaaS with django-tenants.
"""

import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: SECRET_KEY must be set in production via env var.
# Fallback is only for Docker build (collectstatic). Never use in production.
SECRET_KEY = config('SECRET_KEY', default='build-only-not-for-production')

# SECURITY: Defaults to False (production mode)
DEBUG = config('DEBUG', default=False, cast=bool)

# Railway and production hosts
ALLOWED_HOSTS = ["*"]

# CSRF trusted origins for Railway
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
]



# ============= MULTI-TENANCY CONFIG =============

# Shared apps - available to all schemas (public + each tenant)
SHARED_APPS = [
    'django_tenants',
    'tenants',  # Our tenant management app
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party - shared
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # Users must be shared for super admin auth to work
    'users',
]

# Tenant apps - each gym gets their own isolated data
TENANT_APPS = [
    # These MUST be duplicated in tenant schemas for proper isolation
    'django.contrib.contenttypes',
    'django.contrib.auth',
    
    # Local apps - isolated per gym (users removed - now in SHARED_APPS)
    'gym',
    'members',
    'subscriptions',
    'attendance',
    'reports',
    'notifications',
]

# Combined - all apps available
INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# Tenant model config
TENANT_MODEL = 'tenants.Gym'
TENANT_DOMAIN_MODEL = 'tenants.Domain'

# ============= END MULTI-TENANCY CONFIG =============


MIDDLEWARE = [
    # Health check MUST be first - responds before tenant resolution
    'gym_management.middleware.HealthCheckMiddleware',
    'gym_management.middleware.SafeTenantMiddleware',  # Safe tenant resolution (replaces TenantMainMiddleware)
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'gym_management.middleware.JWTTenantMiddleware',  # JWT-based tenant switching
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============= INTERNATIONALIZATION =============
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Casablanca'
USE_I18N = True
USE_TZ = True

ROOT_URLCONF = 'gym_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gym_management.wsgi.application'


# Database - PostgreSQL required for django-tenants
import dj_database_url

DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # Override engine to use django-tenants backend (required for schema routing)
    DATABASES['default']['ENGINE'] = 'django_tenants.postgresql_backend'
else:
    # Local PostgreSQL for development
    DATABASES = {
        'default': {
            'ENGINE': 'django_tenants.postgresql_backend',
            'NAME': config('DB_NAME', default='gym_saas'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Required for django-tenants
DATABASE_ROUTERS = ['django_tenants.routers.TenantSyncRouter']


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Algiers'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Custom User Model
AUTH_USER_MODEL = 'users.User'


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'gym_management.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 20,
    'PAGE_SIZE_QUERY_PARAM': 'page_size',
    'MAX_PAGE_SIZE': 1000,
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/min',
    },
}


# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# CORS Settings
# Flutter apps (mobile + web) call from various origins,
# so we allow all origins. Auth is handled by JWT, not cookies.
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# Twilio settings (optional - for SMS)
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')


# ============= SECURITY HEADERS (Production) =============
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # NOTE: Do NOT enable SECURE_SSL_REDIRECT — Railway handles SSL at the proxy.
    # Enabling it causes redirect loops since internal traffic is HTTP.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ============= LOGGING =============
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
