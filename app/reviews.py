from .db import execute_query           # импортируем функцию для работы с БД
from prompt_toolkit import prompt       # современный безопасный ввод

# ===========================================================
# === 1. Добавление нового отзыва ===
# ===========================================================
def add_review():
    # Добавляет отзыв для выбранного рынка

    # Получаем ID рынка (должен быть числом)
    while True:
        market_id = prompt("Введите ID рынка: ").strip()
        if market_id.isdigit():
            market_id = int(market_id)
            break
        print("Ошибка: ID должен быть числом.")

    # Получаем имя и фамилию без доп. проверки
    first_name = prompt("Введите имя: ").strip()
    last_name = prompt("Введите фамилию: ").strip()
    user_name = f"{first_name} {last_name}"

    # Получаем оценку от 1 до 5
    while True:
        rating = prompt("Оценка (1-5): ").strip()
        if rating.isdigit() and 1 <= int(rating) <= 5:
            rating = int(rating)
            break
        print("Ошибка: введите число от 1 до 5.")

    # Получаем текст отзыва (оставляем как есть, без фильтрации)
    review_text = prompt("Текст отзыва: ").strip()

    # Сохраняем отзыв в базу данных
    execute_query(
        "INSERT INTO reviews (market_id, user_name, rating, review_text) VALUES (%s, %s, %s, %s)",
        (market_id, user_name, rating, review_text)
    )
    print("Отзыв добавлен.")

# ===========================================================
# === 2. Удаление отзыва по ID ===
# ===========================================================
def delete_review():
    # Удаляет отзыв по ID
    while True:
        review_id = prompt("Введите ID отзыва: ").strip()
        if review_id.isdigit():
            break
        print("Ошибка: ID должен быть числом.")
        
    execute_query("DELETE FROM reviews WHERE id = %s", (review_id,))
    print("Отзыв удалён.")
