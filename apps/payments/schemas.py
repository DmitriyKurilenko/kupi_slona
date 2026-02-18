"""
Ninja schemas for payments
"""
from ninja import Schema
from datetime import datetime
from typing import Optional
from decimal import Decimal


class TariffSchema(Schema):
    """Схема тарифа"""
    id: int
    name: str
    price: Decimal
    description: str
    is_active: bool


class CreateOrderSchema(Schema):
    """Схема создания заказа"""
    tariff_name: str
    desired_color: Optional[str] = None


class OrderSchema(Schema):
    """Схема заказа"""
    model_config = {"from_attributes": True}

    id: int
    status: str
    desired_color: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]
    tariff: TariffSchema


class PaymentInitSchema(Schema):
    """Response after payment initiation (redirect to YooKassa)"""
    order_id: int
    payment_url: str


class PaymentResponseSchema(Schema):
    """Схема ответа на оплату"""
    success: bool
    message: str
    order_id: int
