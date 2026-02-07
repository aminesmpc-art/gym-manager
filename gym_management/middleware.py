"""
Custom middleware for Railway deployment.
Handles health checks and auto-creates public tenant if missing.
"""
import os
from django.http import JsonResponse
from django.db import connection


class HealthCheckMiddleware:
    """
    Middleware that responds to /health/ BEFORE tenant middleware runs.
    This ensures Railway healthcheck works even if no tenant is configured.
    
    MUST be placed BEFORE TenantMainMiddleware in settings.MIDDLEWARE.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._tenant_setup_attempted = False
    
    def __call__(self, request):
        # Respond immediately to health checks - bypass all other middleware
        if request.path == '/health/' or request.path == '/health':
            return JsonResponse({
                'status': 'healthy',
                'service': 'gym-backend'
            })
        
        # On first real request, ensure public tenant exists
        if not self._tenant_setup_attempted:
            self._tenant_setup_attempted = True
            self._ensure_public_tenant(request.get_host().split(':')[0])
        
        return self.get_response(request)
    
    def _ensure_public_tenant(self, hostname):
        """Auto-create public tenant with current hostname if not exists."""
        try:
            from tenants.models import Gym, Domain
            from django_tenants.utils import schema_context
            
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
            # Log but don't crash - migrations might not have run yet
            print(f"[Middleware] Tenant setup skipped: {e}")
