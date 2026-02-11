"""
Centralized authentication for django-ninja API endpoints.
Uses HttpBearer as base (available in ninja.security) but overrides
__call__ to check Django session instead of Bearer token header.
"""
from ninja.security import HttpBearer


class SessionAuth(HttpBearer):
    """
    Session-based authentication for django-ninja.
    Overrides HttpBearer.__call__ to skip bearer token check
    and use Django session cookies instead.
    """
    def __call__(self, request):
        # Skip HttpBearer's Authorization header check,
        # go straight to session-based authentication
        return self.authenticate(request, None)

    def authenticate(self, request, token):
        if request.user.is_authenticated:
            return request.user
        return None


auth = SessionAuth()
