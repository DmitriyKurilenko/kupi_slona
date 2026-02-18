"""
URL configuration for elephant_shop project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI
from apps.core import views as core_views

# Initialize Django Ninja API
api = NinjaAPI(
    title="Elephant Color Shop API",
    version="1.0.0",
    description="API для покупки уникальных цветных слонов",
)

# Import API routers
from apps.accounts.api import router as accounts_router
from apps.elephants.api import router as elephants_router
from apps.payments.api import router as payments_router
from apps.gifts.api import router as gifts_router

# Register API routers
api.add_router("/auth/", accounts_router)
api.add_router("/elephants/", elephants_router)
api.add_router("/", payments_router)
api.add_router("/gifts/", gifts_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    # Health check endpoint
    path('health/', core_views.health_check, name='health_check'),
    # Allauth URLs (must come BEFORE custom accounts URLs)
    path('accounts/', include('allauth.urls')),
    # Django views
    path('', include('apps.elephants.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('gift/', include('apps.gifts.urls')),
    path('payment/', include('apps.payments.urls')),
    path('', include('apps.core.urls')),
]

# Custom error handlers
handler403 = 'apps.elephants.views.custom_403'
handler404 = 'apps.elephants.views.custom_404'
handler500 = 'apps.elephants.views.custom_500'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
