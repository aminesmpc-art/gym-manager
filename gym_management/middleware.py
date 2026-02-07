"""
Custom middleware for Railway deployment.
Handles health checks, auto-creates public tenant, and creates superuser if missing.
"""
import os
from django.http import JsonResponse


class HealthCheckMiddleware:
    """
    Middleware that:
    1. Responds to /health/ BEFORE tenant middleware runs
    2. Auto-creates public tenant on first request
    3. Auto-creates superuser if missing
    
    MUST be placed BEFORE TenantMainMiddleware in settings.MIDDLEWARE.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._setup_attempted = False
    
    def __call__(self, request):
        # Respond immediately to health checks - bypass all other middleware
        if request.path == '/health/' or request.path == '/health':
            return JsonResponse({
                'status': 'healthy',
                'service': 'gym-backend'
            })
        
        # On first real request, ensure public tenant and superuser exist
        if not self._setup_attempted:
            self._setup_attempted = True
            hostname = request.get_host().split(':')[0]
            self._ensure_public_tenant(hostname)
            self._ensure_superuser()
        
        return self.get_response(request)
    
    def _ensure_public_tenant(self, hostname):
        """Auto-create public tenant with current hostname if not exists."""
        try:
            from tenants.models import Gym, Domain
            
            # Check if any domain exists for this hostname
            if not Domain.objects.filter(domain=hostname).exists():
                # Get or create public tenant
                public_tenant = Gym.objects.filter(schema_name='public').first()
                
                if not public_tenant:
                    print(f"[Middleware] Creating public tenant...")
                    public_tenant = Gym.objects.create(
                        schema_name='public',
                        name='Public Tenant',
                        slug='public',
                        owner_name='System Admin',
                        owner_email='admin@gym.local',
                        owner_phone='0000000000',
                        status='approved'
                    )
                
                print(f"[Middleware] Adding domain: {hostname}")
                Domain.objects.create(
                    domain=hostname,
                    tenant=public_tenant,
                    is_primary=True
                )
                print(f"[Middleware] Public tenant setup complete for {hostname}!")
                
        except Exception as e:
            print(f"[Middleware] Tenant setup skipped: {e}")
    
    def _ensure_superuser(self):
        """Auto-create superuser if not exists."""
        try:
            from django.contrib.auth import get_user_model
            from django_tenants.utils import schema_context
            
            User = get_user_model()
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gym.local')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
            
            # Create in public schema
            with schema_context('public'):
                if not User.objects.filter(username=username).exists():
                    print(f"[Middleware] Creating superuser: {username}")
                    User.objects.create_superuser(
                        username=username,
                        email=email,
                        password=password
                    )
                    print(f"[Middleware] Superuser {username} created!")
                else:
                    print(f"[Middleware] Superuser {username} already exists")
                    
        except Exception as e:
            print(f"[Middleware] Superuser creation skipped: {e}")
