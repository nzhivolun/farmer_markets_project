# setup_db.py
# ===========================================================
# Этот скрипт отвечает за:
# 1. Создание базы данных (если она ещё не существует).
# 2. Создание всех таблиц в базе данных по файлу init.sql.
#
# Используем библиотеку psycopg2 для работы с PostgreSQL.
# ===========================================================

import psycopg2  # для подключения к PostgreSQL
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  # нужен для CREATE DATABASE
import os
from setup.config import DB_CONFIG  # импортируем настройки подключения (хост, порт, база, логин, пароль)


# ===========================================================
# === Функция для создания базы данных ===
# ===========================================================
def create_database():
    """
    Создаёт базу данных farmer_markets, если она ещё не существует.
    Почему отдельное подключение?
    - Команда CREATE DATABASE не может выполняться внутри базы, которую мы хотим создать.
    - Поэтому подключаемся к системной базе postgres.
    """

    try:
        # 1. Подключаемся к системной базе PostgreSQL (dbname="postgres")
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],      # хост базы данных
            user=DB_CONFIG["user"],      # пользователь
            password=DB_CONFIG["password"],  # пароль
            port=DB_CONFIG["port"],      # порт
            dbname="postgres"            # системная база
        )

        # 2. Разрешаем выполнять команды CREATE DATABASE (автокоммит)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        # 3. Создаём курсор
        cur = conn.cursor()

        # 4. Проверяем, есть ли база с именем из DB_CONFIG["database"]
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["database"],))
        if not cur.fetchone():
            # Если базы нет — создаём
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print(f"База данных {DB_CONFIG['database']} создана.")
        else:
            print(f"ℹБаза {DB_CONFIG['database']} уже существует.")

        # 5. Закрываем соединение
        cur.close()
        conn.close()

    except Exception as e:
        # Если ошибка — выводим сообщение
        print(f"Ошибка при создании базы: {e}")


# ===========================================================
# === Функция для создания таблиц из init.sql ===
# ===========================================================
def create_tables():
    """
    Создаёт таблицы в базе данных.
    Используем SQL-скрипт init.sql, где описана структура таблиц.
    """

    try:
        # 1. Подключаемся к нашей базе данных farmer_markets
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 2. Формируем путь к файлу init.sql (лежит рядом с этим скриптом)
        sql_path = os.path.join(os.path.dirname(__file__), "init.sql")

        # 3. Читаем SQL-скрипт из файла
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # 4. Выполняем весь скрипт (создание таблиц и индексов)
        cur.execute(sql_script)

        # 5. Фиксируем изменения
        conn.commit()
        print("Таблицы созданы успешно.")

        # 6. Закрываем соединение
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")


# ===========================================================
# === Точка входа (если запускаем файл напрямую) ===
# ===========================================================
if __name__ == "__main__":
    create_database()  # создаём базу
    create_tables()    # создаём таблицы
