"""
API endpoints for tenant (gym) management.
Super Admin can list, approve, and suspend gyms.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Sum, Count
from django_tenants.utils import schema_context
from tenants.models import Gym, Domain
from .serializers import GymSerializer, GymRegistrationSerializer


class GymViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing gym tenants.
    Only superadmins can access this.
    """
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter gyms by status if provided."""
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a pending gym application."""
        gym = self.get_object()
        if gym.status == Gym.Status.PENDING:
            gym.status = Gym.Status.APPROVED
            gym.approved_at = timezone.now()
            gym.save()
            
            # Create admin user for the gym
            self._create_gym_admin(gym)
            
            return Response({'status': 'approved', 'gym': GymSerializer(gym).data})
        return Response(
            {'error': f'Cannot approve gym with status: {gym.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def _create_gym_admin(self, gym):
        """Create an admin user for a newly approved gym."""
        try:
            from users.models import User
            from django.utils.crypto import get_random_string
            
            with schema_context(gym.schema_name):
                username = f'{gym.slug}_admin'
                password = get_random_string(12)
                
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': gym.owner_email,
                        'first_name': gym.owner_name.split()[0] if gym.owner_name else 'Admin',
                        'last_name': gym.owner_name.split()[-1] if gym.owner_name else '',
                        'role': 'ADMIN',
                        'is_staff': True,
                        'is_active': True,
                    }
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    # TODO: Send welcome email with credentials
                    print(f"[GymViewSet] Created admin for {gym.name}: {username} / {password}")
        except Exception as e:
            print(f"[GymViewSet] Failed to create admin: {e}")

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend an active gym."""
        gym = self.get_object()
        if gym.status == Gym.Status.APPROVED:
            gym.status = Gym.Status.SUSPENDED
            gym.save()
            return Response({'status': 'suspended', 'gym': GymSerializer(gym).data})
        return Response(
            {'error': f'Cannot suspend gym with status: {gym.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a suspended gym."""
        gym = self.get_object()
        if gym.status == Gym.Status.SUSPENDED:
            gym.status = Gym.Status.APPROVED
            gym.save()
            return Response({'status': 'reactivated', 'gym': GymSerializer(gym).data})
        return Response(
            {'error': f'Cannot reactivate gym with status: {gym.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get real stats for a specific gym tenant."""
        gym = self.get_object()
        
        stats = {
            'members': 0,
            'active_members': 0,
            'staff': 0,
            'revenue': 0,
            'attendance_today': 0,
        }
        
        try:
            with schema_context(gym.schema_name):
                from members.models import Member
                from users.models import User
                from subscriptions.models import Payment
                from attendance.models import Attendance
                
                today = timezone.now().date()
                
                stats['members'] = Member.objects.count()
                stats['active_members'] = Member.objects.filter(
                    subscription_end__gte=today
                ).count()
                stats['staff'] = User.objects.filter(
                    role__in=['STAFF', 'ADMIN', 'OWNER']
                ).count()
                stats['revenue'] = float(
                    Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
                )
                stats['attendance_today'] = Attendance.objects.filter(date=today).count()
        except Exception as e:
            print(f"[GymViewSet.stats] Error querying {gym.schema_name}: {e}")
        
        return Response({
            'gym_id': gym.id,
            'name': gym.name,
            'schema': gym.schema_name,
            'status': gym.status,
            'stats': stats
        })


class SuperAdminDashboardView(APIView):
    """Dashboard stats for Super Admin."""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Get global stats across all gyms."""
        gyms = Gym.objects.exclude(schema_name='public')
        
        stats = {
            'total_gyms': gyms.count(),
            'active_gyms': gyms.filter(status='approved').count(),
            'pending_gyms': gyms.filter(status='pending').count(),
            'suspended_gyms': gyms.filter(status='suspended').count(),
            'total_members': 0,
            'total_revenue': 0,
            'recent_signups': [],
        }
        
        # Get recent gym signups
        recent = gyms.order_by('-created_at')[:5]
        stats['recent_signups'] = GymSerializer(recent, many=True).data
        
        # Aggregate stats from all active gyms
        for gym in gyms.filter(status='approved'):
            try:
                with schema_context(gym.schema_name):
                    from members.models import Member
                    from subscriptions.models import Payment
                    
                    stats['total_members'] += Member.objects.count()
                    stats['total_revenue'] += float(
                        Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
                    )
            except Exception as e:
                print(f"[SuperAdminDashboard] Error querying {gym.schema_name}: {e}")
        
        return Response(stats)


class GymRegistrationView(APIView):
    """
    Public endpoint for gym owners to register their gym.
    Creates a pending gym that needs Super Admin approval.
    """
    permission_classes = [AllowAny]  # Public access
    
    def post(self, request):
        """Register a new gym (pending approval)."""
        serializer = GymRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            # Create gym with pending status
            gym = Gym.objects.create(
                name=serializer.validated_data['name'],
                slug=serializer.validated_data['slug'],
                schema_name=serializer.validated_data['slug'].replace('-', '_'),
                owner_name=serializer.validated_data['owner_name'],
                owner_email=serializer.validated_data['owner_email'],
                owner_phone=serializer.validated_data['owner_phone'],
                status=Gym.Status.PENDING,
            )
            
            return Response({
                'message': 'Gym registration submitted successfully. Pending approval.',
                'gym_id': gym.id,
                'status': gym.status,
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

