from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer to include user role and basic info in the token payload.
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        
        # Add basic profile info if it exists
        if hasattr(user, 'first_name') and user.first_name:
            token['first_name'] = user.first_name
        
        if hasattr(user, 'last_name') and user.last_name:
            token['last_name'] = user.last_name

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Also add role to the response body for convenience
        data['role'] = self.user.role
        data['username'] = self.user.username
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for login to use our custom serializer.
    """
    serializer_class = CustomTokenObtainPairSerializer
