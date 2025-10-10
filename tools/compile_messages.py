# tools/compile_messages.py
# =========================
# Компиляция .po → .mo с помощью polib (чистый Python, работает на Windows/Linux/macOS).
# Скрипт максимально простой, с подробными комментариями для новичка.

import os
import sys

# Импортируем polib — это маленькая библиотека, специально для .po/.mo
# Установить: pip install polib
import polib  # внешний модуль, но очень лёгкий

def compile_one_po(po_path: str) -> None:
    """
    Компилируем ОДИН .po в .mo.
    1) Проверяем, что .po существует.
    2) Открываем .po как UTF-8.
    3) Сохраняем .mo рядом (тот же каталог).
    """
    # Проверяем существование файла .po
    if not os.path.isfile(po_path):
        print(f"[ОШИБКА] Файл не найден: {po_path}")
        sys.exit(1)

    # Вычисляем путь для файла .mo (так же рядом, имя то же, расширение .mo)
    base_dir, name = os.path.split(po_path)
    if not name.lower().endswith(".po"):
        print("[ОШИБКА] Нужен именно .po файл")
        sys.exit(1)
    mo_path = os.path.join(base_dir, name[:-3] + ".mo")

    # Открываем .po в явной кодировке UTF-8
    # polib сам корректно обработает многострочные записи, plural-формы и т.д.
    po = polib.pofile(po_path, encoding="utf-8")

    # Перед записью .mo — на всякий случай удалим старый .mo, если он есть
    try:
        if os.path.exists(mo_path):
            os.remove(mo_path)
    except Exception as e:
        print(f"[ПРЕДУПРЕЖДЕНИЕ] Не удалось удалить старый .mo: {e}")

    # Сохраняем корректный .mo
    po.save_as_mofile(mo_path)
    print(f"[OK] Скомпилировано: {mo_path}")

def main():
    """
    Точка входа.
    Если путь передан аргументом — используем его.
    Если аргумента нет — пробуем типовой путь:
      1) web/locale/ru/LC_MESSAGES/django.po
      2) locale/ru/LC_MESSAGES/django.po
    """
    if len(sys.argv) == 2:
        po_path = sys.argv[1]
    else:
        candidates = [
            os.path.join("web", "locale", "ru", "LC_MESSAGES", "django.po"),
            os.path.join("locale", "ru", "LC_MESSAGES", "django.po"),
        ]
        po_path = None
        for p in candidates:
            if os.path.isfile(p):
                po_path = p
                break
        if po_path is None:
            print("Не найден django.po. Запусти так:")
            print("  python tools\\compile_messages.py web\\locale\\ru\\LC_MESSAGES\\django.po")
            sys.exit(1)

    # Дополнительная проверка: в заголовке .po должна быть UTF-8
    # Это НЕ обязательно, но полезно. Если там стоит другое — лучше поправить.
    try:
        text = open(po_path, "r", encoding="utf-8").read(2048)
        if 'charset=UTF-8' not in text and 'charset=utf-8' not in text:
            print("[ВНИМАНИЕ] В заголовке .po нет charset=UTF-8. Рекомендуется исправить.")
    except UnicodeDecodeError:
        print("[ОШИБКА] .po НЕ в UTF-8. Открой и пересохрани как UTF-8 без BOM.")
        sys.exit(1)

    compile_one_po(po_path)

if __name__ == "__main__":
    main()
