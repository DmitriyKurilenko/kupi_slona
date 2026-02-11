"""
Core views for health checks, monitoring, and static pages
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.views.generic import TemplateView


def health_check(request):
    """
    Health check endpoint for Docker healthchecks and load balancers
    Returns JSON with status of database and cache connections
    """
    status = {
        'status': 'healthy',
        'database': 'unknown',
        'cache': 'unknown',
    }
    http_status = 200

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        status['database'] = 'ok'
    except Exception as e:
        status['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
        http_status = 503

    # Check Redis cache connection
    try:
        cache.set('health_check_key', 'ok', 10)
        cache_value = cache.get('health_check_key')
        if cache_value == 'ok':
            status['cache'] = 'ok'
        else:
            status['cache'] = 'error: value mismatch'
            status['status'] = 'unhealthy'
            http_status = 503
    except Exception as e:
        status['cache'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
        http_status = 503

    return JsonResponse(status, status=http_status)


class TermsView(TemplateView):
    template_name = 'legal/terms.html'


class PrivacyView(TemplateView):
    template_name = 'legal/privacy.html'


class ContactsView(TemplateView):
    template_name = 'legal/contacts.html'


class CheckElephantView(TemplateView):
    template_name = 'check.html'
