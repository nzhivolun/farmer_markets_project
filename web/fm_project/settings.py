from pathlib import Path
import os

from django.utils.translation import gettext_lazy as _

# >>> ДОБАВИТЬ СРАЗУ ПОСЛЕ ЭТИХ ИМПОРТОВ:
# Подключаем загрузку переменных окружения из файла .env (лежит в папке web/)
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем .env. Файл .env должен лежать рядом с manage.py (в папке web)
load_dotenv(dotenv_path=BASE_DIR / '.env')


# ===================== БЕЗОПАСНЫЕ НАСТРОЙКИ ЧЕРЕЗ .ENV =====================
# ВАЖНО: мы больше не храним секреты (ключ, пароли) в коде.
# Всё читаем из окружения. В .env.example показаны примеры значений.

# Секретный ключ Django — строка, которая должна быть длинной и случайной
SECRET_KEY = os.getenv('SECRET_KEY', 'replace_me_with_random_string')

# Режим отладки: 1 / 0 (по умолчанию включен в разработке)
DEBUG = os.getenv('DEBUG', '1') in ('1', 'true', 'True')

# Список хостов, с которых разрешён доступ (через запятую). Для разработки разрешим все.
# Можно указать, например: "localhost,127.0.0.1,192.168.1.105"
ALLOWED_HOSTS_ENV = os.getenv('ALLOWED_HOSTS', '*')
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(',')] if ALLOWED_HOSTS_ENV else ['*']

# После успешного логина – куда редиректить
LOGIN_REDIRECT_URL = "/"

# # После логаута – куда редиректить
# LOGOUT_REDIRECT_URL = "/"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"


# ============================================================================


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',      # стандартные приложения Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'markets',  # ← добавляем наше приложение с рынками
    'markets.apps.MarketsConfig',  # <-- было 'markets'
]

# ----------------- MIDDLEWARE -----------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # ↓↓↓ Должен идти сразу после SessionMiddleware и до CommonMiddleware
    'django.middleware.locale.LocaleMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# ----------------------------------------------

ROOT_URLCONF = 'fm_project.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Ищем шаблоны в папке web/templates
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,  # а также в templates/ внутри приложений (markets/templates/)
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # ВАЖНО: этот процессор даёт в шаблоны переменные и теги i18n
                "django.template.context_processors.i18n",
            ],
        },
    },
]

# === Настройки статики (просто и по-умолчанию) ===
STATIC_URL = 'static/'             # URL-префикс для статики
STATICFILES_DIRS = [
    BASE_DIR / 'static',            # указывает на папку: ...\web\static
]

WSGI_APPLICATION = 'fm_project.wsgi.application'


# ===================== НАСТРОЙКИ БАЗЫ ДАННЫХ (POSTGRES) =====================
# Все параметры читаем из .env. Никакого хардкода паролей в коде.
DB_NAME = os.getenv("DB_NAME", "farmer_markets")   # имя базы
DB_USER = os.getenv("DB_USER", "app_user")         # пользователь БД
DB_PASSWORD = os.getenv("DB_PASSWORD", "app_pass") # пароль пользователя БД
DB_HOST = os.getenv("DB_HOST", "localhost")        # хост БД (в Docker это может быть 'db')
DB_PORT = int(os.getenv("DB_PORT", "5432"))        # порт БД

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",  # используем PostgreSQL драйвер
        "NAME": DB_NAME,       # имя базы данных
        "USER": DB_USER,       # пользователь
        "PASSWORD": DB_PASSWORD,  # пароль
        "HOST": DB_HOST,       # адрес сервера БД
        "PORT": DB_PORT,       # порт (по умолчанию 5432)
    }
}
# ============================================================================

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# === Локализация ===
LANGUAGE_CODE = 'en'  # по умолчанию английский интерфейс

LANGUAGES = [
    ('en', _('English')),
    ('ru', _('Русский')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',  # => web/locale
]

TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

