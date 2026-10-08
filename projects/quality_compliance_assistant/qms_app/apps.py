from django.apps import AppConfig

class QmsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'qms_app'

    def ready(self):
        from . import signals  # noqa
