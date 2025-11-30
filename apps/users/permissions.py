from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission class for Admin users"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsProvider(permissions.BasePermission):
    """Permission class for Provider users"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_provider


class IsRegularUser(permissions.BasePermission):
    """Permission class for regular users"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_regular_user


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission class allowing owners or admins to access/modify objects"""

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True

        # Check if the object has a 'user' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # If the object is a User instance
        if hasattr(obj, 'email'):
            return obj == request.user

        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return obj == request.user


class IsAdminOrProvider(permissions.BasePermission):
    """Permission class for Admin or Provider users"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.is_provider
        )


class CanCreateAssistanceRequest(permissions.BasePermission):
    """Permission to check if user can create assistance request"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Only regular users can create assistance requests
        if request.method == 'POST':
            return request.user.is_regular_user or request.user.is_admin

        return True


class CanAccessProviderData(permissions.BasePermission):
    """Permission for accessing provider-specific data"""

    def has_permission(self, request, view):
        # Allow unauthenticated users to view (GET) provider data
        if request.method in permissions.SAFE_METHODS:
            return True

        # For modifications, authentication is required
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can access all provider data
        if request.user.is_admin:
            return True

        # Providers can only access their own data
        if request.user.is_provider:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Admins can access/modify any provider
        if request.user.is_admin:
            return True

        # Providers can only access/modify their own profile
        if request.user.is_provider:
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return False

        # Regular users can only view
        if request.method in permissions.SAFE_METHODS:
            return True

        return False
