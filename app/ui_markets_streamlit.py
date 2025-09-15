# app/ui_markets_streamlit.py
# ============================================================
# Streamlit-страницы для раздела "Рынки".
# Здесь мы повторяем функции из консольного markets.py, но
# делаем их web-версиями. Консольный код НЕ меняем.

import math
import streamlit as st

# Импортируем функции работы с БД и валидации
# Обрати внимание: импорт абсолютный (через пакет app), без точек.
from app.db import execute_query          # выполнение SQL
from app.utils import validate_coordinates  # проверка широты/долготы


# -----------------------------
# ВСПОМОГАТЕЛЬНЫЕ ЭЛЕМЕНТЫ UI
# -----------------------------

def _pager(total: int, per_page: int, key_prefix: str) -> int:
    """
    Простой пагинатор на кнопках. Держим номер страницы в st.session_state.

    total     — всего записей
    per_page  — сколько записей показываем на странице
    key_prefix — уникальный префикс ключей (чтобы страницы не конфликтовали)
    """
    # Если total = 0, показывать нечего — возвращаем 1 по умолчанию
    total_pages = max(1, math.ceil(max(0, total) / max(1, per_page)))

    # Получаем/инициализируем номер страницы
    page_key = f"{key_prefix}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    # Рисуем элементы пагинации
    col1, col2, col3 = st.columns(3)
    with col1:
        # Кнопка "Назад" — уменьшаем страницу, но не меньше 1
        if st.button("◀ Назад", use_container_width=True, disabled=st.session_state[page_key] <= 1, key=f"{key_prefix}_prev"):
            st.session_state[page_key] = max(1, st.session_state[page_key] - 1)
    with col2:
        # Текущий статус страниц
        st.write(f"Страница {st.session_state[page_key]} из {total_pages}")
    with col3:
        # Кнопка "Вперёд" — увеличиваем страницу, но не больше total_pages
        if st.button("Вперёд ▶", use_container_width=True, disabled=st.session_state[page_key] >= total_pages, key=f"{key_prefix}_next"):
            st.session_state[page_key] = min(total_pages, st.session_state[page_key] + 1)

    return st.session_state[page_key]


def _per_page_control(default: int, key_prefix: str) -> int:
    """
    Небольшой контрол для выбора "сколько строк на странице".
    Храним выбранное значение в session_state, чтобы кнопки пагинации сохраняли контекст.
    """
    per_key = f"{key_prefix}_per_page"
    if per_key not in st.session_state:
        st.session_state[per_key] = default

    st.session_state[per_key] = st.number_input(
        label="Сколько строк на странице",
        min_value=5, max_value=100, value=st.session_state[per_key], step=5,
        help="Чем больше значение — тем больше записей будет на странице."
    )
    return st.session_state[per_key]


def st_paginate(total: int, per_page: int, key_prefix: str) -> int:
    """
    Универсальная пагинация для Streamlit (аналог консольной paginate, но без input()).
    Возвращает OFFSET (смещение) для SQL (то есть начало среза).
    
    Пояснение:
    - total      — сколько всего записей в результате (например, 523 рынка)
    - per_page   — сколько строк показываем на одной странице (например, 10)
    - key_prefix — уникальный префикс, чтобы состояние страниц разных разделов не конфликтовало.
      Например: "list", "search", "sort". Для каждой страницы префикс должен быть свой.
    
    Что делает функция:
    - хранит текущий номер страницы в st.session_state, чтобы при нажатии кнопок страница менялась
    - рисует кнопки «В начало», «Назад», «Вперёд», «В конец» и поле для ручного ввода номера страницы
    - отдаёт offset = (page - 1) * per_page, который удобно подставлять в SQL (LIMIT/OFFSET)
    """

    # --- Готовим ключи для session_state (уникальные для каждого раздела) ---
    page_key = f"{key_prefix}_page"   # здесь будет храниться текущая страница (1, 2, 3, ...)
    total_pages = max(1, math.ceil(max(0, total) / max(1, per_page)))  # хотя бы 1 страница

    # Инициализация страницы по умолчанию (если ещё ни разу не открывали раздел)
    if page_key not in st.session_state:
        st.session_state[page_key] = 1  # начинаем с первой страницы

    # Если вдруг после нового поиска total изменился и текущая страница стала «выше потолка» — чиним
    if st.session_state[page_key] > total_pages:
        st.session_state[page_key] = total_pages
    if st.session_state[page_key] < 1:
        st.session_state[page_key] = 1

    # --- Рисуем элементы управления пагинацией ---
    # 4 колонки: [В начало] [Назад] [Номер страницы] [Вперёд] [В конец]
    c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1, 1])

    with c1:
        # Кнопка "В начало" — перейти на страницу 1
        if st.button("⏮ В начало", use_container_width=True, disabled=(st.session_state[page_key] <= 1), key=f"{key_prefix}_first"):
            st.session_state[page_key] = 1

    with c2:
        # Кнопка "Назад" — страница - 1 (не меньше 1)
        if st.button("◀ Назад", use_container_width=True, disabled=(st.session_state[page_key] <= 1), key=f"{key_prefix}_prev_btn"):
            st.session_state[page_key] = max(1, st.session_state[page_key] - 1)

    with c3:
        # Поле для ручного ввода номера страницы (строго в допустимых пределах)
        current = st.number_input(
            "Страница",
            min_value=1,
            max_value=total_pages,
            value=int(st.session_state[page_key]),
            step=1,
            help="Можно ввести номер страницы вручную."
        )
        # Если пользователь поменял значение — сохраняем в состояние
        if int(current) != st.session_state[page_key]:
            st.session_state[page_key] = int(current)

    with c4:
        # Кнопка "Вперёд" — страница + 1 (не больше total_pages)
        if st.button("Вперёд ▶", use_container_width=True, disabled=(st.session_state[page_key] >= total_pages), key=f"{key_prefix}_next_btn"):
            st.session_state[page_key] = min(total_pages, st.session_state[page_key] + 1)

    with c5:
        # Кнопка "В конец" — перейти на последнюю страницу
        if st.button("⏭ В конец", use_container_width=True, disabled=(st.session_state[page_key] >= total_pages), key=f"{key_prefix}_last"):
            st.session_state[page_key] = total_pages

    # Подпись-индикатор
    st.caption(f"Страница {st.session_state[page_key]} из {total_pages} (всего записей: {total})")

    # Возвращаем OFFSET для SQL
    offset = (st.session_state[page_key] - 1) * per_page
    return offset


# -----------------------------
# 1) Список рынков (Streamlit)
# -----------------------------
def show_markets_page():
    """
    Аналог консольной функции show_markets(), но для веб-UI.
    Добавляем БОЛЬШЕ информации по рынкам:
    - Адрес (улица / город / округ / штат / ZIP)
    - Координаты (широта/долгота)
    - Быстрые ссылки (Website/Facebook/Twitter/YouTube/Other)
    - Рейтинг и число отзывов (через подзапросы — без GROUP BY, чтобы код был проще)
    """
    st.header("1. Список рынков")

    # 1) Сколько всего рынков — для пагинации (оставляем логику как в консоли)
    count_sql = "SELECT COUNT(*) FROM markets"
    try:
        total = execute_query(count_sql, fetch=True)[0]["count"]
    except Exception as e:
        st.error(f"Ошибка при получении количества рынков: {e}")
        return

    # 2) Контрол размера страницы + пагинация (наши уже готовые хелперы)
    per_page = _per_page_control(default=10, key_prefix="list")
    offset = st_paginate(total=total, per_page=per_page, key_prefix="list")
    # current_page можно вывести при желании, но это не обязательно
    # current_page = offset // per_page + 1

    # 3) Основной запрос: забираем больше полей из БД.
    #    Рейтинг и кол-во отзывов считаем подзапросами, чтобы не городить GROUP BY на все колонки.
    query = """
        SELECT
            m.id, m.name,
            l.street, l.city, l.county, l.state, l.zip,
            m.website, m.facebook, m.twitter, m.youtube, m.other_media,
            m.latitude, m.longitude,
            COALESCE((SELECT AVG(r.rating) FROM reviews r WHERE r.market_id = m.id), 0) AS avg_rating,
            (SELECT COUNT(r2.id) FROM reviews r2 WHERE r2.market_id = m.id) AS review_count
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        ORDER BY m.id
        LIMIT %s OFFSET %s
    """
    try:
        rows = execute_query(query, (per_page, offset), fetch=True)
    except Exception as e:
        st.error(f"Ошибка при загрузке рынков: {e}")
        return

    if not rows:
        st.info("Больше данных нет для этой страницы.")
        return

    # 4) Шапка с диапазоном показанных записей
    st.subheader(f"Показаны записи с {offset + 1} по {offset + len(rows)} из {total}")

    # 5) Вывод по каждой записи. Делаем простые карточки с рамкой.
    for r in rows:
        # Безопасно достаём и форматируем данные (на случай NULL-ов)
        avg = round(float(r.get("avg_rating") or 0), 1)
        reviews_count = int(r.get("review_count") or 0)

        # Координаты могут быть DECIMAL — конвертируем в float/строку для красивого отображения
        lat = r.get("latitude")
        lon = r.get("longitude")
        lat_str = f"{float(lat):.6f}" if lat is not None else "—"
        lon_str = f"{float(lon):.6f}" if lon is not None else "—"

        street = (r.get("street") or "").strip()
        city = (r.get("city") or "").strip()
        county = (r.get("county") or "").strip()
        state = (r.get("state") or "").strip()
        zip_code = (r.get("zip") or "").strip()

        # Строим человекочитаемую строку адреса
        # Пример: "123 Main St; Portland, Multnomah; OR 97201"
        parts = []
        if street:
            parts.append(street)
        loc_mid = ", ".join([p for p in [city, county] if p])  # "Город, Округ" (без лишних запятых)
        if loc_mid:
            parts.append(loc_mid)
        tail = " ".join([p for p in [state, zip_code] if p])   # "Штат ZIP"
        if tail:
            parts.append(tail)
        address_line = "; ".join(parts) if parts else "—"

        # Ссылки: собираем только те, что есть
        links = []
        if r.get("website"):
            links.append(f"[Website]({r['website']})")
        if r.get("facebook"):
            links.append(f"[Facebook]({r['facebook']})")
        if r.get("twitter"):
            links.append(f"[Twitter]({r['twitter']})")
        if r.get("youtube"):
            links.append(f"[YouTube]({r['youtube']})")
        if r.get("other_media"):
            # other_media может быть не ссылкой — просто покажем как текст
            links.append(f"Other: {r['other_media']}")

        with st.container(border=True):
            # Первая строка — ID + название
            st.write(f"[{r['id']}] {r['name']}")
            # Вторая — адрес
            st.caption(f"{address_line}")
            # Третья — рейтинг/отзывы
            st.write(f"Рейтинг: {avg} | Отзывов: {reviews_count}")
            # Четвёртая — координаты
            st.write(f"Координаты: {lat_str}, {lon_str}")
            # Пятая — быстрые ссылки (если есть хоть одна)
            if links:
                # Используем markdown, чтобы клики были ссылками
                st.markdown(" | ".join(links))



# ------------------------------------------
# 2) Поиск по городу/штату/почтовому индексу
# ------------------------------------------
def search_market_page():
    """
    Веб-версия search_market(): форма ввода (город/штат/индекс),
    кнопка "Искать", результаты с пагинацией.
    """
    st.header("2. Поиск по городу/штату/индексу")

    # Поля формы поиска — как в консоли, но удобнее
    with st.form("search_form", clear_on_submit=False):
        city = st.text_input("Город (Enter — пропустить)", value="")
        state = st.text_input("Штат (Enter — пропустить)", value="")
        zip_code = st.text_input("Индекс (Enter — пропустить)", value="")
        submitted = st.form_submit_button("Искать")

    # Если пользователь ещё не нажал "Искать" — просто объясняем, что делать
    if not submitted and "search_total" not in st.session_state:
        st.info("Заполните одно или несколько полей и нажмите «Искать».")
        return

    # Сохраняем условия последнего поиска в session_state,
    # чтобы кнопки пагинации работали с теми же фильтрами.
    if submitted:
        st.session_state["search_city"] = city
        st.session_state["search_state"] = state
        st.session_state["search_zip"] = zip_code

    # Берём сохранённые условия (или пустые строки, если что-то пошло не так)
    city = st.session_state.get("search_city", "")
    state = st.session_state.get("search_state", "")
    zip_code = st.session_state.get("search_zip", "")

    # Считаем total так же, как в консольной версии
    count_query = """
        SELECT COUNT(*) 
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE (%s = '' OR l.city ILIKE %s)
          AND (%s = '' OR l.state ILIKE %s)
          AND (%s = '' OR l.zip = %s)
    """
    params = (city, f"%{city}%", state, f"%{state}%", zip_code, zip_code)

    try:
        total = execute_query(count_query, params, fetch=True)[0]["count"]
    except Exception as e:
        st.error(f"Ошибка при подсчёте результатов: {e}")
        return

    st.session_state["search_total"] = total  # запомнили total для пагинации

    if total == 0:
        st.warning("Ничего не найдено. Уточните условия.")
        return

    # Пагинация: размер страницы + кнопки
    per_page = _per_page_control(default=10, key_prefix="search")
    offset = st_paginate(total=total, per_page=per_page, key_prefix="search")
    current_page = offset // per_page + 1


    # Основной запрос (как в консольном коде)
    base_query = """
        SELECT m.id, m.name, l.city, l.state, l.zip
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE (%s = '' OR l.city ILIKE %s)
          AND (%s = '' OR l.state ILIKE %s)
          AND (%s = '' OR l.zip = %s)
        ORDER BY m.id
        LIMIT %s OFFSET %s
    """
    query_params = (*params, per_page, offset)

    try:
        rows = execute_query(base_query, query_params, fetch=True)
    except Exception as e:
        st.error(f"Ошибка при загрузке результатов: {e}")
        return

    st.subheader(f"Найдено рынков: {total}")
    for r in rows:
        st.write(f"[{r['id']}] {r['name']} — {r['city']}, {r['state']} ZIP: {r['zip']}")


# -----------------------------
# 3) Детали рынка + отзывы
# -----------------------------
def show_market_details_page():
    """
    Веб-версия show_market_details() с расширенной информацией:
    - Полный адрес (улица/город/округ/штат/ZIP)
    - Координаты (широта/долгота)
    - Соцсети/ссылки
    - Рейтинг и количество отзывов
    - Список категорий рынка
    - Ниже — сами отзывы (как и было)
    """
    st.header("3. Детали рынка")

    # number_input уже гарантирует целое число >= 1
    market_id = st.number_input("Введите ID рынка", min_value=1, step=1, value=1)

    if st.button("Показать"):
        # 1) Детали рынка + адрес + координаты + ссылки
        details_sql = """
            SELECT 
                m.name,
                l.street, l.city, l.county, l.state, l.zip,
                m.website, m.facebook, m.twitter, m.youtube, m.other_media,
                m.latitude, m.longitude
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            WHERE m.id = %s
        """
        try:
            details = execute_query(details_sql, (market_id,), fetch=True)
        except Exception as e:
            st.error(f"Ошибка при получении деталей: {e}")
            return

        if not details:
            st.warning("Рынок не найден.")
            return

        d = details[0]

        # Форматируем адрес в одну аккуратную строку
        street = (d.get("street") or "").strip()
        city = (d.get("city") or "").strip()
        county = (d.get("county") or "").strip()
        state = (d.get("state") or "").strip()
        zip_code = (d.get("zip") or "").strip()

        parts = []
        if street:
            parts.append(street)
        loc_mid = ", ".join([p for p in [city, county] if p])
        if loc_mid:
            parts.append(loc_mid)
        tail = " ".join([p for p in [state, zip_code] if p])
        if tail:
            parts.append(tail)
        address_line = "; ".join(parts) if parts else "—"

        # Координаты: DECIMAL -> str
        lat = d.get("latitude")
        lon = d.get("longitude")
        lat_str = f"{float(lat):.6f}" if lat is not None else "—"
        lon_str = f"{float(lon):.6f}" if lon is not None else "—"

        # Заголовок карточки
        st.subheader(d["name"])
        st.write(f"Адрес: {address_line}")
        st.write(f"Координаты: {lat_str}, {lon_str}")

        # Покажем ссылки (в виде кликабельных Markdown-ссылок, если есть)
        links = []
        if d.get("website"):
            links.append(f"[Website]({d['website']})")
        if d.get("facebook"):
            links.append(f"[Facebook]({d['facebook']})")
        if d.get("twitter"):
            links.append(f"[Twitter]({d['twitter']})")
        if d.get("youtube"):
            links.append(f"[YouTube]({d['youtube']})")
        if d.get("other_media"):
            links.append(f"Other: {d['other_media']}")
        if links:
            st.markdown(" | ".join(links))

        # 2) Рейтинг и число отзывов (отдельный простой запрос)
        try:
            agg = execute_query(
                """
                SELECT 
                    COALESCE(AVG(r.rating), 0) AS avg_rating,
                    COUNT(r.id) AS review_count
                FROM reviews r
                WHERE r.market_id = %s
                """,
                (market_id,),
                fetch=True
            )[0]
            avg = round(float(agg.get("avg_rating") or 0), 1)
            cnt = int(agg.get("review_count") or 0)
            st.write(f"Рейтинг: {avg} | Отзывов: {cnt}")
        except Exception as e:
            st.error(f"Ошибка при расчёте рейтинга: {e}")
            avg, cnt = 0.0, 0

        # 3) Категории рынка (простым списком, через связующую таблицу)
        try:
            cats = execute_query(
                """
                SELECT c.name
                FROM categories c
                JOIN market_categories mc ON mc.category_id = c.id
                WHERE mc.market_id = %s
                ORDER BY c.name
                """,
                (market_id,),
                fetch=True
            )
            if cats:
                names = [ (row.get("name") or "").strip() for row in cats ]
                st.write("Категории: " + ", ".join([n for n in names if n]))
            else:
                st.caption("Категории: нет данных.")
        except Exception as e:
            st.error(f"Ошибка при загрузке категорий: {e}")

        # --- Разделитель перед отзывами ---
        st.markdown("---")
        st.subheader("Отзывы")

        # 4) Сами отзывы — оставляем логику как было (только ORDER BY для стабильности)
        reviews_sql = """
            SELECT id, user_name, rating, review_text
            FROM reviews
            WHERE market_id = %s
            ORDER BY id
        """
        try:
            reviews = execute_query(reviews_sql, (market_id,), fetch=True)
        except Exception as e:
            st.error(f"Ошибка при загрузке отзывов: {e}")
            return

        if not reviews:
            st.caption("Нет отзывов.")
        else:
            for r in reviews:
                user = (r.get("user_name") or "").strip()
                text = (r.get("review_text") or "").strip()
                st.write(f"[{r['id']}] {user} ({r['rating']}): {text}")



# -----------------------------
# 4) Добавление отзыва
# -----------------------------

def add_review_page():
    """
    Страница 'Добавить отзыв' без выпадающих списков.
    Логика:
    1) Пользователь ИЛИ знает ID рынка и вводит его вручную, мы проверяем существование.
    2) ИЛИ выполняет текстовый поиск по названию/городу/штату (одна строка),
       листает результаты (пагинация), жмёт 'Выбрать' → фиксируем выбранный рынок.
    3) После выбора рынка показывается форма добавления отзыва (имя/рейтинг/текст + чекбокс).
    4) INSERT в таблицу reviews.
    """

    st.header("4. Добавить отзыв")

    # --- Блок А. Быстрый ввод по известному ID рынка ---
    with st.expander("Я знаю ID рынка", expanded=False):
        known_id = st.number_input("ID рынка", min_value=1, step=1, value=1, key="addrev_known_id")
        if st.button("Проверить ID", key="addrev_check_id"):
            try:
                row = execute_query(
                    """
                    SELECT m.id, m.name, l.city, l.state
                    FROM markets m
                    JOIN locations l ON m.location_id = l.id
                    WHERE m.id = %s
                    """,
                    (int(known_id),),
                    fetch=True
                )
            except Exception as e:
                st.error(f"Ошибка запроса: {e}")
                row = None

            if row:
                st.session_state["addrev_selected_market"] = int(known_id)
                st.success(f"Рынок найден и выбран: [{row[0]['id']}] {row[0]['name']} — {row[0]['city']}, {row[0]['state']}")
            else:
                st.warning("Рынок с таким ID не найден.")

    # --- Блок B. Поиск рынка по строке (название/город/штат) ---
    st.subheader("Поиск рынка")
    st.caption("Введите часть названия рынка, города или штата. Поиск регистронезависимый.")
    query = st.text_input("Поиск", value=st.session_state.get("addrev_last_query", ""), key="addrev_query_text")

    # Управление размером страницы через уже принятый паттерн
    per_page = _per_page_control(default=10, key_prefix="addrev_search")

    # Ищем только если задан запрос
    rows = []
    total = 0
    if st.button("Найти рынки", key="addrev_do_search"):
        q = (query or "").strip()
        st.session_state["addrev_last_query"] = q  # запомним для пагинации и перерисовок
        if not q:
            st.warning("Введите запрос для поиска.")
        else:
            try:
                # Считаем total
                total = execute_query(
                    """
                    SELECT COUNT(*) 
                    FROM markets m
                    JOIN locations l ON m.location_id = l.id
                    WHERE m.name ILIKE %s OR l.city ILIKE %s OR l.state ILIKE %s
                    """,
                    (f"%{q}%", f"%{q}%", f"%{q}%"),
                    fetch=True
                )[0]["count"]
                st.session_state["addrev_total"] = total
            except Exception as e:
                st.error(f"Ошибка подсчёта результатов: {e}")
                total = 0

    # Если ранее уже искали — восстанавливаем total и query, рисуем пагинацию и результаты
    q = st.session_state.get("addrev_last_query", "")
    total = st.session_state.get("addrev_total", 0) if q else 0

    if q and total > 0:
        current_page = _pager(total=total, per_page=per_page, key_prefix="addrev_search")
        offset = (current_page - 1) * per_page

        try:
            rows = execute_query(
                """
                SELECT m.id, m.name, l.city, l.state
                FROM markets m
                JOIN locations l ON m.location_id = l.id
                WHERE m.name ILIKE %s OR l.city ILIKE %s OR l.state ILIKE %s
                ORDER BY m.name
                LIMIT %s OFFSET %s
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", per_page, offset),
                fetch=True
            )
        except Exception as e:
            st.error(f"Ошибка выборки результатов: {e}")
            rows = []

        if rows:
            st.subheader(f"Найдено рынков: {total}")
            for r in rows:
                # Каждая строка — мини-карточка с кнопкой "Выбрать"
                with st.container(border=True):
                    st.write(f"[{r['id']}] {r['name']} — {r['city']}, {r['state']}")
                    if st.button("Выбрать", key=f"addrev_pick_{r['id']}"):
                        st.session_state["addrev_selected_market"] = int(r["id"])
                        st.success(f"Выбран рынок: [{r['id']}] {r['name']} — {r['city']}, {r['state']}")

    # --- Блок C. Если рынок выбран — показываем форму добавления отзыва ---
    market_id = st.session_state.get("addrev_selected_market")
    if market_id:
        # Подтянем короткую карточку выбранного рынка (на случай, если выбор был по ID)
        try:
            info = execute_query(
                """
                SELECT m.id, m.name, l.city, l.state
                FROM markets m
                JOIN locations l ON m.location_id = l.id
                WHERE m.id = %s
                """,
                (market_id,),
                fetch=True
            )
        except Exception as e:
            st.error(f"Ошибка получения данных о рынке: {e}")
            info = None

        if not info:
            st.warning("Выбранный рынок не найден (возможно, был удалён). Выберите другой.")
            # Сбросим выбор, чтобы не мешало
            st.session_state.pop("addrev_selected_market", None)
            return

        r = info[0]
        st.markdown("---")
        st.subheader("Выбранный рынок")
        st.write(f"[{r['id']}] {r['name']} — {r['city']}, {r['state']}")

        # Форма отзыва
        with st.form("addrev_form", clear_on_submit=True):
            # Имя — можно оставить пустым, тогда будет "Аноним"
            user_name = st.text_input("Ваше имя (опционально)", value="")
            rating = st.slider("Оценка", min_value=1, max_value=5, value=5, step=1)
            review_text = st.text_area("Текст отзыва", height=120, max_chars=1000, placeholder="Коротко опишите впечатления.")
            agree = st.checkbox("Подтверждаю корректность введённых данных")
            submitted = st.form_submit_button("Сохранить отзыв")

        if submitted:
            # Простейшая валидация
            name_clean = (user_name or "").strip() or "Аноним"
            text_clean = (review_text or "").strip()

            if not text_clean:
                st.warning("Поле 'Текст отзыва' не должно быть пустым.")
                return
            if not agree:
                st.warning("Поставьте галочку подтверждения.")
                return

            try:
                execute_query(
                    """
                    INSERT INTO reviews (market_id, user_name, rating, review_text)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (market_id, name_clean, int(rating), text_clean),
                    fetch=False
                )
                st.success("Отзыв успешно сохранён.")
                # Опционально: сбросить выбор рынка после успешной вставки
                # st.session_state.pop("addrev_selected_market", None)
            except Exception as e:
                st.error(f"Не удалось сохранить отзыв: {e}")
    else:
        st.info("Сначала выберите рынок (введите ID или найдите через поиск).")


# -----------------------------
# 5) Удаление отзыва
# -----------------------------

def delete_review_page():
    """
    Страница 'Удалить отзыв' без выпадающих списков, с подробными комментариями.
    Логика максимально простая и быстрая:
    1) Если вы ЗНАЕТЕ ID отзыва — можно удалить напрямую (с подтверждением).
    2) Если ID не знаете — сначала найдите отзыв:
       - фильтр по ID рынка (опционально),
       - строка поиска по имени пользователя и/или тексту отзыва (ILIKE),
       - пагинация результатов,
       - удаление конкретной записи по кнопке с чекбоксом-подтверждением.
    """

    st.header("5. Удалить отзыв")

    # ==============================
    # Блок А. Быстрое удаление по ID
    # ==============================
    with st.expander("Я знаю ID отзыва", expanded=False):
        # number_input гарантирует целое число >= 1
        review_id_direct = st.number_input(
            "ID отзыва",
            min_value=1,
            step=1,
            value=1,
            help="Если вы знаете точный ID отзыва, укажите его здесь.",
            key="delrev_review_id_direct"
        )
        # Чекбокс для подтверждения, чтобы случайно не удалить
        confirm_direct = st.checkbox(
            f"Подтверждаю удаление отзыва #{review_id_direct}",
            key="delrev_confirm_direct"
        )

        # Кнопка удаления по ID
        if st.button("Удалить по ID", key="delrev_delete_by_id"):
            if not confirm_direct:
                st.warning("Поставьте галочку подтверждения перед удалением.")
            else:
                try:
                    # Перед удалением проверим, что отзыв существует — это дружелюбнее для пользователя
                    exists = execute_query(
                        "SELECT id FROM reviews WHERE id = %s",
                        (int(review_id_direct),),
                        fetch=True
                    )
                    if not exists:
                        st.warning("Отзыв с таким ID не найден.")
                    else:
                        # Само удаление — простая команда DELETE по первичному ключу
                        execute_query("DELETE FROM reviews WHERE id = %s", (int(review_id_direct),), fetch=False)
                        st.success(f"Отзыв #{int(review_id_direct)} удалён.")
                except Exception as e:
                    st.error(f"Ошибка удаления: {e}")

    st.markdown("---")

    # ===================================================
    # Блок B. Поиск отзывов (если ID неизвестен или много)
    # ===================================================
    st.subheader("Поиск отзывов")

    # Форма фильтров: ID рынка (опционально) + строка поиска по имени/тексту отзыва
    with st.form("delrev_search_form", clear_on_submit=False):
        market_id = st.number_input(
            "ID рынка (опционально)",
            min_value=0,     # 0 используем как признак "не фильтровать по рынку"
            step=1,
            value=0,
            help="0 — не фильтровать по рынку",
            key="delrev_market_id_input"
        )
        q = st.text_input(
            "Строка поиска (имя пользователя или текст отзыва, опционально)",
            value=st.session_state.get("delrev_q", ""),
            help="Поиск регистронезависимый. Ищем по user_name ИЛИ по review_text.",
            key="delrev_q_input"
        )
        submitted = st.form_submit_button("Искать")

    # Сохраняем состояние фильтров в session_state, чтобы работала пагинация и повторные перерисовки
    if submitted:
        st.session_state["delrev_market_id"] = int(market_id or 0)
        st.session_state["delrev_q"] = (q or "").strip()

    # Достаём текущее состояние фильтров
    market_id = st.session_state.get("delrev_market_id", 0)
    q = st.session_state.get("delrev_q", "")

    # Контрол "сколько строк на странице" — используем наш общий помощник
    per_page = _per_page_control(default=10, key_prefix="delrev")

    # Если пользователь ничего не задал — просто подсказка
    if (market_id == 0) and (not q):
        st.info("Укажите ID рынка и/или строку поиска, затем нажмите «Искать».")
        return

    # Собираем WHERE-условие максимально просто и прозрачно
    where_clauses = []   # сюда добавляем кусочки условий
    params = []          # а сюда соответствующие параметры для cur.execute

    if market_id > 0:
        where_clauses.append("r.market_id = %s")
        params.append(market_id)

    if q:
        # Ищем в user_name ИЛИ в review_text (ILIKE — регистронезависимое)
        where_clauses.append("(r.user_name ILIKE %s OR r.review_text ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    # Склеиваем WHERE, если есть хотя бы одно условие
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # 1) Считаем общее количество подходящих отзывов — это нужно для пагинации
    try:
        count_sql = f"SELECT COUNT(*) FROM reviews r {where_sql}"
        total = execute_query(count_sql, tuple(params), fetch=True)[0]["count"]
    except Exception as e:
        st.error(f"Ошибка подсчёта результатов: {e}")
        return

    if total == 0:
        st.warning("Ничего не найдено по заданным условиям.")
        return

    # 2) Рисуем пагинацию (кнопки Назад/Вперёд) и вычисляем OFFSET
    current_page = _pager(total=total, per_page=per_page, key_prefix="delrev")
    offset = (current_page - 1) * per_page

    # 3) Выбираем страницу отзывов с краткой карточкой рынка (чтобы понять, где отзыв)
    try:
        rows = execute_query(
            f"""
            SELECT r.id, r.market_id, r.user_name, r.rating, r.review_text,
                   m.name AS market_name, l.city, l.state
            FROM reviews r
            JOIN markets m ON m.id = r.market_id
            JOIN locations l ON l.id = m.location_id
            {where_sql}
            ORDER BY r.id DESC
            LIMIT %s OFFSET %s
            """,
            tuple(params) + (per_page, offset),
            fetch=True
        )
    except Exception as e:
        st.error(f"Ошибка выборки данных: {e}")
        return

    st.subheader(f"Найдено отзывов: {total}")

    # 4) Рисуем карточки результатов — простым текстом
    for r in rows:
        rid = r["id"]
        mid = r["market_id"]
        uname = (r.get("user_name") or "").strip()
        rating = int(r.get("rating") or 0)
        text = (r.get("review_text") or "").strip()

        # Делаем короткий превью текста, чтобы карточка не была слишком длинной
        text_preview = text if len(text) <= 200 else text[:200] + "..."

        # Контейнер с рамкой — визуально отделяем каждую карточку
        with st.container(border=True):
            st.write(f"**Отзыв #{rid}**  |  Рынок: [{mid}] {r.get('market_name')} — {r.get('city')}, {r.get('state')}")
            st.write(f"Пользователь: {uname}  |  Оценка: {rating}")
            st.write(f"Текст: {text_preview}")

            # Две колонки: слева чекбокс подтверждения, справа кнопка удаления
            cols = st.columns([1, 1])
            with cols[0]:
                confirm = st.checkbox(
                    f"Подтверждаю удаление #{rid}",
                    key=f"delrev_confirm_{rid}"
                )
            with cols[1]:
                if st.button("Удалить", key=f"delrev_delete_{rid}"):
                    if not confirm:
                        st.warning(f"Поставьте галочку подтверждения для отзыва #{rid}.")
                    else:
                        try:
                            execute_query("DELETE FROM reviews WHERE id = %s", (rid,), fetch=False)
                            st.success(f"Отзыв #{rid} удалён.")
                            # Перерисовываем страницу, чтобы карточка сразу исчезла из списка
                        except Exception as e:
                            st.error(f"Ошибка удаления #{rid}: {e}")


# -----------------------------
# 6) Сортировка рынков
# -----------------------------
def sort_markets_page():
    """
    Веб-версия sort_markets(): выбор критерия и направления, пагинация.
    """
    st.header("6. Сортировка рынков")

    # Критерий сортировки (как в консоли)
    sort_choice = st.selectbox(
        "Сортировать по",
        options=[
            ("По рейтингу", "rating"),
            ("По городу", "city"),
            ("По штату", "state"),
            ("По расстоянию", "distance"),
        ],
        format_func=lambda x: x[0],
        index=0
    )
    direction = st.radio("Направление", options=[("Возрастание", "ASC"), ("Убывание", "DESC")],
                         index=0, horizontal=True, format_func=lambda x: x[0])[1]

    # Если нужен расчёт расстояния — запросим координаты
    lat, lon = None, None
    if sort_choice[1] == "distance":
        st.info("Для сортировки по расстоянию введите координаты точки.")
        lat = st.text_input("Широта", value="")
        lon = st.text_input("Долгота", value="")
        # Проверим координаты (как в консольной функции через validate_coordinates)
        coords = validate_coordinates(lat.strip(), lon.strip())
        if not coords:
            st.warning("Введите корректные координаты (пример: 45.52 и -122.67).")
            return
        lat, lon = coords

    # Общее количество (как в консоли)
    if sort_choice[1] == "distance":
        total_sql = """
            SELECT COUNT(*) FROM markets
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
    else:
        total_sql = "SELECT COUNT(*) FROM markets"

    try:
        total = execute_query(total_sql, fetch=True)[0]["count"]
    except Exception as e:
        st.error(f"Ошибка при подсчёте: {e}")
        return

    # Параметры страницы
    per_page = _per_page_control(default=10, key_prefix="sort")
    offset = st_paginate(total=total, per_page=per_page, key_prefix="sort")
    current_page = offset // per_page + 1


    # Собираем SQL под выбранный вариант (в точности как в консоли)
    if sort_choice[1] == "rating":
        order_clause = f"ORDER BY avg_rating {direction}"
        query = f"""
            SELECT m.id, m.name, l.city, l.state, COALESCE(AVG(r.rating), 0) AS avg_rating
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            LEFT JOIN reviews r ON r.market_id = m.id
            GROUP BY m.id, l.city, l.state
            {order_clause}
            LIMIT %s OFFSET %s
        """
        params = (per_page, offset)

    elif sort_choice[1] == "city":
        order_clause = f"ORDER BY l.city {direction}"
        query = f"""
            SELECT m.id, m.name, l.city, l.state
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            {order_clause}
            LIMIT %s OFFSET %s
        """
        params = (per_page, offset)

    elif sort_choice[1] == "state":
        order_clause = f"ORDER BY l.state {direction}"
        query = f"""
            SELECT m.id, m.name, l.city, l.state
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            {order_clause}
            LIMIT %s OFFSET %s
        """
        params = (per_page, offset)

    else:  # distance
        order_clause = f"ORDER BY distance {direction}"
        query = f"""
            SELECT m.id, m.name, l.city, l.state,
            (3959 * acos(
                cos(radians({lat})) * cos(radians(m.latitude)) *
                cos(radians(m.longitude) - radians({lon})) +
                sin(radians({lat})) * sin(radians(m.latitude))
            )) AS distance
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            WHERE m.latitude IS NOT NULL AND m.longitude IS NOT NULL
            {order_clause}
            LIMIT %s OFFSET %s
        """
        params = (per_page, offset)

    try:
        rows = execute_query(query, params, fetch=True)
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        return

    # Вывод
    for r in rows:
        if "avg_rating" in r:
            st.write(f"[{r['id']}] {r['name']} — {r['city']}, {r['state']} | Рейтинг: {round(float(r['avg_rating'] or 0), 1)}")
        elif "distance" in r:
            st.write(f"[{r['id']}] {r['name']} — {r['city']}, {r['state']} | {round(float(r['distance'] or 0), 2)} миль")
        else:
            st.write(f"[{r['id']}] {r['name']} — {r['city']}, {r['state']}")


# -----------------------------
# 7) Поиск по радиусу (30 миль)
# -----------------------------
def search_by_radius_page():
    """
    Веб-версия search_by_radius(): берём координаты, выводим до 20 рынков в радиусе 30 миль.
    """
    st.header("7. Поиск по радиусу (30 миль)")

    lat = st.text_input("Широта", value="")
    lon = st.text_input("Долгота", value="")

    coords = validate_coordinates(lat.strip(), lon.strip())
    if not coords:
        st.info("Введите корректные координаты и нажмите кнопку ниже.")
        if st.button("Показать рынки"):
            st.warning("Координаты некорректны.")
        return

    if st.button("Показать рынки"):
        lat, lon = coords
        query = """
            SELECT m.id, m.name, l.city, l.state,
            (3959 * acos(
                cos(radians(%s)) * cos(radians(m.latitude)) *
                cos(radians(m.longitude) - radians(%s)) +
                sin(radians(%s)) * sin(radians(m.latitude))
            )) AS distance
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            WHERE (3959 * acos(
                cos(radians(%s)) * cos(radians(m.latitude)) *
                cos(radians(m.longitude) - radians(%s)) +
                sin(radians(%s)) * sin(radians(m.latitude))
            )) < 30
            ORDER BY distance ASC
            LIMIT 20
        """
        params = (lat, lon, lat, lat, lon, lat)

        try:
            rows = execute_query(query, params, fetch=True)
        except Exception as e:
            st.error(f"Ошибка запроса: {e}")
            return

        if not rows:
            st.warning("В радиусе 30 миль рынков не найдено.")
            return

        st.subheader("Рынки в радиусе 30 миль:")
        for r in rows:
            st.write(f"[{r['id']}] {r['name']} — {r['city']}, {r['state']} | {round(float(r['distance'] or 0), 2)} миль")


# -----------------------------
# 8) Удаление рынка
# -----------------------------
def delete_market_page():
    """
    Веб-версия delete_market(): вводим ID, подтверждаем, удаляем.
    """
    st.header("8. Удалить рынок")

    market_id = st.number_input("ID рынка", min_value=1, step=1, value=1)
    confirm = st.checkbox(f"Я подтверждаю удаление рынка #{market_id}")

    if st.button("Удалить"):
        if not confirm:
            st.warning("Поставьте галочку подтверждения.")
            return
        try:
            execute_query("DELETE FROM markets WHERE id = %s", (market_id,))
        except Exception as e:
            st.error(f"Ошибка удаления: {e}")
            return
        st.success(f"Рынок #{market_id} удалён.")




# -----------------------------
# 9) Показать рынки по категории
# -----------------------------

def render_markets_by_category():
    """
    Раздел "Показать рынки по категории".
    Сценарий работы:
    1) Загружаем список категорий из БД (id, name), сортируем по алфавиту.
    2) Даём поле быстрого поиска по категориям (текстовый фильтр).
    3) Даём выбор категории (selectbox) из отфильтрованного списка.
    4) По выбранной категории выводим таблицу рынков (ID, Название, Город, Штат) с простой пагинацией.
    
    """

    # Заголовок раздела в интерфейсе
    st.header("Показать рынки по категории")

    # --- 1. Загружаем список категорий из базы данных ---
    # Пишем простой SQL-запрос: хотим получить id и name из таблицы categories.
    # ORDER BY name — отсортируем категории по алфавиту.
    categories = execute_query(
        """
        SELECT id, name
        FROM categories
        ORDER BY name;
        """,
        (),  # параметры запроса пустые
        fetch=True  # fetch=True означает "вернуть данные" (список строк)
    )

    # Если категорий нет — сообщим пользователю и завершим
    if not categories:
        st.info("Категории не найдены в базе данных.")
        return

    # --- 2. Поле быстрого поиска по категориям ---
    # Это обычный текстовый input. Пользователь вводит часть названия,
    # мы локально фильтруем список категорий в памяти (без повторного запроса в БД).
    search_text = st.text_input(
        "Быстрый поиск категории по названию",
        value="",
        help="Введите часть названия категории, чтобы быстро отфильтровать список."
    ).strip().lower()

    # Локальная фильтрация: если поле пустое — берём все категории,
    # иначе — оставляем только те, в названии которых есть введённый текст
    if search_text:
        filtered_categories = []
        for c in categories:
            # аккуратно берём имя, на случай если оно вдруг NULL в БД
            name = (c.get("name") or "").lower()
            if search_text in name:
                filtered_categories.append(c)
    else:
        filtered_categories = categories

    # Если после фильтра ничего не осталось — сообщим об этом
    if not filtered_categories:
        st.warning("По вашему фильтру категорий не найдено.")
        return

    # --- 3. Виджет выбора категории ---
    # Для удобства пользователю показываем выпадающий список (selectbox)
    # уже отфильтрованных категорий. Элементов обычно не очень много.
    # Если у вас вдруг тысячи категорий — можно будет заменить на автокомплит,
    # но сейчас оставляем простой вариант + наш текстовый фильтр выше.
    category_names = [c.get("name") or f"Категория #{c.get('id')}" for c in filtered_categories]
    selected_name = st.selectbox(
        "Выберите категорию",
        options=category_names,
        index=0
    )

    # По выбранному названию найдём сам объект категории (чтобы получить её id)
    selected_category = None
    for c in filtered_categories:
        if (c.get("name") or f"Категория #{c.get('id')}") == selected_name:
            selected_category = c
            break

    if not selected_category:
        st.error("Не удалось определить выбранную категорию.")
        return

    category_id = selected_category["id"]

    # --- 4. Загружаем рынки для выбранной категории (с пагинацией через SQL LIMIT/OFFSET) ---
    # Сначала узнаём, сколько всего рынков подходит под выбранную категорию — это нужно для пагинации.
    try:
        total = execute_query(
            """
            SELECT COUNT(*)
            FROM markets m
            JOIN market_categories mc ON mc.market_id = m.id
            JOIN categories c        ON c.id = mc.category_id
            WHERE c.id = %s
            """,
            (category_id,),
            fetch=True
        )[0]["count"]
    except Exception as e:
        st.error(f"Ошибка при подсчёте рынков: {e}")
        return

    # Покажем итоговое количество найденных рынков
    st.write(f"Найдено рынков: **{total}**")

    if total == 0:
        st.info("В этой категории пока нет рынков.")
        return

    # --- 5. Контрол «сколько строк на странице» + универсальный пагинатор ---
    # Храним состояние отдельно для каждой выбранной категории, чтобы переключение категорий
    # не мешало пагинации (ключ включает ID категории).
    key_prefix = f"cat_{category_id}"

    # Простое числовое поле для выбора размера страницы (5..100 шагом 5)
    per_page = _per_page_control(default=10, key_prefix=key_prefix)

    # Универсальная пагинация: рисует кнопки/номер страницы и возвращает OFFSET для SQL
    offset = st_paginate(total=total, per_page=per_page, key_prefix=key_prefix)
    current_page = offset // per_page + 1  # вычисляем номер текущей страницы для подписи

    # --- 6. Загружаем текущую страницу рынков по категории ---
    try:
        page_rows = execute_query(
            """
            SELECT m.id,
                   m.name,
                   l.city,
                   l.state
            FROM markets m
            JOIN market_categories mc ON mc.market_id = m.id
            JOIN categories c        ON c.id = mc.category_id
            JOIN locations l         ON l.id = m.location_id
            WHERE c.id = %s
            ORDER BY m.name
            LIMIT %s OFFSET %s
            """,
            (category_id, per_page, offset),
            fetch=True
        )
    except Exception as e:
        st.error(f"Ошибка при загрузке рынков: {e}")
        return

    # --- 7. Готовим простую «таблицу-список» ---
    # Преобразуем строки в список словарей с русскими заголовками.
    table_rows = []
    for row in page_rows:
        table_rows.append({
            "ID": row.get("id"),
            "Рынок": row.get("name") or "",
            "Город": row.get("city") or "",
            "Штат": row.get("state") or ""
        })

    # Выводим таблицу без технического индекса (только наши колонки ID, Рынок, Город, Штат).
    st.dataframe(table_rows, hide_index=True)


    # Подпись о текущей странице (подтягиваем общее число страниц через «потолок»)
    total_pages = max(1, math.ceil(total / max(1, per_page)))
    st.caption(f"Страница {current_page} из {total_pages} (показаны {len(page_rows)} записей)")
