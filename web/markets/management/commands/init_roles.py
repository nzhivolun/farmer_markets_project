# web/markets/management/commands/init_roles.py
# ---------------------------------------------
# Очень простой скрипт: создаёт группы "Администраторы" и "Пользователи"
# и назначает им права на основе наших моделей и встроенных моделей Django.

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from markets.models import Market, Review

class Command(BaseCommand):
    help = "Создаёт группы и назначает им базовые права"

    def handle(self, *args, **options):
        # Получаем/создаём группы
        admins_group, _ = Group.objects.get_or_create(name="Администраторы")
        users_group, _  = Group.objects.get_or_create(name="Пользователи")

        # ContentTypes для наших моделей
        ct_market = ContentType.objects.get_for_model(Market)
        ct_review = ContentType.objects.get_for_model(Review)

        # Права по отзывам (стандартные)
        add_review    = Permission.objects.get(codename="add_review",    content_type=ct_review)
        delete_review = Permission.objects.get(codename="delete_review", content_type=ct_review)
        view_review   = Permission.objects.get(codename="view_review",   content_type=ct_review)

        # Кастомные права по рынкам
        can_delete_market = Permission.objects.get(codename="can_delete_market", content_type=ct_market)
        # can_create_market оставим без назначения группам (только суперпользователь)
        # но объект разрешения существует:
        can_create_market = Permission.objects.get(codename="can_create_market", content_type=ct_market)

        # Права по пользователям (встроенная модель auth.User)
        ct_user = ContentType.objects.get(app_label="auth", model="user")
        add_user   = Permission.objects.get(codename="add_user",   content_type=ct_user)
        change_user= Permission.objects.get(codename="change_user",content_type=ct_user)
        view_user  = Permission.objects.get(codename="view_user",  content_type=ct_user)

        # --- Группа "Администраторы" ---
        # Могут: создавать пользователей, добавлять/удалять отзывы, удалять рынки.
        admins_perms = [
            add_user, change_user, view_user,
            add_review, delete_review, view_review,
            can_delete_market,  # важно!
        ]
        admins_group.permissions.set(admins_perms)  # перезаписываем набор прав
        # По желанию можно сделать add() чтобы не затирать существующие.

        # --- Группа "Пользователи" ---
        # Могут: добавлять отзывы, смотреть отзывы, удалять ТОЛЬКО свои отзывы
        # (логику "только свои" мы проверим во view delete_review)
        users_perms = [
            add_review, view_review, delete_review,  # delete_review остаётся, но во view будет проверка владельца
        ]
        users_group.permissions.set(users_perms)

        self.stdout.write(self.style.SUCCESS("Группы и права инициализированы."))
