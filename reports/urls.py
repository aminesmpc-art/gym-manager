from django.urls import path
from .views import DashboardView, RevenueChartView, TrendsView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('revenue-chart/', RevenueChartView.as_view(), name='revenue-chart'),
    path('trends/', TrendsView.as_view(), name='trends'),
]
