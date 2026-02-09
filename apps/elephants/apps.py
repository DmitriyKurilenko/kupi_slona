from django.apps import AppConfig


class ElephantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.elephants'
    verbose_name = 'Elephants'

    def ready(self):
        """Import signals when app is ready"""
        import apps.elephants.signals  # noqa
