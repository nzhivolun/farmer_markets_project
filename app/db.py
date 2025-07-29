# db.py
# ==============================================
# Этот модуль отвечает за подключение к базе данных PostgreSQL
# и выполнение SQL-запросов.
# Здесь мы используем библиотеку psycopg2 для работы с PostgreSQL.
# ==============================================

import sys
import os

# Добавляем путь к папке setup, чтобы можно было импортировать config.py
# os.path.dirname(__file__) — это путь к текущей папке (где лежит db.py)
# '..' — поднимаемся на уровень выше, добавляем 'setup'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))

# Импортируем словарь DB_CONFIG из файла config.py
# В нем хранятся настройки подключения к базе данных (хост, порт, имя базы и т.д.)
from setup.config import DB_CONFIG

# Импортируем библиотеку для работы с PostgreSQL
import psycopg2
# RealDictCursor нужен для того, чтобы результаты запроса возвращались в виде словаря
# (ключи — это названия колонок, значения — данные)
from psycopg2.extras import RealDictCursor


def get_connection():
    """
    Функция создает подключение к базе данных PostgreSQL.
    Возвращает объект соединения conn.

    Почему отдельная функция?
    - Чтобы в любом месте кода можно было просто вызвать get_connection()
      и получить готовое подключение.
    """
    return psycopg2.connect(**DB_CONFIG)  # **DB_CONFIG разворачивает словарь в аргументы


def execute_query(query, params=None, fetch=False):
    """
    Выполняет SQL-запрос к базе данных.

    :param query: SQL-строка (например, SELECT ... FROM ...)
    :param params: кортеж или список параметров, которые будут подставлены в SQL (например, (id,))
    :param fetch: если True, то вернем результат (список словарей), если False — ничего не возвращаем
    :return: список словарей с результатами (если fetch=True) или None
    """

    # 1. Создаем подключение к базе данных
    conn = get_connection()

    # 2. Создаем курсор для выполнения запросов
    # Используем RealDictCursor, чтобы результат возвращался как словарь:
    #   { 'id': 1, 'name': 'Market 1' }
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 3. Выполняем SQL-запрос
    # params or () — если params нет, передаем пустой кортеж, чтобы не было ошибок
    cur.execute(query, params or ())

    # 4. Если нужно получить результат, читаем все строки
    result = None
    if fetch:
        result = cur.fetchall()  # Возвращает список словарей

    # 5. Фиксируем изменения (если были INSERT/UPDATE/DELETE)
    conn.commit()

    # 6. Закрываем соединение с базой
    conn.close()

    # 7. Возвращаем результат (или None)
    return result
