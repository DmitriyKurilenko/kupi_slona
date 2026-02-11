"""
Ninja schemas for authentication
"""
from ninja import Schema


class RegisterSchema(Schema):
    """Схема регистрации"""
    email: str
    password: str


class LoginSchema(Schema):
    """Схема входа"""
    email: str
    password: str


class UserSchema(Schema):
    """Схема пользователя"""
    id: int
    username: str
    email: str


class MessageSchema(Schema):
    """Схема сообщения"""
    message: str
