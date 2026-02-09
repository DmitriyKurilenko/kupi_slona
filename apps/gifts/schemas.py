"""
Ninja schemas for gifts
"""
from ninja import Schema
from datetime import datetime
from typing import Optional
from pydantic import ConfigDict, field_serializer, field_validator
from uuid import UUID


class CreateGiftSchema(Schema):
    """Схема создания подарка"""
    elephant_id: int
    sender_name: Optional[str] = ""
    recipient_name: Optional[str] = ""
    message: Optional[str] = ""


class GiftLinkSchema(Schema):
    """Схема подарочной ссылки"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    sender_name: str
    recipient_name: str
    message: str
    is_claimed: bool
    created_at: datetime
    claimed_at: Optional[datetime]
    public_url: str
    elephant_color: str

    @field_validator('uuid', mode='before')
    @classmethod
    def validate_uuid(cls, value):
        """Конвертация UUID в строку перед валидацией"""
        if isinstance(value, UUID):
            return str(value)
        return value

    @staticmethod
    def resolve_public_url(obj):
        """URL подарка"""
        return obj.get_public_url()

    @staticmethod
    def resolve_elephant_color(obj):
        """Цвет слона"""
        return obj.elephant.color_hex if obj.elephant else None


class PublicGiftSchema(Schema):
    """Публичная схема подарка"""
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    sender_name: str
    recipient_name: str
    message: str
    is_claimed: bool
    claimed_by_username: Optional[str]
    elephant_color: str
    elephant_name: str
    elephant_image_url: str

    @field_validator('uuid', mode='before')
    @classmethod
    def validate_uuid(cls, value):
        """Конвертация UUID в строку перед валидацией"""
        if isinstance(value, UUID):
            return str(value)
        return value

    @staticmethod
    def resolve_sender_name(obj):
        """Имя отправителя (кастомное или username)"""
        return obj.sender_name if obj.sender_name else (obj.sender.username if obj.sender else "Аноним")

    @staticmethod
    def resolve_elephant_name(obj):
        """Имя слона"""
        return obj.elephant.get_name() if obj.elephant else None

    @staticmethod
    def resolve_claimed_by_username(obj):
        """Имя принявшего"""
        return obj.claimed_by.username if obj.claimed_by else None

    @staticmethod
    def resolve_elephant_color(obj):
        """Цвет слона"""
        return obj.elephant.color_hex if obj.elephant else None

    @staticmethod
    def resolve_elephant_image_url(obj):
        """URL изображения слона"""
        if obj.elephant and obj.elephant.image:
            return obj.elephant.image.url
        return None


class ClaimGiftResponseSchema(Schema):
    """Схема ответа на принятие подарка"""
    success: bool
    message: str
    elephant_id: Optional[int] = None
