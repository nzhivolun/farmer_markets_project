# === Патч пути: добавляем корень проекта в sys.path ===
# Это нужно, потому что Streamlit запускает файл как обычный скрипт (__main__),
# === Патч пути: добавляем корень проекта в sys.path ===
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # .../app
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))  # корень проекта
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

# ВАЖНО: только абсолютные импорты из пакета app
from app.ui_markets_streamlit import (
    show_markets_page,
    search_market_page,
    show_market_details_page,
    sort_markets_page,
    search_by_radius_page,
    delete_market_page,
    add_review_page,
    delete_review_page,
    render_markets_by_category
)

st.set_page_config(page_title="Farmer Markets — Streamlit", layout="wide")

# --- Делаем ЛЕВЫЙ САЙДБАР максимально широким при старте ---
# Мы применяем CSS ко встроенному контейнеру сайдбара Streamlit (по data-testid).
# Важно: этим мы меняем ТОЛЬКО левый сайдбар, правая рабочая область остаётся как есть.
# При необходимости меняйте цифры ниже (rem/px) под ваш монитор.

st.markdown("""
    <style>
    /* Сам контейнер сайдбара */
    [data-testid="stSidebar"] {
        /* Ширина сайдбара. 28rem ~ 448px (1rem ≈ 16px). Можно увеличить до 32rem и т.п. */
        width: 28rem !important;
        min-width: 28rem !important;   /* чтобы не сжимался меньше заданного */
        max-width: 40rem !important;   /* верхняя граница (на всякий случай) */
    }
    /* Внутренний wrapper, чтобы ширина применилась корректно */
    [data-testid="stSidebar"] > div {
        width: 28rem !important;
        min-width: 28rem !important;
        max-width: 40rem !important;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. Описание пунктов меню (как в консольном скриншоте) ---
MENU = [
    (1, "Список рынков"),
    (2, "Поиск по городу/штату/индексу"),
    (3, "Детали рынка"),
    (4, "Добавить отзыв"),
    (5, "Удалить отзыв"),
    (6, "Сортировка рынков"),
    (7, "Поиск по радиусу (30 миль)"),
    (8, "Удалить рынок"),
    (9, "Показать рынки по категории"),
    (0, "Выход"),
]

# --- 3. Инициализация состояния приложения ---
if "current_page_id" not in st.session_state:
    st.session_state["current_page_id"] = 1  # по умолчанию открываем пункт №1

# --- 4. Заглушки-страницы (только заголовок и TODO) ---
def page_list_markets():
    show_markets_page()

def page_search():
    search_market_page()

def page_details():
    show_market_details_page()

def page_add_review():
    add_review_page()

def page_delete_review():
    delete_review_page()

def page_sort():
    sort_markets_page()

def page_radius():
    search_by_radius_page()

def page_delete_market():
    delete_market_page()

def page_by_category():
    render_markets_by_category()

def page_exit():
    st.header("0. Выход")
    st.warning("В веб-версии Streamlit пункт «Выход» ничего не делает. Можно просто закрыть вкладку браузера.")

# --- 5. Роутер страниц: номер -> функция ---
PAGE_ROUTER = {
    1: page_list_markets,
    2: page_search,
    3: page_details,
    4: page_add_review,
    5: page_delete_review,
    6: page_sort,
    7: page_radius,
    8: page_delete_market,
    9: page_by_category,
    0: page_exit,
}

# --- 6. Сайдбар (меню-кнопки слева) ---
with st.sidebar:
    # Заголовок меню + версия (просто как пример)
    st.title("Меню")
    st.caption("Farmer Markets App")

    # Рисуем по кнопке на каждый пункт меню
    for num, title in MENU:
        label = f"{num}. {title}"
        # use_container_width=True — растягивает кнопку на всю доступную ширину сайдбара
        if st.button(label, key=f"menu_{num}", use_container_width=True):
            st.session_state["current_page_id"] = num

    st.markdown("---")
    active = st.session_state.get("current_page_id", 1)
    name = dict(MENU).get(active, "неизвестно")
    st.caption(f"Активный пункт: {active}. {name}")

# --- 7. Основное окно (справа) ---
current_id = st.session_state.get("current_page_id", 1)
page_fn = PAGE_ROUTER.get(current_id)

if page_fn is None:
    st.error("Страница не найдена. Проверьте PAGE_ROUTER.")
else:
    page_fn()