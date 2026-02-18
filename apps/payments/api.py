"""
API endpoints for payments and orders
"""
import logging

from ninja import Router
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from .models import Tariff, Order
from .services import get_active_tariffs, create_order, get_user_orders, get_order_by_id
from .schemas import TariffSchema, CreateOrderSchema, OrderSchema, PaymentInitSchema, PaymentResponseSchema
from .yookassa_service import create_yookassa_payment, process_yookassa_webhook
from apps.accounts.schemas import MessageSchema
from apps.core.auth import auth

logger = logging.getLogger('apps')

router = Router()


@router.get("/tariffs", response=list[TariffSchema])
def list_tariffs(request):
    """Список активных тарифов"""
    tariffs = get_active_tariffs()
    return list(tariffs)


@router.post("/orders", response={201: PaymentInitSchema, 400: MessageSchema, 401: MessageSchema}, auth=auth)
def create_new_order(request, payload: CreateOrderSchema):
    """Создать заказ и инициировать оплату через YooKassa"""
    try:
        order = create_order(
            user=request.user,
            tariff_name=payload.tariff_name,
            desired_color=payload.desired_color
        )

        payment_url = create_yookassa_payment(order)

        return 201, {
            "order_id": order.id,
            "payment_url": payment_url
        }

    except Tariff.DoesNotExist:
        return 400, {"message": "Тариф не найден"}
    except ValidationError as e:
        return 400, {"message": str(e)}
    except Exception as e:
        logger.error(f"Order creation error: {e}")
        return 400, {"message": str(e)}


@router.post("/orders/{order_id}/pay", response={200: PaymentInitSchema, 400: MessageSchema, 401: MessageSchema, 403: MessageSchema, 404: MessageSchema}, auth=auth)
def pay_order(request, order_id: int):
    """Повторная инициация оплаты для pending заказа"""
    try:
        order = get_order_by_id(order_id, request.user)

        if order.status != 'pending':
            return 400, {"message": "Заказ уже обработан"}

        payment_url = create_yookassa_payment(order)

        return 200, {
            "order_id": order.id,
            "payment_url": payment_url
        }

    except Order.DoesNotExist:
        return 404, {"message": "Заказ не найден"}
    except PermissionError:
        return 403, {"message": "Доступ запрещён"}
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        return 400, {"message": str(e)}


@router.post("/payments/webhook", response={200: dict})
def yookassa_webhook(request: HttpRequest):
    """Webhook endpoint for YooKassa payment notifications (no auth)"""
    try:
        process_yookassa_webhook(request.body)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
    # Always return 200 to prevent YooKassa from retrying
    return 200, {"status": "ok"}


@router.get("/orders", response={200: list[OrderSchema], 401: MessageSchema}, auth=auth)
def list_orders(request):
    """Список заказов пользователя"""
    orders = get_user_orders(request.user)
    return 200, list(orders)


@router.get("/orders/{order_id}", response={200: OrderSchema, 401: MessageSchema, 403: MessageSchema, 404: MessageSchema}, auth=auth)
def get_order(request, order_id: int):
    """Получить заказ по ID"""
    try:
        order = get_order_by_id(order_id, request.user)
        return 200, order
    except Order.DoesNotExist:
        return 404, {"message": "Заказ не найден"}
    except PermissionError:
        return 403, {"message": "Доступ запрещён"}
