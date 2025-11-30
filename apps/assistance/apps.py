from django.apps import AppConfig


class AssistanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assistance'
    verbose_name = 'Assistance Management'

    def ready(self):
        import apps.assistance.signals  # noqa
