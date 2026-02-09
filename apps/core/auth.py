"""
Centralized authentication utilities for django-ninja API endpoints
"""
from ninja.security import HttpBearer
from typing import Optional
from django.contrib.auth.models import User


class AuthBearer(HttpBearer):
    """
    Authentication bearer for django-ninja
    Replaces manual is_authenticated checks across 11+ endpoints

    Usage:
        from apps.core.auth import auth

        @router.get("/", auth=auth)
        def my_endpoint(request):
            # request.user is guaranteed to be authenticated
            pass
    """
    def authenticate(self, request, token: Optional[str] = None) -> Optional[User]:
        """
        Authenticate request based on session

        Args:
            request: Django HttpRequest
            token: Optional bearer token (not used for session auth)

        Returns:
            User object if authenticated, None otherwise
        """
        if request.user.is_authenticated:
            return request.user
        return None


# Singleton instance to be imported across the project
auth = AuthBearer()
