"""
Centralized authentication for django-ninja API endpoints.
Uses django-ninja's built-in django_auth for session-based authentication.
https://django-ninja.dev/guides/authentication/#django-session-auth
"""
from ninja.security import django_auth

auth = django_auth
