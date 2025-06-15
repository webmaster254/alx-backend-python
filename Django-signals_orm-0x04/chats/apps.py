from django.apps import AppConfig


class ChatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chats'

    def ready(self):
        """
        Import signal handlers when the app is ready.
        This ensures that Django signals are properly registered.
        """
        import chats.signals
