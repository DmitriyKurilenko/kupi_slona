"""
API endpoints for payments and orders
"""
from ninja import Router
from django.core.exceptions import ValidationError

from .models import Tariff, Order
from .services import get_active_tariffs, create_order, process_payment, get_user_orders, get_order_by_id
from .schemas import TariffSchema, CreateOrderSchema, OrderSchema, PaymentResponseSchema
from apps.accounts.schemas import MessageSchema
from apps.elephants.tasks import generate_elephant_image
from apps.core.auth import auth

router = Router()


@router.get("/tariffs", response=list[TariffSchema])
def list_tariffs(request):
    """Список активных тарифов"""
    tariffs = get_active_tariffs()
    return list(tariffs)


@router.post("/orders", response={201: OrderSchema, 400: MessageSchema, 401: MessageSchema}, auth=auth)
def create_new_order(request, payload: CreateOrderSchema):
    """Создать новый заказ и сразу запустить генерацию (автоматическая оплата)"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    try:
        # Создаём заказ
        order = create_order(
            user=request.user,
            tariff_name=payload.tariff_name,
            desired_color=payload.desired_color
        )

        # Автоматически оплачиваем (т.к. нет платежной системы)
        process_payment(order.id)

        # Запускаем генерацию слона
        generate_elephant_image.delay(order.id)

        return 201, order

    except Tariff.DoesNotExist:
        return 400, {"message": "Тариф не найден"}
    except ValidationError as e:
        return 400, {"message": str(e)}
    except Exception as e:
        return 400, {"message": str(e)}


@router.post("/orders/{order_id}/pay", response={200: PaymentResponseSchema, 400: MessageSchema, 401: MessageSchema, 403: MessageSchema, 404: MessageSchema}, auth=auth)
def pay_order(request, order_id: int):
    """Оплатить заказ и запустить генерацию слона"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    try:
        # Получаем заказ с проверкой владельца
        order = get_order_by_id(order_id, request.user)

        # Обрабатываем оплату (заглушка)
        process_payment(order_id)

        # Запускаем асинхронную задачу генерации слона
        task = generate_elephant_image.delay(order_id)

        return 200, {
            "success": True,
            "message": "Оплата принята. Генерация слона началась.",
            "order_id": order_id
        }

    except Order.DoesNotExist:
        return 404, {"message": "Заказ не найден"}
    except PermissionError:
        return 403, {"message": "Доступ запрещён"}
    except ValueError as e:
        return 400, {"message": str(e)}
    except Exception as e:
        return 400, {"message": str(e)}


@router.get("/orders", response={200: list[OrderSchema], 401: MessageSchema}, auth=auth)
def list_orders(request):
    """Список заказов пользователя"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    orders = get_user_orders(request.user)
    return 200, list(orders)


@router.get("/orders/{order_id}", response={200: OrderSchema, 401: MessageSchema, 403: MessageSchema, 404: MessageSchema}, auth=auth)
def get_order(request, order_id: int):
    """Получить заказ по ID"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    try:
        order = get_order_by_id(order_id, request.user)
        return 200, order
    except Order.DoesNotExist:
        return 404, {"message": "Заказ не найден"}
    except PermissionError:
        return 403, {"message": "Доступ запрещён"}
