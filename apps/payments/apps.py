from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger('apps')


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'Payments'

    def ready(self):
        """Validate YooKassa configuration on startup."""
        shop_id = getattr(settings, 'YOOKASSA_SHOP_ID', None)
        secret_key = getattr(settings, 'YOOKASSA_SECRET_KEY', None)

        if not shop_id or not secret_key:
            logger.warning(
                "YOOKASSA_SHOP_ID and/or YOOKASSA_SECRET_KEY are not configured. "
                "Payment functionality will be unavailable until these are set."
            )
        else:
            logger.info("YooKassa payment configuration loaded successfully.")
