# web/markets/signals.py
# ---------------------------------------------------------------
# Подписываемся на сигнал post_migrate и вызываем нашу команду init_roles
# сразу после применения миграций. Это удобно в Docker-entrypoint.
# ---------------------------------------------------------------
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.management import call_command


@receiver(post_migrate)
def init_roles_after_migrate(sender, **kwargs):
    """
    Этот обработчик вызывается Django после каждой миграции.
    Мы запускаем команду init_roles. Команда идемпотентная — безопасно.
    """
    try:
        call_command("init_roles")  # создаст/обновит группы и права
    except Exception as e:
        # Не валим запуск проекта из-за ошибок прав — просто логируем
        print(f"[post_migrate] init_roles: предупреждение: {e}")
