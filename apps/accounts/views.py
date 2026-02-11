"""
Views for authentication pages
"""
import uuid

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.views import View


class LoginView(View):
    """Страница входа"""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/dashboard/')
        return render(request, self.template_name, {'page_title': 'Вход'})

    def post(self, request):
        email = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/dashboard/')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный email или пароль')
            return render(request, self.template_name, {'page_title': 'Вход'})


class RegisterView(View):
    """Страница регистрации"""
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/dashboard/')
        return render(request, self.template_name, {'page_title': 'Регистрация'})

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Валидация
        if password != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, self.template_name, {'page_title': 'Регистрация'})

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return render(request, self.template_name, {'page_title': 'Регистрация'})

        # Валидация пароля
        try:
            validate_password(password, user=User(email=email))
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, self.template_name, {'page_title': 'Регистрация'})

        # Генерируем username из email (Django User требует это поле)
        username = email.split('@')[0][:30]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{uuid.uuid4().hex[:6]}"

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        messages.success(request, 'Добро пожаловать!')
        return redirect('/dashboard/')


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('/')


# OAuth redirect views
def google_oauth_init(request):
    """Initiate Google OAuth flow"""
    return redirect(reverse('google_login'))
