"""
Views for authentication pages
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
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
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/dashboard/')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
            return render(request, self.template_name, {'page_title': 'Вход'})


class RegisterView(View):
    """Страница регистрации"""
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/dashboard/')
        return render(request, self.template_name, {'page_title': 'Регистрация'})

    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Валидация
        if password != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, self.template_name, {'page_title': 'Регистрация'})

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует')
            return render(request, self.template_name, {'page_title': 'Регистрация'})

        # Создание пользователя
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, 'Добро пожаловать!')
        return redirect('/dashboard/')


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('/')


# OAuth redirect views
from django.urls import reverse


def google_oauth_init(request):
    """Initiate Google OAuth flow"""
    return redirect(reverse('google_login'))


def apple_oauth_init(request):
    """Initiate Apple OAuth flow"""
    return redirect(reverse('apple_login'))
