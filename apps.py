from django.apps import AppConfig


class AutowashConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'autowash'
    # myapp/apps.py

class AutowashConfig(AppConfig):
    name = 'autowash'

    def ready(self):
        import autowash.signals

