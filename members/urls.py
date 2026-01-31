from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MemberViewSet, NotificationBotView

router = DefaultRouter()
router.register(r'', MemberViewSet, basename='members')

router.register(r'notify', NotificationBotView, basename='notify')

urlpatterns = [
    path('', include(router.urls)),
]
