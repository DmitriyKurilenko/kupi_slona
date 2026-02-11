"""
Ninja schemas for elephants
"""
from ninja import Schema
from datetime import datetime
from typing import Optional
from pydantic import ConfigDict


class ElephantListSchema(Schema):
    """Схема слона для списка"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color_hex: str
    color_r: int
    color_g: int
    color_b: int
    image: Optional[str] = None
    image_url: Optional[str] = None
    color_display: str
    is_gifted: bool
    is_owned_by_user: bool
    gift_recipient: Optional[str] = None
    gift_date: Optional[datetime] = None
    gift_uuid: Optional[str] = None
    created_at: datetime

    @staticmethod
    def resolve_name(obj):
        """Уникальное имя слона на основе цвета"""
        return obj.get_name()

    @staticmethod
    def resolve_image(obj):
        """Получить путь к изображению"""
        return obj.image.name if obj.image else None

    @staticmethod
    def resolve_image_url(obj):
        """Получить URL изображения"""
        return obj.image.url if obj.image else None

    @staticmethod
    def resolve_color_display(obj):
        """Строковое представление цвета"""
        return obj.get_color_display()

    @staticmethod
    def resolve_gift_recipient(obj):
        """Получатель подарка"""
        if obj.is_gifted and hasattr(obj, 'gift_link'):
            return obj.gift_link.get_recipient_display()
        return None

    @staticmethod
    def resolve_gift_date(obj):
        """Дата создания подарка"""
        if obj.is_gifted and hasattr(obj, 'gift_link'):
            return obj.gift_link.created_at
        return None

    @staticmethod
    def resolve_gift_uuid(obj):
        """UUID подарочной ссылки"""
        if obj.is_gifted and hasattr(obj, 'gift_link'):
            return str(obj.gift_link.uuid)
        return None


class ElephantDetailSchema(Schema):
    """Детальная схема слона"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color_hex: str
    color_r: int
    color_g: int
    color_b: int
    color_display: str
    image_url: str
    is_gifted: bool
    created_at: datetime
    order_id: int

    @staticmethod
    def resolve_name(obj):
        """Уникальное имя слона на основе цвета"""
        return obj.get_name()

    @staticmethod
    def resolve_color_display(obj):
        """Строковое представление цвета"""
        return obj.get_color_display()

    @staticmethod
    def resolve_image_url(obj):
        """Получить URL изображения"""
        if obj.image:
            return obj.image.url
        return None

    @staticmethod
    def resolve_order_id(obj):
        """ID заказа"""
        return obj.order.id if obj.order else None
