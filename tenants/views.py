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


class AdminResetDemoView(APIView):
    """
    Admin utility endpoint. Uses a secret key instead of login.
    Usage: 
      - POST /api/tenants/admin/reset-demo/?secret=gym_reset_2026 - Reset demo data
      - POST /api/tenants/admin/reset-demo/?secret=gym_reset_2026&action=create_superuser - Create superuser
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Simple secret key check
        secret = request.query_params.get('secret')
        if secret != 'gym_reset_2026':
            return Response(
                {'error': 'Invalid secret key'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        action = request.query_params.get('action', 'reset_demo')
        
        # Create superuser action
        if action == 'create_superuser':
            return self._create_superuser()
        
        # Default: Reset demo data
        return self._reset_demo()
    
    def _create_superuser(self):
        """Create/update superuser in public schema."""
        from django.contrib.auth import get_user_model
        from django_tenants.utils import schema_context
        
        User = get_user_model()
        try:
            with schema_context('public'):
                user, created = User.objects.update_or_create(
                    username='admin',
                    defaults={
                        'email': 'admin@gym.local',
                        'first_name': 'Super',
                        'last_name': 'Admin',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                        'role': 'ADMIN',
                    }
                )
                user.set_password('admin123')
                user.save()
                
                return Response({
                    'status': 'success',
                    'message': f'Superuser {"created" if created else "updated"}',
                    'credentials': {
                        'gym_slug': 'public',
                        'username': 'admin',
                        'password': 'admin123'
                    }
                })
        except Exception as e:
            import traceback
            return Response(
                {'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _reset_demo(self):
        """Reset demo gym data."""
        from django.core.management import call_command
        from io import StringIO
        import traceback
        
        try:
            out = StringIO()
            err = StringIO()
            call_command('create_demo_gym', '--reset', stdout=out, stderr=err)
            output = out.getvalue()
            errors = err.getvalue()
            return Response({
                'status': 'success',
                'message': 'Demo data reset to 120 members',
                'output': output,
                'errors': errors
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            
            # Create admin user for the gym and get credentials
            admin_credentials = self._create_gym_admin(gym)
            
            response_data = {
                'status': 'approved',
                'gym': GymSerializer(gym).data,
            }
            
            if admin_credentials:
                response_data['admin_credentials'] = admin_credentials
            
            return Response(response_data)
        return Response(
            {'error': f'Cannot approve gym with status: {gym.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def _create_gym_admin(self, gym):
        """Create an admin user for a newly approved gym. Returns credentials dict."""
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
                    print(f"[GymViewSet] Created admin for {gym.name}: {username} / {password}")
                    return {
                        'username': username,
                        'password': password,
                        'email': gym.owner_email,
                    }
                else:
                    return {
                        'username': username,
                        'message': 'Admin user already exists (password unchanged)',
                    }
        except Exception as e:
            print(f"[GymViewSet] Failed to create admin: {e}")
            return None

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

    @action(detail=False, methods=['post'], url_path='reset-demo')
    def reset_demo(self, request):
        """Reset demo gym data to exactly 120 members. Super Admin only."""
        from django.core.management import call_command
        from io import StringIO
        
        try:
            out = StringIO()
            call_command('create_demo_gym', '--reset', stdout=out)
            output = out.getvalue()
            return Response({
                'status': 'success',
                'message': 'Demo data reset to 120 members',
                'output': output
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

