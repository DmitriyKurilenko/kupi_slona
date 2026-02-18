"""
URL patterns for payments app
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('return/', views.payment_return, name='payment_return'),
]
