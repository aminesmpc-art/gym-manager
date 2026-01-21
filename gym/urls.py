from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityTypeViewSet, MembershipPlanViewSet, GymViewSet

router = DefaultRouter()
router.register(r'activities', ActivityTypeViewSet)
router.register(r'plans', MembershipPlanViewSet)
router.register(r'info', GymViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
