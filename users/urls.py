from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, StaffPaymentViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

# Separate router for payments (will be at /api/staff-payments/)
payment_router = DefaultRouter()
payment_router.register(r'', StaffPaymentViewSet, basename='staff-payment')

urlpatterns = [
    path('', include(router.urls)),
]

# Export payment URLs to be included separately
payment_urls = [
    path('', include(payment_router.urls)),
]
