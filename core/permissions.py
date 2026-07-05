"""
Reusable authorization primitives for the core app.

Role model: User.role is "admin" or "employee" (core.models.User.ROLE_CHOICES).
Django superusers are treated as admins so `createsuperuser` accounts work
regardless of their `role` value.

Usage:
    permission_classes = [IsAdmin]                      # admin-only endpoint
    permission_classes = [IsAdminOrReadOnly]            # anyone authed reads, admin writes
    permission_classes = [IsOwnerOrAdmin]               # object-level ownership
    permission_classes = [IsAuthenticated]              # re-exported from DRF for one import site
"""
from django.contrib.auth import get_user_model
from rest_framework.permissions import (  # noqa: F401  (IsAuthenticated re-exported)
    SAFE_METHODS,
    BasePermission,
    IsAuthenticated,
)

ADMIN_ROLE = "admin"


def user_is_admin(user) -> bool:
    """Single source of truth for 'is this user an admin?'."""
    return bool(
        user
        and user.is_authenticated
        and (getattr(user, "role", None) == ADMIN_ROLE or user.is_superuser)
    )


class IsAdmin(BasePermission):
    """Allow only authenticated admins."""

    message = "Administrator access required."

    def has_permission(self, request, view):
        return user_is_admin(request.user)


class IsAdminOrReadOnly(BasePermission):
    """
    Authenticated users get read access (GET/HEAD/OPTIONS);
    write access requires admin.
    """

    message = "Administrator access required for this action."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.method in SAFE_METHODS or user_is_admin(request.user)


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: admins always pass; otherwise the requester
    must own the object.

    Ownership resolution:
      - User instances: the requester is the user themselves.
      - Objects with an `employee` FK (Appointment, ClientProfile,
        Notifications): the requester is the assigned employee.
      - Anything else: denied.
    """

    message = "You may only act on your own records."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if user_is_admin(request.user):
            return True
        if isinstance(obj, get_user_model()):
            return obj == request.user
        owner = getattr(obj, "employee", None)
        return owner is not None and owner == request.user
