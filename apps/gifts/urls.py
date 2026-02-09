"""
URL patterns for gifts app
"""
from django.urls import path
from .views import PublicGiftView

urlpatterns = [
    path('<uuid:uuid>/', PublicGiftView.as_view(), name='gift-page'),
]
