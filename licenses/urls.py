from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LicenseViewSet, VerifyLicenseView

router = DefaultRouter()
router.register(r'', LicenseViewSet, basename='license')

urlpatterns = [
    # Public endpoint - no auth needed (local app uses this)
    path('verify/', VerifyLicenseView.as_view(), name='license-verify'),
    # Super admin endpoints (auth required)
    path('', include(router.urls)),
]
