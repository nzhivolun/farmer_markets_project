# web/markets/middleware.py
# -------------------------
# Простейшая прослойка (middleware), которая принудительно перенаправляет
# всех НЕавторизованных пользователей на страницу логина.
# Исключения: страницы логина/логаута, регистрации, админка, статика/медиа.

import re
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    Логика работы (читаем последовательно):
    1) Если пользователь уже авторизован (request.user.is_authenticated == True),
       то ничего не делаем — пускаем дальше.
    2) Если URL попадает в «белый список» (логин, логаут, регистрация, админка, статика, медиа),
       то тоже пропускаем без авторизации.
    3) Иначе — редиректим на LOGIN_URL, добавляя next=<исходный путь>, чтобы после логина вернуться.
    """

    def __init__(self, get_response):
        # Сохраняем ссылку на следующий обработчик
        self.get_response = get_response

        # Готовим регулярные выражения для исключений (белый список)
        # Комментарии для новичка: r'^pattern$' означает "строка URL целиком должна совпасть с pattern".
        self.exempt_urls = [
            re.compile(r'^' + re.escape(settings.LOGIN_URL) + r'$'),   # /login/   (страница входа)
        ]

        # Если используете logout по URL /logout/ (или /accounts/logout/), добавьте шаблон ниже
        # Здесь используем оба варианта, чтобы ничего не сломать:
        self.exempt_urls.append(re.compile(r'^/logout/$'))
        self.exempt_urls.append(re.compile(r'^/accounts/logout/$'))

        # Регистрация (саморегистрация пользователей)
        self.exempt_urls.append(re.compile(r'^/register/$'))

        # Админка — должна быть доступна без предварительного логина через нашу прослойку,
        # т.к. сама админка проверит доступ и покажет форму входа:
        self.exempt_urls.append(re.compile(r'^/admin/'))

        # Статика/медиа — без авторизации (иначе сломается CSS/JS/картинки):
        self.exempt_urls.append(re.compile(r'^/static/'))
        self.exempt_urls.append(re.compile(r'^/media/'))

        # Частые сервисные пути браузера/иконки:
        self.exempt_urls.append(re.compile(r'^/favicon\.ico$'))
        self.exempt_urls.append(re.compile(r'^/robots\.txt$'))

    def __call__(self, request):
        path = request.path  # текущий путь, например: "/list/"

        # Если пользователь уже вошёл — пропускаем:
        if request.user.is_authenticated:
            return self.get_response(request)

        # Проверяем, не попадает ли путь в белый список:
        for pattern in self.exempt_urls:
            if pattern.match(path):
                return self.get_response(request)

        # Если сюда дошли — значит пользователь неавторизован и URL не из исключений.
        # Делаем редирект на страницу логина, передаём next=...,
        # чтобы после входа вернуться обратно на исходную страницу.
        login_url = settings.LOGIN_URL  # например, "/login/"
        return redirect(f"{login_url}?next={path}")
