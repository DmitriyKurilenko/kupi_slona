"""
Signals for accounts app
"""
import logging

from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.models import Site
from allauth.account.signals import user_signed_up

logger = logging.getLogger('apps')


@receiver(user_signed_up)
def send_welcome_email(request, user, **kwargs):
    """Send welcome email after registration"""
    if not user.email:
        return

    try:
        current_site = Site.objects.get_current()
        context = {
            'user': user,
            'current_site': current_site,
            'dashboard_url': f'https://{current_site.domain}/dashboard/',
        }

        html_message = render_to_string('account/email/welcome_message.html', context)
        plain_message = render_to_string('account/email/welcome_message.txt', context)

        send_mail(
            subject='Добро пожаловать — Купи слона',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
