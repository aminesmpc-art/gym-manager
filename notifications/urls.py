from django.urls import path
from .views import SendVerificationCodeView, VerifyCodeView

urlpatterns = [
    path('send-code/', SendVerificationCodeView.as_view(), name='send-verification-code'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
]
