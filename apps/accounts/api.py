"""
API endpoints for authentication
"""
import uuid

from ninja import Router
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

from .schemas import RegisterSchema, LoginSchema, UserSchema, MessageSchema
from apps.core.auth import auth

router = Router()


@router.post("/register", response={201: UserSchema, 400: MessageSchema})
def register(request, payload: RegisterSchema):
    """Регистрация нового пользователя"""
    try:
        # Validate password strength using Django's built-in validators
        try:
            validate_password(payload.password)
        except DjangoValidationError as e:
            return 400, {"message": " ".join(e.messages)}

        if User.objects.filter(email=payload.email).exists():
            return 400, {"message": "Пользователь с таким email уже существует"}

        # Генерируем username из email
        username = payload.email.split('@')[0][:30]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{uuid.uuid4().hex[:6]}"

        user = User.objects.create_user(
            username=username,
            email=payload.email,
            password=payload.password
        )

        # Автоматически входим
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return 201, user

    except IntegrityError:
        return 400, {"message": "Пользователь с таким email уже существует"}
    except Exception as e:
        return 400, {"message": str(e)}


@router.post("/login", response={200: UserSchema, 401: MessageSchema})
def login_user(request, payload: LoginSchema):
    """Вход пользователя"""
    user = authenticate(
        request,
        username=payload.email,
        password=payload.password
    )

    if user is not None:
        login(request, user)
        return 200, user
    else:
        return 401, {"message": "Неверный email или пароль"}


@router.post("/logout", response=MessageSchema)
def logout_user(request):
    """Выход пользователя"""
    logout(request)
    return {"message": "Вы успешно вышли из системы"}


@router.get("/me", response={200: UserSchema, 401: MessageSchema})
def get_current_user(request):
    """Получить текущего пользователя"""
    if request.user.is_authenticated:
        return 200, request.user
    else:
        return 401, {"message": "Пользователь не авторизован"}


@router.get("/connections", response={200: list, 401: MessageSchema}, auth=auth)
def get_social_connections(request):
    """Get user's connected social accounts"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    from allauth.socialaccount.models import SocialAccount

    connections = []
    for account in SocialAccount.objects.filter(user=request.user):
        connections.append({
            "provider": account.provider,
            "uid": account.uid,
            "email": account.extra_data.get('email', ''),
        })

    return 200, connections


@router.post("/disconnect/{provider}", response={200: MessageSchema, 400: MessageSchema}, auth=auth)
def disconnect_social_account(request, provider: str):
    """Disconnect social account"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    from allauth.socialaccount.models import SocialAccount

    try:
        account = SocialAccount.objects.get(user=request.user, provider=provider)

        # Don't allow disconnect if it's the only auth method
        if not request.user.has_usable_password():
            other_accounts = SocialAccount.objects.filter(user=request.user).exclude(id=account.id)
            if not other_accounts.exists():
                return 400, {"message": "Cannot disconnect the only auth method"}

        account.delete()
        return 200, {"message": f"Disconnected {provider}"}
    except SocialAccount.DoesNotExist:
        return 400, {"message": f"{provider} not connected"}
