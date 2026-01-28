from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, StaffPayment
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    StaffPaymentSerializer, StaffPaymentCreateSerializer
)


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
        token['allowed_gender'] = user.allowed_gender
        
        # Add basic profile info if it exists
        if hasattr(user, 'first_name') and user.first_name:
            token['first_name'] = user.first_name
        
        if hasattr(user, 'last_name') and user.last_name:
            token['last_name'] = user.last_name

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Also add role and allowed_gender to the response body for convenience
        data['role'] = self.user.role
        data['username'] = self.user.username
        data['allowed_gender'] = self.user.allowed_gender
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for login to use our custom serializer.
    """
    serializer_class = CustomTokenObtainPairSerializer


class IsAdminUser(permissions.BasePermission):
    """Only allow admin users to access."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users (staff management).
    Only admins can access this.
    """
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by role if specified
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role.upper())
        
        # Filter by archived status (default: show non-archived)
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        if show_archived:
            queryset = queryset.filter(is_archived=True)
        else:
            queryset = queryset.filter(is_archived=False)
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Prevent deleting yourself
        if instance.id == request.user.id:
            return Response(
                {'error': 'Cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get all payments for a specific staff member."""
        user = self.get_object()
        payments = StaffPayment.objects.filter(staff=user)
        serializer = StaffPaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a user (soft delete)."""
        from django.utils import timezone
        user = self.get_object()
        
        # Prevent archiving yourself
        if user.id == request.user.id:
            return Response({
                'status': 'error',
                'message': 'Cannot archive your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_archived:
            return Response({
                'status': 'error',
                'message': 'User is already archived'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_archived = True
        user.archived_at = timezone.now()
        user.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
        
        return Response({
            'status': 'success',
            'message': 'User archived successfully',
            'is_archived': True,
            'archived_at': user.archived_at
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived user."""
        user = self.get_object()
        
        if not user.is_archived:
            return Response({
                'status': 'error',
                'message': 'User is not archived'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_archived = False
        user.archived_at = None
        user.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
        
        return Response({
            'status': 'success',
            'message': 'User restored successfully',
            'is_archived': False
        })


class IsAdminOrOwnPayments(permissions.BasePermission):
    """
    Allow admins full access, staff can only view their own payments.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Admins have full access
        if request.user.role == 'ADMIN':
            return True
        
        # Staff can only view (GET)
        if request.user.role == 'STAFF' and request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admins can access any payment
        if request.user.role == 'ADMIN':
            return True
        
        # Staff can only access their own payments
        if request.user.role == 'STAFF':
            return obj.staff == request.user
        
        return False


class StaffPaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing staff payments.
    - Admins: Full CRUD access
    - Staff: Read-only access to own payments
    """
    queryset = StaffPayment.objects.all()
    permission_classes = [IsAdminOrOwnPayments]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StaffPaymentCreateSerializer
        return StaffPaymentSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to return full serialized object."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Return full response using read serializer
        read_serializer = StaffPaymentSerializer(instance)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Staff can only see their own payments
        if user.role == 'STAFF':
            queryset = queryset.filter(staff=user)
        
        # Filter by staff_id if specified
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            queryset = queryset.filter(staff_id=staff_id)
        
        # Filter by year if specified
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(period_year=year)
        
        return queryset

