"""
URL patterns for core app (static/legal pages)
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('contacts/', views.ContactsView.as_view(), name='contacts'),
]
