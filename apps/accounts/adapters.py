"""
Custom adapters for django-allauth
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    """Customize account adapter"""

    def get_login_redirect_url(self, request):
        """Redirect to dashboard after login"""
        next_url = request.GET.get('next')
        if next_url:
            return next_url
        return settings.LOGIN_REDIRECT_URL


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Customize social account adapter for OAuth"""

    def pre_social_login(self, request, sociallogin):
        """
        Connect social account to existing user if email matches
        """
        # User already logged in - connect account
        if request.user.is_authenticated:
            sociallogin.connect(request, request.user)
            return

        # Check if email matches existing user
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def populate_user(self, request, sociallogin, data):
        """Populate user with data from provider"""
        user = super().populate_user(request, sociallogin, data)
        if not user.first_name:
            user.first_name = data.get('first_name', '')
        if not user.last_name:
            user.last_name = data.get('last_name', '')
        return user
