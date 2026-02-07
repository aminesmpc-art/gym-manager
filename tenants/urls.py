"""
URL routing for tenant management API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GymViewSet

router = DefaultRouter()
router.register(r'', GymViewSet, basename='gym')

urlpatterns = [
    path('', include(router.urls)),
]
