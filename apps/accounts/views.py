"""
Views for authentication pages
"""
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
        import sys
        import traceback

        try:
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

            # Валидация пароля
            try:
                validate_password(password, user=User(username=username, email=email))
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return render(request, self.template_name, {'page_title': 'Регистрация'})

            # Создание пользователя
            print(f"DEBUG: Creating user {username} with email {email}", file=sys.stderr, flush=True)
            user = User.objects.create_user(username=username, email=email, password=password)
            print(f"DEBUG: User created successfully: {user.id}", file=sys.stderr, flush=True)

            print(f"DEBUG: Attempting login for user {user.username}", file=sys.stderr, flush=True)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            print(f"DEBUG: Login successful", file=sys.stderr, flush=True)

            messages.success(request, 'Добро пожаловать!')
            return redirect('/dashboard/')

        except Exception as e:
            print(f"REGISTRATION ERROR: {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
            print(f"FULL TRACEBACK:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
            messages.error(request, f'Ошибка регистрации: {str(e)}')
            return render(request, self.template_name, {'page_title': 'Регистрация'})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('/')


# OAuth redirect views
def google_oauth_init(request):
    """Initiate Google OAuth flow"""
    return redirect(reverse('google_login'))


def apple_oauth_init(request):
    """Initiate Apple OAuth flow"""
    return redirect(reverse('apple_login'))
