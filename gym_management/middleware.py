"""
Custom middleware for Railway deployment.
Bypasses tenant resolution for health check endpoints.
"""
from django.http import JsonResponse


class HealthCheckMiddleware:
    """
    Middleware that responds to /health/ BEFORE tenant middleware runs.
    This ensures Railway healthcheck works even if no tenant is configured.
    
    MUST be placed BEFORE TenantMainMiddleware in settings.MIDDLEWARE.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Respond immediately to health checks - bypass all other middleware
        if request.path == '/health/' or request.path == '/health':
            return JsonResponse({
                'status': 'healthy',
                'service': 'gym-backend'
            })
        
        # Also handle root path for basic availability check
        if request.path == '/' and request.method == 'GET':
            # Check if this looks like a healthcheck (no cookies, basic request)
            if not request.COOKIES and request.headers.get('User-Agent', '').startswith('Railway'):
                return JsonResponse({
                    'status': 'ok',
                    'service': 'gym-backend'
                })
        
        return self.get_response(request)
