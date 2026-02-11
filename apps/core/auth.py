"""
Centralized authentication utilities for django-ninja API endpoints
"""
from ninja.security import HttpAuthBase
from typing import Optional, Any
from django.http import HttpRequest


class SessionAuth(HttpAuthBase):
    """
    Session-based authentication for django-ninja.
    Checks Django session cookies instead of Bearer tokens.

    Usage:
        from apps.core.auth import auth

        @router.get("/", auth=auth)
        def my_endpoint(request):
            # request.user is guaranteed to be authenticated
            pass
    """
    def __call__(self, request: HttpRequest) -> Optional[Any]:
        if request.user.is_authenticated:
            return request.user
        return None


# Singleton instance to be imported across the project
auth = SessionAuth()
