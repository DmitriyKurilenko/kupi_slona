"""
Views for elephant pages
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(TemplateView):
    """Лендинг страница"""
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Elephant Color Shop - Купи уникального цветного слона!'
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """Личный кабинет"""
    template_name = 'dashboard.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Мои слоны - Dashboard'
        return context


def custom_403(request, exception=None):
    """Custom 403 forbidden error page"""
    return render(request, '403.html', status=403)


def custom_404(request, exception=None):
    """Custom 404 error page"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 error page"""
    return render(request, '500.html', status=500)
