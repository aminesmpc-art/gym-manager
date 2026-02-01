"""
API Views for Phone Number Verification.
"""

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from notifications.verification import phone_verification


class SendVerificationCodeView(views.APIView):
    """Send OTP verification code to a phone number."""
    permission_classes = [AllowAny]  # Allow for new member registration
    
    def post(self, request):
        phone = request.data.get('phone')
        name = request.data.get('name', '')
        
        if not phone:
            return Response(
                {'error': 'Phone number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = phone_verification.send_otp(phone, name)
        
        if result['success']:
            return Response({
                'message': result['message'],
                'expires_in_minutes': result.get('expires_in_minutes', 10)
            })
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyCodeView(views.APIView):
    """Verify OTP code for a phone number."""
    permission_classes = [AllowAny]  # Allow for new member registration
    
    def post(self, request):
        phone = request.data.get('phone')
        code = request.data.get('code')
        
        if not phone or not code:
            return Response(
                {'error': 'Phone number and code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = phone_verification.verify_otp(phone, str(code))
        
        if result['verified']:
            return Response({
                'verified': True,
                'message': result['message']
            })
        else:
            return Response({
                'verified': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
