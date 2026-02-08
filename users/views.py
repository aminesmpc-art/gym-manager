from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from django.contrib.auth import authenticate
from django_tenants.utils import schema_context
from .models import User, StaffPayment
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    StaffPaymentSerializer, StaffPaymentCreateSerializer,
    ChangePasswordSerializer
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer with multi-tenant gym_slug support.
    Accepts gym_slug to authenticate users within a specific gym's schema.
    """
    
    gym_slug = serializers.CharField(required=False, default='public', write_only=True)
    
    @classmethod
    def get_token(cls, user, gym_slug='public'):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        token['allowed_gender'] = user.allowed_gender
        token['gym_slug'] = gym_slug  # Store gym_slug in token
        
        # Add basic profile info if it exists
        if hasattr(user, 'first_name') and user.first_name:
            token['first_name'] = user.first_name
        
        if hasattr(user, 'last_name') and user.last_name:
            token['last_name'] = user.last_name

        return token

    def validate(self, attrs):
        gym_slug = attrs.pop('gym_slug', 'public')
        username = attrs.get('username')
        password = attrs.get('password')
        
        # Special handling for public schema (Super Admin)
        if gym_slug == 'public':
            # Authenticate super admin in public schema
            with schema_context('public'):
                user = authenticate(username=username, password=password)
                if user is None:
                    raise serializers.ValidationError({'detail': 'Invalid username or password.'})
                if not user.is_active:
                    raise serializers.ValidationError({'detail': 'User account is disabled.'})
                if not user.is_superuser:
                    raise serializers.ValidationError({'detail': 'Super Admin access required.'})
                
                self.user = user
                
                # Generate tokens
                refresh = self.get_token(user, 'public')
                
                return {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'role': user.role,
                    'username': user.username,
                    'allowed_gender': user.allowed_gender,
                    'gym_slug': 'public',
                    'gym_name': 'Super Admin',
                }
        
        # Validate gym_slug exists for tenant users
        from tenants.models import Gym
        try:
            with schema_context('public'):
                gym = Gym.objects.get(schema_name=gym_slug)
                if gym.status != 'approved':
                    raise serializers.ValidationError({'gym_slug': 'This gym is not active.'})
        except Gym.DoesNotExist:
            raise serializers.ValidationError({'gym_slug': 'Invalid gym code.'})
        
        # Authenticate within the tenant schema
        with schema_context(gym_slug):
            user = authenticate(username=username, password=password)
            if user is None:
                raise serializers.ValidationError({'detail': 'Invalid username or password.'})
            if not user.is_active:
                raise serializers.ValidationError({'detail': 'User account is disabled.'})
            
            self.user = user
            
            # Generate tokens
            refresh = self.get_token(user, gym_slug)
            
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': user.role,
                'username': user.username,
                'allowed_gender': user.allowed_gender,
                'gym_slug': gym_slug,
                'gym_name': gym.name,
            }
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for login with multi-tenant gym_slug support.
    
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

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current authenticated user's profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change the current user's password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save(update_fields=['password', 'updated_at'])
            return Response({
                'status': 'success',
                'message': 'Password changed successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

