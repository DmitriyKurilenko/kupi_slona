"""
Centralized authentication for django-ninja API endpoints.
django-ninja auth= accepts any callable that returns a truthy value or None.
"""


def auth(request):
    """
    Session-based authentication callable for django-ninja.

    Usage:
        from apps.core.auth import auth

        @router.get("/", auth=auth)
        def my_endpoint(request):
            # request.user is guaranteed to be authenticated
            pass
    """
    if request.user.is_authenticated:
        return request.user
    return None
