"""
Custom permission classes for Gym Management System.
"""

from rest_framework import permissions


class IsAdminOrStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to:
    - Allow ADMIN and STAFF to modify data
    - Allow others (MEMBER) read-only access
    """

    def has_permission(self, request, view):
        # Authenticated users only
        if not request.user.is_authenticated:
            return False
            
        # Admin and Staff have full access
        if request.user.is_admin or request.user.is_staff_member:
            return True
            
        # Members have read-only access (GET, HEAD, OPTIONS)
        return request.method in permissions.SAFE_METHODS


class MemberAccessPolicy(permissions.BasePermission):
    """
    Detailed access policy for Members:
    - Admin: Full access
    - Staff: List, Create, Retrieve, Update (cannot delete usually)
    - Member: Retrieve OWN profile only
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.is_admin:
            return True
        
        # Staff can view and edit any member
        if request.user.is_staff_member:
            # Staff typically cannot delete members (business rule)
            if request.method == 'DELETE':
                return False
            return True
            
        # Member can only view their own profile
        if request.user.is_gym_member:
            # Ensure the object being accessed belongs to the request user
            return obj.user == request.user and request.method in permissions.SAFE_METHODS
            
        return False
