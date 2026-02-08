"""
URL routing for tenant management API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GymViewSet, SuperAdminDashboardView, GymRegistrationView

router = DefaultRouter()
router.register(r'', GymViewSet, basename='gym')

urlpatterns = [
    path('dashboard/', SuperAdminDashboardView.as_view(), name='superadmin-dashboard'),
    path('register/', GymRegistrationView.as_view(), name='gym-register'),
    path('', include(router.urls)),
]

