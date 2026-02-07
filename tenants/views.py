"""
API endpoints for tenant (gym) management.
Super Admin can list, approve, and suspend gyms.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from tenants.models import Gym, Domain
from .serializers import GymSerializer


class GymViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing gym tenants.
    Only superadmins can access this.
    """
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a pending gym application."""
        gym = self.get_object()
        if gym.status == Gym.Status.PENDING:
            gym.status = Gym.Status.APPROVED
            gym.approved_at = timezone.now()
            gym.save()
            return Response({'status': 'approved', 'gym': GymSerializer(gym).data})
        return Response(
            {'error': f'Cannot approve gym with status: {gym.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

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
        """Get stats for a specific gym tenant."""
        gym = self.get_object()
        # TODO: Query the tenant schema for member count, etc.
        return Response({
            'gym_id': gym.id,
            'name': gym.name,
            'schema': gym.schema_name,
            'status': gym.status,
            'stats': {
                'members': 0,  # Would need to query tenant schema
                'staff': 0,
                'revenue': 0,
            }
        })
