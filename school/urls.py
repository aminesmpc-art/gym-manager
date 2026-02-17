"""
School-specific URL patterns.
Mounted at /api/school/ in the main urls.py.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolStaffViewSet, SchoolStudentViewSet

router = DefaultRouter()
router.register(r'staff', SchoolStaffViewSet, basename='school-staff')
router.register(r'students', SchoolStudentViewSet, basename='school-student')

urlpatterns = [
    path('', include(router.urls)),
]
