"""
Business logic services for payments and orders
"""
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Tariff, Order
from apps.elephants.services import check_color_availability
from apps.elephants.utils import validate_hex_color


def get_active_tariffs():
    """
    Получить список активных тарифов

    Returns:
        QuerySet с активными тарифами
    """
    return Tariff.objects.filter(is_active=True)


def get_tariff_by_name(name: str) -> Tariff:
    """
    Получить тариф по имени

    Args:
        name: Название тарифа (basic/advanced)

    Returns:
        Tariff объект

    Raises:
        Tariff.DoesNotExist: Если тариф не найден
    """
    return Tariff.objects.get(name=name, is_active=True)


def validate_desired_color(color_hex: str, tariff: Tariff) -> bool:
    """
    Валидация желаемого цвета или оттенка

    Args:
        color_hex: Цвет в формате #RRGGBB или оттенок HUE:XXX
        tariff: Tariff объект

    Returns:
        True если цвет валиден

    Raises:
        ValidationError: Если цвет невалиден или недоступен
    """
    # Для basic тарифа цвет не нужен
    if tariff.name == Tariff.BASIC:
        if color_hex:
            raise ValidationError("Для базового тарифа нельзя выбирать цвет")
        return True

    # Для advanced тарифа цвет или оттенок обязателен
    if tariff.name == Tariff.ADVANCED:
        if not color_hex:
            raise ValidationError("Для продвинутого тарифа необходимо указать цвет или оттенок")

        # Проверка формата: либо HUE:XXX либо #RRGGBB
        if color_hex.startswith('HUE:'):
            # Формат HUE:XXX - проверяем что после HUE: идёт число от 0 до 360
            try:
                hue_value = int(color_hex.split(':')[1])
                if not (0 <= hue_value <= 360):
                    raise ValidationError("Оттенок должен быть в диапазоне 0-360")
            except (ValueError, IndexError):
                raise ValidationError("Формат оттенка должен быть HUE:XXX (например, HUE:180)")
        elif color_hex.startswith('#'):
            # Формат #RRGGBB - проверка HEX
            if not validate_hex_color(color_hex):
                raise ValidationError("Некорректный формат цвета. Используйте #RRGGBB")

            # Проверка доступности (только для точного цвета)
            color_hex_upper = color_hex.upper()
            if not check_color_availability(color_hex_upper):
                raise ValidationError(f"Цвет {color_hex_upper} уже занят. Выберите другой цвет.")
        else:
            raise ValidationError("Некорректный формат. Используйте #RRGGBB или HUE:XXX")

        return True

    return True


@transaction.atomic
def create_order(user, tariff_name: str, desired_color: str = None) -> Order:
    """
    Создание нового заказа

    Args:
        user: User объект
        tariff_name: Название тарифа (basic/advanced)
        desired_color: Желаемый цвет для advanced тарифа (опционально)

    Returns:
        Созданный Order объект

    Raises:
        Tariff.DoesNotExist: Если тариф не найден
        ValidationError: Если данные невалидны
    """
    # Получаем тариф
    tariff = get_tariff_by_name(tariff_name)

    # Нормализуем цвет
    if desired_color:
        desired_color = desired_color.upper()

    # Валидируем цвет
    validate_desired_color(desired_color, tariff)

    # Создаём заказ
    order = Order.objects.create(
        user=user,
        tariff=tariff,
        desired_color=desired_color
    )

    return order


@transaction.atomic
def process_payment(order_id: int) -> bool:
    """
    Обработка оплаты (заглушка)

    В реальном приложении здесь была бы интеграция с платёжной системой.
    Сейчас просто помечаем заказ как оплаченный.

    Args:
        order_id: ID заказа

    Returns:
        True если оплата успешна

    Raises:
        Order.DoesNotExist: Если заказ не найден
        ValueError: Если заказ уже оплачен
    """
    order = Order.objects.get(pk=order_id)

    if order.status != "pending":
        raise ValueError(f"Заказ #{order_id} не в статусе ожидания оплаты")

    # Помечаем как оплаченный
    order.mark_as_paid()

    return True


def get_user_orders(user):
    """
    Получить список заказов пользователя

    Args:
        user: User объект

    Returns:
        QuerySet с заказами пользователя
    """
    return Order.objects.filter(user=user).select_related('tariff')


def get_order_by_id(order_id: int, user=None) -> Order:
    """
    Получить заказ по ID с опциональной проверкой владельца

    Args:
        order_id: ID заказа
        user: User объект для проверки (опционально)

    Returns:
        Order объект

    Raises:
        Order.DoesNotExist: Если заказ не найден
        PermissionError: Если пользователь не владелец
    """
    order = Order.objects.select_related('tariff').get(pk=order_id)

    if user and order.user != user:
        raise PermissionError("Вы не являетесь владельцем этого заказа")

    return order
