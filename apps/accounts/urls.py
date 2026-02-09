"""
URL patterns for accounts app
"""
from django.urls import path
from .views import LoginView, RegisterView, logout_view, google_oauth_init, apple_oauth_init

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', logout_view, name='logout'),
    path('oauth/google/', google_oauth_init, name='oauth_google'),
    path('oauth/apple/', apple_oauth_init, name='oauth_apple'),
]
