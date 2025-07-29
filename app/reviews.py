from .db import execute_query  # импортируем функцию для работы с БД


# ===========================================================
# === 1. Добавление нового отзыва ===
# ===========================================================
def add_review():
    """Добавляет отзыв для выбранного рынка"""
    market_id = input("Введите ID рынка: ").strip()
    first_name = input("Введите имя: ").strip()
    last_name = input("Введите фамилию: ").strip()
    rating = input("Оценка (1-5): ").strip()
    review_text = input("Текст отзыва: ").strip()

    # Удаляем невалидные символы
    review_text = review_text.encode('utf-8', 'ignore').decode('utf-8')

    # Проверка корректности данных
    if not (market_id.isdigit() and rating.isdigit() and 1 <= int(rating) <= 5):
        print("Ошибка: неверный ввод.")
        return

    user_name = f"{first_name} {last_name}"
    execute_query(
        "INSERT INTO reviews (market_id, user_name, rating, review_text) VALUES (%s,%s,%s,%s)",
        (market_id, user_name, int(rating), review_text)
    )
    print("Отзыв добавлен.")


# ===========================================================
# === 2. Удаление отзыва по ID ===
# ===========================================================
def delete_review():
    """Удаляет отзыв по ID"""
    review_id = input("Введите ID отзыва: ").strip()
    if not review_id.isdigit():
        print("Неверный ID.")
        return
    execute_query("DELETE FROM reviews WHERE id = %s", (review_id,))
    print("Отзыв удалён.")