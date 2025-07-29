import os

# # Настройки подключения к PostgreSQL
# DB_CONFIG = {
#     "host": "localhost",
#     "port": 5432,
#     "database": "farmer_markets",  # Создадим базу с таким именем
#     "user": "postgres",            # Админский логин
#     "password": ""      # Админский пароль
# }


# Читаем настройки из переменных окружения (если их нет — используем значения по умолчанию)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "farmer_markets"),  # Создадим базу с таким именем
    "user": os.getenv("DB_USER", "app_user"),       # заменили postgres на app_user
    "password": os.getenv("DB_PASSWORD", "app_pass") # заменили суперпользователя на нормального юзера
}
