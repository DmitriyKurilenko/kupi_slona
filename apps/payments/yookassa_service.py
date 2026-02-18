"""
YooKassa payment integration service
"""
import json
import logging
import uuid

from django.conf import settings
from django.db import transaction
from yookassa import Configuration, Payment

from .models import Order
from apps.elephants.tasks import generate_elephant_image

logger = logging.getLogger('apps')


def _configure_yookassa():
    """Configure YooKassa SDK with shop credentials"""
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def create_yookassa_payment(order: Order) -> str:
    """
    Create YooKassa payment for an order.

    Args:
        order: Order instance (must be in 'pending' status)

    Returns:
        confirmation_url for redirect to YooKassa payment page

    Raises:
        ValueError: If order is not in pending status
        Exception: If YooKassa API call fails
    """
    if order.status != 'pending':
        raise ValueError(f"Order #{order.id} is not in pending status")

    _configure_yookassa()

    # Use uuid5 based on order ID for idempotency
    idempotency_key = str(uuid.uuid5(uuid.NAMESPACE_URL, f"order-{order.id}"))

    tariff_display = order.tariff.get_name_display()

    payment = Payment.create({
        "amount": {
            "value": str(order.tariff.price),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"{settings.YOOKASSA_RETURN_URL}?order_id={order.id}"
        },
        "capture": True,
        "description": f"Слон — тариф «{tariff_display}»",
        "metadata": {
            "order_id": order.id
        }
    }, idempotency_key)

    # Save YooKassa payment ID to order
    order.yookassa_payment_id = payment.id
    order.save(update_fields=['yookassa_payment_id'])

    logger.info(f"YooKassa payment {payment.id} created for order #{order.id}")

    return payment.confirmation.confirmation_url


def process_yookassa_webhook(body: bytes) -> bool:
    """
    Process YooKassa webhook notification.
    Idempotent — safe to call multiple times for the same event.

    Args:
        body: Raw request body bytes

    Returns:
        True if processed successfully
    """
    data = json.loads(body)
    event_type = data.get('event')
    payment_data = data.get('object', {})
    payment_id = payment_data.get('id')

    if not payment_id:
        logger.warning("Webhook without payment ID")
        return False

    logger.info(f"YooKassa webhook: {event_type} for payment {payment_id}")

    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(
                yookassa_payment_id=payment_id
            )
        except Order.DoesNotExist:
            logger.error(f"Order not found for payment {payment_id}")
            return False

        if event_type == 'payment.succeeded':
            if order.status in ('paid', 'processing', 'completed'):
                logger.info(f"Order #{order.id} already processed, skipping")
                return True

            order.mark_as_paid()
            logger.info(f"Order #{order.id} marked as paid")

        elif event_type == 'payment.canceled':
            if order.status == 'cancelled':
                logger.info(f"Order #{order.id} already cancelled, skipping")
                return True

            order.mark_as_cancelled()
            logger.info(f"Order #{order.id} cancelled")
            return True

        else:
            logger.info(f"Ignoring webhook event: {event_type}")
            return True

    # Launch elephant generation outside the transaction
    if event_type == 'payment.succeeded':
        generate_elephant_image.delay(order.id)
        logger.info(f"Elephant generation started for order #{order.id}")

    return True


def check_payment_status(order: Order) -> str:
    """
    Check payment status via YooKassa API.

    Args:
        order: Order instance with yookassa_payment_id

    Returns:
        Payment status string from YooKassa
    """
    if not order.yookassa_payment_id:
        return 'unknown'

    _configure_yookassa()

    payment = Payment.find_one(order.yookassa_payment_id)
    return payment.status
