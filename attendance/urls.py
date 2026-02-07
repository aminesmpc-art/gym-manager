from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, SmartCheckInView

router = DefaultRouter()
router.register(r'', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('checkin/', SmartCheckInView.as_view(), name='smart-checkin'),
    path('', include(router.urls)),
]

