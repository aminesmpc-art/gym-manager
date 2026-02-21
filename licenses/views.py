"""
License management API views.
- Super admin: CRUD + generate/revoke/renew/unbind
- Local app: verify endpoint (no auth required)

Security:
- All verify responses are signed with HMAC-SHA256 (X-Response-Signature header)
- The local app verifies this signature to prevent fake server attacks (MITM)
"""

import hmac
import hashlib
import json

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from .models import License
from .serializers import LicenseSerializer, GenerateLicenseSerializer, VerifyLicenseSerializer

# Must match the secret in the Flutter app's SecurityService
HMAC_SECRET = 'MOL-GYM-HMAC-K3Y-2026-s3cur3-!@#'


def signed_response(data, http_status=200):
    """
    Create an HTTP response with HMAC-SHA256 signature.
    Uses raw HttpResponse so the body is EXACTLY what we sign.
    The Flutter app verifies this signature to prevent fake servers.
    """
    body = json.dumps(data)
    signature = hmac.new(
        HMAC_SECRET.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    response = HttpResponse(body, content_type='application/json', status=http_status)
    response['X-Response-Signature'] = signature
    return response


class LicenseViewSet(viewsets.ModelViewSet):
    """
    Super Admin license management.
    
    list:    GET    /api/licenses/
    create:  POST   /api/licenses/         (use generate/ instead)
    detail:  GET    /api/licenses/{id}/
    update:  PUT    /api/licenses/{id}/
    delete:  DELETE /api/licenses/{id}/
    """
    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new license key.
        POST /api/licenses/generate/
        """
        serializer = GenerateLicenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        license = License.objects.create(
            tier=data['tier'],
            gym_name=data['gym_name'],
            owner_name=data.get('owner_name', ''),
            owner_email=data.get('owner_email', ''),
            owner_phone=data.get('owner_phone', ''),
            max_members=data.get('max_members', 500),
            notes=data.get('notes', ''),
        )

        return Response(
            LicenseSerializer(license).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """
        Revoke a license.
        POST /api/licenses/{id}/revoke/
        """
        license = self.get_object()
        license.status = License.Status.REVOKED
        license.save()
        return Response(LicenseSerializer(license).data)

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """
        Reactivate a revoked/expired license.
        POST /api/licenses/{id}/reactivate/
        """
        license = self.get_object()
        license.status = License.Status.ACTIVE
        
        # If expired, extend by original tier duration
        if license.expires_at and license.expires_at < timezone.now():
            license.renew(license.tier)
        else:
            license.save()
        
        return Response(LicenseSerializer(license).data)

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """
        Renew/extend a license with a new tier.
        POST /api/licenses/{id}/renew/
        Body: {"tier": "yearly"}
        """
        license = self.get_object()
        new_tier = request.data.get('tier', license.tier)
        license.renew(new_tier)
        return Response(LicenseSerializer(license).data)

    @action(detail=True, methods=['post'])
    def unbind(self, request, pk=None):
        """
        Unbind a license from its device (allow re-activation on another device).
        POST /api/licenses/{id}/unbind/
        """
        license = self.get_object()
        license.device_id = None
        license.save()
        return Response(LicenseSerializer(license).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        License dashboard statistics.
        GET /api/licenses/stats/
        """
        now = timezone.now()
        total = License.objects.count()
        active = License.objects.filter(status='active').count()
        expired = License.objects.filter(status='expired').count()
        revoked = License.objects.filter(status='revoked').count()
        
        # Count by tier
        tier_counts = License.objects.values('tier').annotate(count=Count('id'))
        tiers = {item['tier']: item['count'] for item in tier_counts}

        # Expiring soon (within 7 days)
        expiring_soon = License.objects.filter(
            status='active',
            expires_at__isnull=False,
            expires_at__lte=now + timezone.timedelta(days=7),
            expires_at__gt=now,
        ).count()

        return Response({
            'total': total,
            'active': active,
            'expired': expired,
            'revoked': revoked,
            'expiring_soon': expiring_soon,
            'tiers': tiers,
        })


class VerifyLicenseView(APIView):
    """
    Public endpoint for local app to verify a license key.
    No authentication required — the license key IS the auth.
    
    POST /api/licenses/verify/
    Body: {"license_key": "MOL-XXXX-XXXX-XXXX", "device_id": "optional-device-id"}
    
    Returns:
    - valid: true/false
    - tier, expires, gym_name, max_members (if valid)
    - message (always)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyLicenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        license_key = serializer.validated_data['license_key']
        device_id = serializer.validated_data.get('device_id', '')

        try:
            license = License.objects.get(license_key=license_key)
        except License.DoesNotExist:
            return signed_response({
                'valid': False,
                'message': 'Invalid license key.',
            })

        # Check if revoked
        if license.status == License.Status.REVOKED:
            return signed_response({
                'valid': False,
                'message': 'This license has been revoked. Contact support.',
            })

        # Check if expired
        if license.expires_at and license.expires_at < timezone.now():
            # Auto-update status
            if license.status != License.Status.EXPIRED:
                license.status = License.Status.EXPIRED
                license.save()
            return signed_response({
                'valid': False,
                'message': f'License expired on {license.expires_at.strftime("%Y-%m-%d")}.',
            })

        # Device binding check
        if device_id:
            if license.device_id and license.device_id != device_id:
                return signed_response({
                    'valid': False,
                    'message': 'This license is already activated on another device.',
                })
            # Bind to device on first verification
            if not license.device_id:
                license.device_id = device_id

        # Update last verified timestamp
        license.last_verified_at = timezone.now()
        license.save()

        return signed_response({
            'valid': True,
            'message': 'License valid.',
            'tier': license.tier,
            'expires': license.expires_at.strftime('%Y-%m-%d') if license.expires_at else None,
            'gym_name': license.gym_name,
            'max_members': license.max_members,
        })
