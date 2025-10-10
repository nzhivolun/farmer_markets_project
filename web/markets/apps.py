from django.apps import AppConfig


class MarketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'markets'
    
    def ready(self):
        # Импортируем обработчики сигналов при старте приложения
        # (импорт внутри метода ready, чтобы не было ранних импортов)
        from . import signals  # noqa: F401
