"""
URL configuration for gym_management project.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/gym/', include('gym.urls')),
    path('api/members/', include('members.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/reports/', include('reports.urls')),
]
