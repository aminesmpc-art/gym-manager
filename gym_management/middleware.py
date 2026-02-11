"""
Custom middleware for Railway deployment.
Handles health checks, safe tenant resolution, auto-setup, and JWT-based tenant routing.
"""
import os
import jwt
from django.http import JsonResponse
from django.conf import settings
from django.db import connection


class HealthCheckMiddleware:
    """
    Middleware that responds to /health/ BEFORE any tenant middleware runs.
    Also auto-creates public tenant and superuser on first request.
    
    MUST be placed FIRST in settings.MIDDLEWARE.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._setup_attempted = False
    
    def __call__(self, request):
        # Respond immediately to health checks
        if request.path in ('/health/', '/health'):
            return JsonResponse({
                'status': 'healthy',
                'service': 'gym-backend'
            })
        
        # On first real request, ensure public tenant and superuser exist
        if not self._setup_attempted:
            self._setup_attempted = True
            try:
                hostname = request.get_host().split(':')[0]
                self._ensure_public_tenant(hostname)
                self._ensure_superuser()
            except Exception as e:
                print(f"[HealthCheck] Setup error (non-fatal): {e}")
        
        return self.get_response(request)
    
    def _ensure_public_tenant(self, hostname):
        """Auto-create public tenant with current hostname if not exists."""
        try:
            from tenants.models import Gym, Domain
            
            if not Domain.objects.filter(domain=hostname).exists():
                public_tenant = Gym.objects.filter(schema_name='public').first()
                
                if not public_tenant:
                    print(f"[HealthCheck] Creating public tenant...")
                    public_tenant = Gym.objects.create(
                        schema_name='public',
                        name='Public Tenant',
                        slug='public',
                        owner_name='System Admin',
                        owner_email='admin@gym.local',
                        owner_phone='0000000000',
                        status='approved'
                    )
                
                print(f"[HealthCheck] Adding domain: {hostname}")
                Domain.objects.create(
                    domain=hostname,
                    tenant=public_tenant,
                    is_primary=True
                )
                print(f"[HealthCheck] Domain {hostname} added!")
                
        except Exception as e:
            print(f"[HealthCheck] Tenant setup skipped: {e}")
    
    def _ensure_superuser(self):
        """Auto-create superuser if DJANGO_SUPERUSER_PASSWORD is set."""
        try:
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            if not password:
                return
            
            from django.contrib.auth import get_user_model
            from django_tenants.utils import schema_context
            
            User = get_user_model()
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gym.local')
            
            with schema_context('public'):
                if not User.objects.filter(username=username).exists():
                    print(f"[HealthCheck] Creating superuser: {username}")
                    User.objects.create_superuser(
                        username=username,
                        email=email,
                        password=password
                    )
                    print(f"[HealthCheck] Superuser {username} created!")
                    
        except Exception as e:
            print(f"[HealthCheck] Superuser creation skipped: {e}")


class SafeTenantMiddleware:
    """
    REPLACEMENT for django_tenants.middleware.main.TenantMainMiddleware.
    
    The original TenantMainMiddleware hangs/crashes if the domain is not found.
    This middleware safely resolves the tenant or falls back to the public schema.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            hostname = request.get_host().split(':')[0]
            
            from tenants.models import Gym, Domain
            
            # Try to find the domain
            try:
                domain = Domain.objects.select_related('tenant').get(domain=hostname)
                tenant = domain.tenant
            except Domain.DoesNotExist:
                # Domain not found - fall back to public tenant
                print(f"[SafeTenant] Domain '{hostname}' not found, using public schema")
                tenant = Gym.objects.filter(schema_name='public').first()
                
                if tenant is None:
                    # No public tenant exists yet - just use public schema directly
                    print(f"[SafeTenant] No public tenant found, setting schema to 'public'")
                    connection.set_schema('public')
                    request.tenant = None
                    return self.get_response(request)
            
            # Set the tenant on the request and connection
            request.tenant = tenant
            connection.set_tenant(tenant)
            
        except Exception as e:
            print(f"[SafeTenant] Error resolving tenant: {e}, falling back to public")
            connection.set_schema('public')
            request.tenant = None
        
        return self.get_response(request)


class JWTTenantMiddleware:
    """
    Middleware that reads gym_slug from JWT token and switches to the correct tenant schema.
    MUST be placed AFTER AuthenticationMiddleware in settings.MIDDLEWARE.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for unauthenticated endpoints
        if request.path in ('/health/', '/health', '/api/auth/login/', '/api/auth/register/'):
            return self.get_response(request)
        
        # Try to get gym_slug from JWT token
        gym_slug = self._get_gym_slug_from_token(request)
        
        if gym_slug and gym_slug != 'public':
            from django_tenants.utils import schema_context
            
            tenant_exists = False
            try:
                from tenants.models import Gym
                with schema_context('public'):
                    tenant_exists = Gym.objects.filter(schema_name=gym_slug).exists()
            except Exception as e:
                print(f"[JWTTenant] Failed to check tenant: {e}")
            
            if tenant_exists:
                connection.set_schema(gym_slug)
        
        return self.get_response(request)
    
    def _get_gym_slug_from_token(self, request):
        """Extract gym_slug from Authorization header JWT token."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]
        
        try:
            decoded = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return decoded.get('gym_slug', 'public')
        except Exception as e:
            print(f"[JWTTenant] Failed to decode token: {e}")
            return None
