"""
YooKassa payment integration service
"""
import json
import logging
import uuid

from django.conf import settings
from django.db import transaction

from .models import Order
from apps.elephants.tasks import generate_elephant_image

logger = logging.getLogger('apps')


class YooKassaConfigError(Exception):
    """Raised when YooKassa credentials are missing or invalid."""
    pass


class YooKassaAPIError(Exception):
    """Raised when YooKassa API returns an error."""
    def __init__(self, message, status_code=None, raw_response=None):
        super().__init__(message)
        self.status_code = status_code
        self.raw_response = raw_response


def _configure_yookassa():
    """Configure YooKassa SDK with shop credentials."""
    shop_id = getattr(settings, 'YOOKASSA_SHOP_ID', None)
    secret_key = getattr(settings, 'YOOKASSA_SECRET_KEY', None)

    if not shop_id or not secret_key:
        raise YooKassaConfigError(
            "YooKassa credentials are not configured. "
            "Set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY environment variables."
        )

    try:
        from yookassa import Configuration
        Configuration.account_id = str(shop_id)
        Configuration.secret_key = str(secret_key)
    except Exception as e:
        raise YooKassaConfigError(f"Failed to configure YooKassa SDK: {e}")


def create_yookassa_payment(order: Order) -> str:
    """
    Create YooKassa payment for an order.

    Args:
        order: Order instance (must be in 'pending' status)

    Returns:
        confirmation_url for redirect to YooKassa payment page

    Raises:
        ValueError: If order is not in pending status
        YooKassaConfigError: If YooKassa credentials are not configured
        YooKassaAPIError: If YooKassa API call fails
    """
    if order.status != 'pending':
        raise ValueError(f"Order #{order.id} is not in pending status")

    _configure_yookassa()

    # Use uuid5 based on order ID for idempotency
    idempotency_key = str(uuid.uuid5(uuid.NAMESPACE_URL, f"order-{order.id}"))

    tariff_display = order.tariff.get_name_display()

    payload = {
        "amount": {
            "value": str(order.tariff.price),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"{settings.YOOKASSA_RETURN_URL}?order_id={order.id}"
        },
        "capture": True,
        "description": f"Слон — тариф «{tariff_display}»"[:128],
        "metadata": {
            "order_id": order.id
        }
    }

    try:
        from yookassa import Payment
        payment = Payment.create(payload, idempotency_key)
    except Exception as e:
        error_name = type(e).__name__
        error_msg = str(e)
        logger.exception(
            f"YooKassa API error ({error_name}) creating payment for order #{order.id}: {error_msg}"
        )
        raw = getattr(e, 'json_body', None) or getattr(e, 'raw_response', None)
        raise YooKassaAPIError(
            message=f"Payment gateway error: {error_msg}",
            raw_response=raw
        )

    if not payment or not getattr(payment, 'confirmation', None):
        logger.error(f"YooKassa returned invalid payment object for order #{order.id}")
        raise YooKassaAPIError("YooKassa returned invalid payment object")

    confirmation_url = getattr(payment.confirmation, 'confirmation_url', None)
    if not confirmation_url:
        logger.error(f"YooKassa did not return confirmation_url for order #{order.id}")
        raise YooKassaAPIError("YooKassa did not return confirmation_url")

    # Save YooKassa payment ID to order
    order.yookassa_payment_id = payment.id
    order.save(update_fields=['yookassa_payment_id'])

    logger.info(
        f"YooKassa payment {payment.id} created for order #{order.id}, "
        f"redirect URL: {confirmation_url}"
    )

    return confirmation_url


def process_yookassa_webhook(body: bytes) -> bool:
    """
    Process YooKassa webhook notification.
    Idempotent — safe to call multiple times for the same event.

    Args:
        body: Raw request body bytes

    Returns:
        True if processed successfully
    """
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid webhook JSON: {e}")
        return False

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
        Payment status string from YooKassa or 'unknown'
    """
    if not order.yookassa_payment_id:
        return 'unknown'

    try:
        _configure_yookassa()
    except YooKassaConfigError:
        logger.error("Cannot check payment status: YooKassa not configured")
        return 'unknown'

    try:
        from yookassa import Payment
        payment = Payment.find_one(order.yookassa_payment_id)
        return payment.status
    except Exception as e:
        logger.exception(f"Failed to check payment status for order #{order.id}: {e}")
        return 'unknown'
