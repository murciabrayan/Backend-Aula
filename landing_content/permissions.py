from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRoleOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", "") == "ADMIN" or user.is_staff or user.is_superuser)
        )

