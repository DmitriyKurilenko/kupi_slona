"""
Celery tasks for elephant image generation
"""
import logging
from celery import shared_task
from django.db import transaction

from apps.payments.models import Order, Tariff
from .services import create_elephant, check_color_availability
from .utils import generate_random_color, generate_color_from_hue

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_elephant_image(self, order_id: int):
    """
    Асинхронная генерация изображения слона

    Задача выполняется после оплаты заказа. Генерирует уникальный цвет
    (для basic тарифа) или использует выбранный цвет (для advanced),
    создаёт изображение и сохраняет объект Elephant.

    Args:
        order_id: ID заказа

    Returns:
        Dict с информацией о созданном слоне
    """
    try:
        logger.info(f"Starting elephant generation for order {order_id}")

        # Получаем заказ
        order = Order.objects.select_related('tariff', 'user').get(pk=order_id)

        # Проверка статуса заказа
        if not order.can_be_processed():
            logger.error(f"Order {order_id} is not in 'paid' status: {order.status}")
            return {
                'success': False,
                'error': f"Order is not paid"
            }

        # Обновляем статус на "processing"
        order.mark_as_processing()
        logger.info(f"Order {order_id} marked as processing")

        # Определяем цвет в зависимости от тарифа
        color_hex = None
        max_attempts = 10

        if order.tariff.name == Tariff.BASIC:
            # Для basic тарифа генерируем случайный цвет
            for attempt in range(max_attempts):
                color_hex = generate_random_color()

                # Проверяем уникальность
                if check_color_availability(color_hex):
                    logger.info(f"Generated unique color {color_hex} on attempt {attempt + 1}")
                    break
            else:
                # Не удалось найти уникальный цвет за max_attempts попыток
                logger.error(f"Failed to generate unique color after {max_attempts} attempts")
                order.mark_as_failed()
                return {
                    'success': False,
                    'error': 'Failed to generate unique color'
                }

        elif order.tariff.name == Tariff.ADVANCED:
            # Для advanced проверяем формат: оттенок или точный цвет
            desired = order.desired_color

            if desired and desired.startswith('HUE:'):
                # Формат "HUE:180" - генерируем цвет в заданном оттенке
                try:
                    hue = int(desired.split(':')[1])
                    logger.info(f"Generating color from hue {hue}")

                    # Пытаемся сгенерировать уникальный цвет в заданном оттенке
                    for attempt in range(max_attempts):
                        color_hex = generate_color_from_hue(hue)

                        # Проверяем уникальность
                        if check_color_availability(color_hex):
                            logger.info(f"Generated unique color {color_hex} from hue {hue} on attempt {attempt + 1}")
                            break
                    else:
                        # Не удалось найти уникальный цвет в этом оттенке
                        logger.error(f"Failed to generate unique color from hue {hue} after {max_attempts} attempts")
                        order.mark_as_failed()
                        return {
                            'success': False,
                            'error': f'Failed to generate unique color in hue {hue}'
                        }

                except (ValueError, IndexError) as e:
                    logger.error(f"Invalid hue format: {desired}")
                    order.mark_as_failed()
                    return {
                        'success': False,
                        'error': 'Invalid hue format'
                    }
            else:
                # Используем точный цвет (для обратной совместимости)
                color_hex = desired

                # Проверяем уникальность
                if not check_color_availability(color_hex):
                    logger.error(f"Desired color {color_hex} is not available")
                    order.mark_as_failed()
                    return {
                        'success': False,
                        'error': f'Color {color_hex} is already taken'
                    }

                logger.info(f"Using desired color {color_hex}")

        # Создаём слона (включая генерацию изображения)
        # Use select_for_update to lock the order row and prevent concurrent modifications
        with transaction.atomic():
            # Re-fetch order with lock to ensure no other task modifies it
            order = Order.objects.select_for_update().get(pk=order_id)

            elephant = create_elephant(order, color_hex)
            logger.info(f"Elephant created with ID {elephant.id}, color {color_hex}")

            # Обновляем статус заказа на "completed"
            order.mark_as_completed()
            logger.info(f"Order {order_id} completed successfully")

        return {
            'success': True,
            'elephant_id': elephant.id,
            'color_hex': elephant.color_hex,
            'order_id': order_id
        }

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return {
            'success': False,
            'error': 'Order not found'
        }

    except Exception as e:
        logger.exception(f"Error generating elephant for order {order_id}: {str(e)}")

        # Пытаемся отметить заказ как failed
        try:
            order = Order.objects.get(pk=order_id)
            order.mark_as_failed()
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found during cleanup")
        except Exception as cleanup_error:
            logger.error(f"Failed to mark order {order_id} as failed: {str(cleanup_error)}")

        # Retry с экспоненциальной задержкой
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
