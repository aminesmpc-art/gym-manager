from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import CustomTokenObtainPairView
from users.urls import payment_urls


def root(request):
    """Simple root endpoint so the Render homepage doesn't 404."""
    return JsonResponse(
        {
            "status": "ok",
            "app": "gym-backend",
            "endpoints": [
                "/api/auth/login/",
                "/api/users/",
                "/api/members/",
                "/api/subscriptions/",
                "/api/attendance/",
                "/api/reports/",
            ],
        }
    )


urlpatterns = [
    path('', root, name='root'),
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/staff-payments/', include(payment_urls)),
    path('api/gym/', include('gym.urls')),
    path('api/members/', include('members.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/verify/', include('notifications.urls')),
]
