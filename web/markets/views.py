# web/markets/views.py

from math import ceil

from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from .db import execute_query
from .utils import validate_coordinates
from django.db import connection  # даёт доступ к "сырым" SQL-запросам
import json  # нужен для превращения Python-списков в JSON для JS в шаблоне
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib.auth.models import Group  # нужен, чтобы добавить нового юзера в группу "Пользователи"
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User

from django.http import JsonResponse  # ← добавь этот импорт наверху файла


def is_admin(user):
    """
    Простой помощник: возвращает True, если пользователь:
    - суперпользователь (is_superuser), ИЛИ
    - состоит в группе "Администраторы".
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name="Администраторы").exists()


# ---------------------------------------------
# Саморегистрация пользователя
# ---------------------------------------------
def register(request):
    """
    Простая форма саморегистрации.
    Новый пользователь автоматически попадает в группу "Пользователи".
    """
    if request.method == "POST":
        # Создаём форму на основе присланных данных
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Сохраняем пользователя в БД
            user = form.save()  # по умолчанию Django создаёт is_active=True, is_staff=False, is_superuser=False

            # --- Автодобавление в группу "Пользователи" ---
            # Пояснение: если группы нет, создаём её на лету, чтобы не падать на пустой базе.
            users_group, _ = Group.objects.get_or_create(name="Пользователи")
            user.groups.add(users_group)  # добавляем пользователя в группу
            user.save()  # сохраняем изменения по пользователю (на всякий случай)

            # --- Автовход можно включить одной строкой (по желанию) ---
            # from django.contrib.auth import login as auth_login
            # auth_login(request, user)  # если раскомментировать — сразу залогинит нового пользователя

            # После успешной регистрации отправляем на страницу логина,
            # чтобы пользователь сам вошёл под своими новыми данными.
            return redirect("login")
    else:
        # Если GET-запрос — показываем пустую форму регистрации
        form = CustomUserCreationForm()

    # Рендерим шаблон регистрации с формой (ошибки формы тоже попадут сюда автоматически)
    return render(request, "register.html", {"form": form})


@login_required  # ← ДОБАВИЛИ: требуем вход для главной страницы
def dashboard_home(request):
    """
    Этот view рендерит главную страницу-дэшборд.
    Здесь мы считаем 4 простых KPI и два набора данных для графиков:
    1) ТОП-10 штатов по числу рынков (бар-чарт)
    2) Распределение рынков по категориям (pie) через market_categories
    """

    # Вспомогательная функция: вернуть одно целое число (например, COUNT(*))
    def fetch_one_value(sql: str) -> int:
        # Открываем соединение и выполняем запрос
        with connection.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()  # ожидаем одну строку, вида (123,)
        # Если строка есть — берём первый столбец, иначе 0
        return int(row[0]) if row and row[0] is not None else 0

    # Вспомогательная функция: вернуть все строки как список словарей
    def fetch_all_dicts(sql: str):
        # Выполняем запрос
        with connection.cursor() as cur:
            cur.execute(sql)
            cols = [c[0] for c in cur.description] if cur.description else []
            rows = cur.fetchall()
        # Собираем список словарей вида [{"state": "CA", "markets_count": 123}, ...]
        result = []
        for r in rows:
            item = {}
            for i, v in enumerate(r):
                item[cols[i]] = v
            result.append(item)
        return result

    # -------- KPI (4 счётчика) --------
    total_markets = fetch_one_value("SELECT COUNT(*) FROM markets;")                       # всего рынков
    total_reviews = fetch_one_value("SELECT COUNT(*) FROM reviews;")                       # всего отзывов
    states_count  = fetch_one_value("SELECT COUNT(DISTINCT state) FROM locations;")        # штатов в базе
    cities_count  = fetch_one_value("SELECT COUNT(DISTINCT city) FROM locations;")         # городов в базе

    # -------- График 1: ТОП-10 штатов по числу рынков (бар-чарт) --------
    # Логика: соединяем markets с locations по location_id и считаем рынки по state.
    rows_states = fetch_all_dicts("""
        SELECT l.state AS state, COUNT(m.id) AS markets_count
        FROM markets m
        JOIN locations l ON l.id = m.location_id
        GROUP BY l.state
        ORDER BY COUNT(m.id) DESC
        LIMIT 10;
    """)
    # Два параллельных списка: подписи (штаты) и значения (кол-во рынков)
    top_states_labels = json.dumps([(r["state"] or "—") for r in rows_states], ensure_ascii=False)
    top_states_values = json.dumps([int(r["markets_count"] or 0) for r in rows_states])

    # -------- График 2: Распределение рынков по категориям (pie) --------
    # Логика: таблица связей market_categories (market_id, category_id).
    # COUNT(mc.market_id) = сколько рынков относится к категории.
    rows_cat = fetch_all_dicts("""
        SELECT c.name AS category, COUNT(mc.market_id) AS markets_count
        FROM categories c
        JOIN market_categories mc ON mc.category_id = c.id
        GROUP BY c.name
        ORDER BY COUNT(mc.market_id) DESC, c.name ASC
        LIMIT 10;
    """)
    cat_labels = json.dumps([(r["category"] or "—") for r in rows_cat], ensure_ascii=False)
    cat_values = json.dumps([int(r["markets_count"] or 0) for r in rows_cat])

    # Передаём всё в шаблон
    context = {
        # KPI
        "total_markets": total_markets,
        "total_reviews": total_reviews,
        "states_count":  states_count,
        "cities_count":  cities_count,

        # Данные для графиков (как JSON-строки для безопасной вставки в атрибуты)
        "top_states_labels": top_states_labels,
        "top_states_values": top_states_values,
        "cat_labels": cat_labels,
        "cat_values": cat_values,
    }
    
    return render(request, "home.html", context)

# ---------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ---------------------------

def _get_int(request: HttpRequest, name: str, default: int, min_v: int, max_v: int) -> int:
    """
    Читаем целое из query (?page=..&per=..). Если не число — берём default.
    Ограничиваем диапазон значений.
    """
    raw = request.GET.get(name, None) or request.POST.get(name, None)
    try:
        val = int(raw)
    except (TypeError, ValueError):
        val = default
    # принудительно зажимаем значение в допустимые границы
    val = max(min_v, min(val, max_v))
    return val

def _paginate(total: int, per_page: int, page: int) -> dict:
    """
    Считаем параметры пагинации и offset — полностью аналогично Streamlit-логике,
    где мы работали с offset = (page-1)*per_page.
    """
    # Кол-во страниц: ceil(total / per_page), но минимум 1
    pages = max(1, ceil(max(0, total) / max(1, per_page)))
    # Текущую страницу зажимаем в 1..pages
    page = max(1, min(page, pages))
    # Смещение для SQL LIMIT/OFFSET
    offset = (page - 1) * per_page
    return {
        "total": total,          # всего записей
        "per_page": per_page,    # сколько на страницу
        "page": page,            # текущая страница (1..pages)
        "pages": pages,          # всего страниц
        "offset": offset,        # смещение (как в Streamlit)
        "has_prev": page > 1,
        "has_next": page < pages,
        "prev_page": page - 1 if page > 1 else 1,
        "next_page": page + 1 if page < pages else pages,
    }
    

def build_pagination_context(request, total: int, default_per: int = 10, min_per: int = 5, max_per: int = 100):
    """
    Универсальный хелпер для пагинации.
    Возвращает словарь с полями:
      page, pages, per, per_options, has_prev, has_next, prev_page, next_page, offset
    """
    per = _get_int(request, "per", default=default_per, min_v=min_per, max_v=max_per)
    page = _get_int(request, "page", default=1, min_v=1, max_v=10**9)

    p = _paginate(total, per, page)

    return {
        "page": p["page"],
        "pages": p["pages"],
        "per": p["per_page"],
        "per_options": [5, 10, 15, 20, 50, 100],
        "has_prev": p["has_prev"],
        "has_next": p["has_next"],
        "prev_page": p["prev_page"],
        "next_page": p["next_page"],
        "offset": p["offset"],
    }

# ---------------------------
# 1) СПИСОК РЫНКОВ
# ---------------------------

def markets_list(request: HttpRequest) -> HttpResponse:
    """
    Django-версия списка рынков (адаптация Streamlit-функции).
    Пагинация через build_pagination_context + универсальный шаблон.
    """

    # 1) Считаем общее количество рынков
    total_row = execute_query("SELECT COUNT(*) FROM markets", fetch=True)[0]
    total = int(total_row.get("count") or 0)

    # 2) Строим словарь пагинации
    pagination = build_pagination_context(request, total, default_per=15)

    # 3) Основной запрос — отдаём поля
    rows = execute_query(
        """
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
        """,
        (pagination["per"], pagination["offset"]),
        fetch=True,
    ) or []

    # 4) Подготовка данных (как раньше)
    prepared = []
    for r in rows:
        avg = round(float(r.get("avg_rating") or 0), 1)
        reviews_count = int(r.get("review_count") or 0)

        lat = r.get("latitude")
        lon = r.get("longitude")
        lat_str = f"{float(lat):.6f}" if lat is not None else "—"
        lon_str = f"{float(lon):.6f}" if lon is not None else "—"

        street   = (r.get("street") or "").strip()
        city     = (r.get("city") or "").strip()
        county   = (r.get("county") or "").strip()
        state    = (r.get("state") or "").strip()
        zip_code = (r.get("zip") or "").strip()

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

        links = []
        if r.get("website"): links.append(str(r["website"]))
        if r.get("facebook"): links.append(str(r["facebook"]))
        if r.get("twitter"): links.append(str(r["twitter"]))
        if r.get("youtube"): links.append(str(r["youtube"]))
        if r.get("other_media"): links.append(str(r["other_media"]))
        links_str = " | ".join(links) if links else "—"

        prepared.append({
            "id": r["id"],
            "name": r["name"],
            "address_line": address_line,
            "avg_rating": avg,
            "review_count": reviews_count,
            "lat_str": lat_str,
            "lon_str": lon_str,
            "links_str": links_str,
        })

    # 5) Диапазон строк "с N по M из T"
    row_from = (pagination["offset"] + 1) if total > 0 else 0
    row_to   = pagination["offset"] + len(prepared)

    # 6) Контекст в шаблон
    ctx = {
        "rows": prepared,
        "total": total,
        "row_from": row_from,
        "row_to": row_to,
    }
    ctx.update(pagination)  # сюда добавятся page, pages, per, per_options и т.д.

    return render(request, "list.html", ctx)

# ---------------------------
# 2) ПОИСК
# ---------------------------
def markets_search(request: HttpRequest) -> HttpResponse:
    """
    Поиск по городу/штату/ZIP: форма GET (city/state/zip) + пагинация.
    SQL адаптирован из Streamlit-версии без изменений логики.
    """
    city = (request.GET.get("city") or "").strip()
    state = (request.GET.get("state") or "").strip()
    zip_code = (request.GET.get("zip") or "").strip()

    # total
    total = execute_query(
        """
        SELECT COUNT(*) 
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE (%s = '' OR l.city ILIKE %s)
          AND (%s = '' OR l.state ILIKE %s)
          AND (%s = '' OR l.zip = %s)
        """,
        (city, f"%{city}%", state, f"%{state}%", zip_code, zip_code),
        fetch=True
    )[0]["count"]

    per_page = _get_int(request, "per", default=10, min_v=5, max_v=100)
    page = _get_int(request, "page", default=1, min_v=1, max_v=10**9)
    p = _paginate(total, per_page, page)
    
    # Формируем окно страниц (±2 от текущей)
    win = 2
    start = max(1, p["page"] - win)
    end = min(p["pages"], p["page"] + win)
    page_window = list(range(start, end + 1))

    # Варианты "на страницу"
    per_options = [10, 15, 20, 50, 100]

    rows = []
    if total > 0:
        rows = execute_query(
            """
            SELECT m.id, m.name, l.city, l.state, l.zip
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            WHERE (%s = '' OR l.city ILIKE %s)
              AND (%s = '' OR l.state ILIKE %s)
              AND (%s = '' OR l.zip = %s)
            ORDER BY m.id
            LIMIT %s OFFSET %s
            """,
            (city, f"%{city}%", state, f"%{state}%", zip_code, zip_code, p["per_page"], p["offset"]),
            fetch=True
        )

    pagination = build_pagination_context(request, total, default_per=10)
    ctx = {
        "rows": rows,
        "city": city,
        "state": state,
        "zip": zip_code,
    }
    ctx.update(pagination)
    return render(request, "markets_search.html", ctx)

# ---------------------------
# 3) ДЕТАЛИ РЫНКА
# ---------------------------

def market_details(request: HttpRequest) -> HttpResponse:
    """
    Одна страница: форма для ввода ID рынка + вывод деталей.
    Если id не передан или рынок не найден — показываем сообщение.
    """
    id_str = (request.GET.get("id") or "").strip()
    market_id = int(id_str) if id_str.isdigit() else None

    context = {"market_id": market_id, "not_found": False}

    if market_id:
        # Загружаем основные данные
        details = execute_query(
            """
            SELECT 
                m.name,
                l.street, l.city, l.county, l.state, l.zip,
                m.website, m.facebook, m.twitter, m.youtube, m.other_media,
                m.latitude, m.longitude
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            WHERE m.id = %s
            """,
            (market_id,),
            fetch=True
        )
        if not details:
            context["not_found"] = True
        else:
            d = details[0]

            # Рейтинг
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
            avg_rating = round(float(agg.get("avg_rating") or 0), 1)
            review_count = int(agg.get("review_count") or 0)

            # Категории
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

            # Отзывы
            reviews = execute_query(
                """
                SELECT id, user_name, rating, review_text
                FROM reviews
                WHERE market_id = %s
                ORDER BY id
                """,
                (market_id,),
                fetch=True
            )

            context.update({
                "d": d,
                "avg_rating": avg_rating,
                "review_count": review_count,
                "cats": cats,
                "reviews": reviews,
            })

    return render(request, "details.html", context)


# ---------------------------
# 4) ДОБАВИТЬ ОТЗЫВ
# ---------------------------

@login_required  # только для вошедших
def add_review(request: HttpRequest) -> HttpResponse:
    """
    Два пути:
    1) Знаем ID рынка — вводим и проверяем.
    2) Не знаем — ищем по подстроке (название/город/штат), листаем, выбираем рынок.
    После выбора рынка — форма отзыва (имя/оценка/текст + подтверждение).
    """
    ctx = {}

    # A) Быстрая проверка рынка по ID (через GET или POST)
    if request.method == "POST" and request.POST.get("action") == "check_id":
        try:
            known_id = int(request.POST.get("known_id", "0"))
        except ValueError:
            known_id = 0

        if known_id > 0:
            row = execute_query(
                """
                SELECT m.id, m.name, l.city, l.state
                FROM markets m
                JOIN locations l ON m.location_id = l.id
                WHERE m.id = %s
                """,
                (known_id,),
                fetch=True
            )
            if row:
                ctx["selected_market"] = row[0]  # словарь с id/name/city/state
            else:
                ctx["error_check_id"] = "Рынок с таким ID не найден."
        else:
            ctx["error_check_id"] = "Введите корректный ID (> 0)."

    # B) Поиск рынка по строке (название/город/штат)
    q = (request.GET.get("q") or "").strip()
    ctx["q"] = q

    per_page = _get_int(request, "per", default=10, min_v=5, max_v=100)
    page = _get_int(request, "page", default=1, min_v=1, max_v=10**9)

    total = 0
    rows = []
    if q:
        # Счётчик
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

        p = _paginate(total, per_page, page)
        ctx["p"] = p

        if total > 0:
            rows = execute_query(
                """
                SELECT m.id, m.name, l.city, l.state
                FROM markets m
                JOIN locations l ON m.location_id = l.id
                WHERE m.name ILIKE %s OR l.city ILIKE %s OR l.state ILIKE %s
                ORDER BY m.name
                LIMIT %s OFFSET %s
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", p["per_page"], p["offset"]),
                fetch=True
            )

    ctx["rows"] = rows
    ctx["total"] = total
    ctx["per"] = per_page

    # C) Если выбрали рынок из списка (кнопка "Выбрать")
    if request.method == "POST" and request.POST.get("action") == "pick_market":
        try:
            pick_id = int(request.POST.get("pick_id", "0"))
        except ValueError:
            pick_id = 0
        if pick_id > 0:
            info = execute_query(
                """
                SELECT m.id, m.name, l.city, l.state
                FROM markets m
                JOIN locations l ON m.location_id = l.id
                WHERE m.id = %s
                """,
                (pick_id,),
                fetch=True
            )
            if info:
                ctx["selected_market"] = info[0]
            else:
                ctx["error_pick"] = "Выбранный рынок не найден."

    # D) Сохранение отзыва
    if request.method == "POST" and request.POST.get("action") == "save_review":
        try:
            market_id = int(request.POST.get("market_id", "0"))
        except ValueError:
            market_id = 0
        user_name = request.user.username  # сохраняем реального автора из Django User
        review_text = (request.POST.get("review_text") or "").strip()
        try:
            rating = int(request.POST.get("rating", "5"))
        except ValueError:
            rating = 5
        agree = (request.POST.get("agree") == "on")

        if market_id <= 0:
            ctx["error_save"] = "Не выбран рынок."
        elif not review_text:
            ctx["error_save"] = "Поле «Текст отзыва» обязательно."
        elif not (1 <= rating <= 5):
            ctx["error_save"] = "Оценка должна быть от 1 до 5."
        elif not agree:
            ctx["error_save"] = "Поставьте галочку подтверждения."
        else:
            # Вставляем отзыв
            user_id = request.user.id if request.user.is_authenticated else None
            execute_query(
                """
                INSERT INTO reviews (market_id, user_name, rating, review_text, user_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (market_id, user_name, rating, review_text, user_id),
                fetch=False
            )
            # Редиректим на детали рынка — так исключаем повторную отправку формы F5
            return redirect(f"{reverse('markets:details')}?id={market_id}")

    return render(request, "add_review.html", ctx)


# ---------------------------
# 5) УДАЛИТЬ ОТЗЫВ
# ---------------------------

@login_required
def delete_review(request: HttpRequest) -> HttpResponse:
    """
    Только автор своего отзыва или администратор может удалить.
    """
    ctx = {}

    # A) Удаление по известному ID
    if request.method == "POST" and request.POST.get("action") == "delete_by_id":
        try:
            review_id = int(request.POST.get("review_id", "0"))
        except ValueError:
            review_id = 0
        confirm = (request.POST.get("confirm") == "on")
        if review_id <= 0:
            ctx["error_direct"] = "Введите корректный ID отзыва."
        elif not confirm:
            ctx["error_direct"] = "Поставьте галочку подтверждения."
        else:
            # --- ДОБАВЛЯЕМ выбор автора отзыва ---
            row = execute_query(
                "SELECT id, user_name FROM reviews WHERE id = %s",
                (review_id,),
                fetch=True
            )
            if not row:
                ctx["error_direct"] = "Отзыв с таким ID не найден."
            else:
                # -----------------------------------------------
                # НОВАЯ ПРОВЕРКА ПРАВ ДЛЯ МОДЕРАЦИИ ОТЗЫВОВ
                # 1) Разрешаем удалять, если:
                #    - у пользователя есть кастомное право 'markets.can_moderate_reviews', ИЛИ
                #    - пользователь суперпользователь, ИЛИ
                #    - пользователь является автором этого отзыва (по имени)
                # 2) Дополнительно проверим user_id в БД, если он у отзыва есть
                # -----------------------------------------------
                can_moderate = request.user.has_perm('markets.can_moderate_reviews')  # проверяем кастомное право
                author = (row[0].get("user_name") or "").strip()  # имя автора из БД (колонка user_name)

                if can_moderate or request.user.is_superuser or request.user.username == author:
                    # Страхуемся: сверяем, не чужой ли это отзыв по user_id
                    review = execute_query(
                        "SELECT user_id FROM reviews WHERE id = %s",
                        (review_id,),
                        fetch=True
                    )
                    if not review:
                        ctx["error_direct"] = "Отзыв не найден."
                    else:
                        # Если у отзыва есть user_id, и это НЕ наш id, и мы НЕ модератор/не суперюзер — запрещаем
                        uid = review[0].get("user_id")
                        if (uid is not None) and (uid != request.user.id) and not (can_moderate or request.user.is_superuser):
                            ctx["error_direct"] = "Вы не можете удалить чужой отзыв."
                        else:
                            # Всё ок — удаляем
                            execute_query("DELETE FROM reviews WHERE id = %s", (review_id,), fetch=False)
                            ctx["success_direct"] = f"Отзыв #{review_id} удалён."
                else:
                    ctx["error_direct"] = "Недостаточно прав для удаления этого отзыва."



    # B) Поиск отзывов
    try:
        market_id = int(request.GET.get("market_id", "0"))
    except ValueError:
        market_id = 0
    q = (request.GET.get("q") or "").strip()

    where_clauses = []
    params = []
    if market_id > 0:
        where_clauses.append("r.market_id = %s")
        params.append(market_id)
    if q:
        where_clauses.append("(r.user_name ILIKE %s OR r.review_text ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    total = 0
    per_page = _get_int(request, "per", default=10, min_v=5, max_v=100)
    page = _get_int(request, "page", default=1, min_v=1, max_v=10**9)

    # Считаем total
    total = execute_query(f"SELECT COUNT(*) FROM reviews r {where_sql}", tuple(params), fetch=True)[0]["count"]
    p = _paginate(total, per_page, page)

    rows = []
    if total > 0:
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
            tuple(params) + (p["per_page"], p["offset"]),
            fetch=True
        )

    ctx.update({
        "market_id": market_id,
        "q": q,
        "total": total,
        "p": p,
        "rows": rows,
        "per": per_page,
    })

    # C) Удаление конкретной записи из таблицы результатов
    if request.method == "POST" and request.POST.get("action") == "delete_one":
        try:
            rid = int(request.POST.get("rid", "0"))
        except ValueError:
            rid = 0
        confirm_row = (request.POST.get("confirm_row") == "on")
        if rid <= 0:
            ctx["error_row"] = "Некорректный ID."
        elif not confirm_row:
            ctx["error_row"] = "Поставьте галочку подтверждения."
        else:
            # --- ДОБАВЛЯЕМ выбор автора отзыва ---
            row = execute_query(
                "SELECT id, user_name FROM reviews WHERE id = %s",
                (rid,),
                fetch=True
            )
            if not row:
                ctx["error_row"] = "Отзыв не найден."
            else:
                # Разрешаем удаление, если есть право модерации, либо суперюзер, либо автор отзыва
                can_moderate = request.user.has_perm('markets.can_moderate_reviews')
                author = (row[0].get("user_name") or "").strip()

                if can_moderate or request.user.is_superuser or request.user.username == author:
                    execute_query("DELETE FROM reviews WHERE id = %s", (rid,), fetch=False)
                    # Перенаправляем обратно на ту же страницу со старыми параметрами
                    return redirect(f"{reverse('delete_review')}?...")  # оставь свой существующий redirect
                else:
                    ctx["error_row"] = "Недостаточно прав для удаления этого отзыва."



    # После удаления перенаправляем обратно на страницу деталей или отзывов
    return redirect(request.META.get("HTTP_REFERER", reverse("markets:reviews")))



def reviews_page(request: HttpRequest) -> HttpResponse:
    """
    Единая страница для работы с отзывами:
    - поиск рынка по ID или строке (name/city/state/zip)
    - добавление нового отзыва
    - удаление существующих отзывов
    """
    context = {"selected_market": None, "reviews": [], "error": None}
    q = (request.GET.get("q") or "").strip()
    market_id = request.GET.get("id")

    # --- Поиск рынка по ID ---
    if market_id:
        details = execute_query(
            """
            SELECT m.id, m.name, l.city, l.state, l.zip
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            WHERE m.id = %s
            """,
            (market_id,),
            fetch=True
        )
        if details:
            context["selected_market"] = details[0]
        else:
            context["error"] = f"Рынок с ID {market_id} не найден"

    # --- Поиск по строке ---
    elif q:
    # Поиск по строке
        rows = execute_query(
            """
            SELECT m.id, m.name, l.city, l.state, l.zip
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            WHERE m.name ILIKE %s OR l.city ILIKE %s OR l.state ILIKE %s OR l.zip::text ILIKE %s
            ORDER BY m.name
            LIMIT 20
            """,
            (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
            fetch=True
        )
        context["rows"] = rows
        context["q"] = q

    else:
        # Если нет ни id, ни q — показываем рынки с пагинацией
        total_row = execute_query("SELECT COUNT(*) FROM markets", fetch=True)[0]
        total = int(total_row.get("count") or 0)

        per_page = _get_int(request, "per", default=10, min_v=5, max_v=100)
        page = _get_int(request, "page", default=1, min_v=1, max_v=10**9)

        p = _paginate(total, per_page, page)

        rows = execute_query(
            """
            SELECT m.id, m.name, l.city, l.state, l.zip
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            ORDER BY m.id
            LIMIT %s OFFSET %s
            """,
            (p["per_page"], p["offset"]),
            fetch=True,
        )

        # Окно страниц (±2 вокруг текущей)
        win = 2
        start = max(1, p["page"] - win)
        end = min(p["pages"], p["page"] + win)
        page_window = list(range(start, end + 1))

        context.update({
            "rows": rows,
            "p": p,
            "total": total,
            "page_window": page_window,
            "per_options": [10, 15, 20, 50, 100],  # варианты "на страницу" для select
        })



    # --- Обработка POST ---
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add":
            market_id = request.POST.get("market_id")
            user_name = request.POST.get("user_name") or "Аноним"
            rating = int(request.POST.get("rating") or 5)
            review_text = request.POST.get("review_text") or ""

            if not review_text.strip():
                context["error"] = "Текст отзыва не может быть пустым"
            else:
                execute_query(
                    "INSERT INTO reviews (market_id, user_name, rating, review_text) VALUES (%s, %s, %s, %s)",
                    (market_id, user_name, rating, review_text)
                )
                return redirect(f"{reverse('markets:reviews')}?id={market_id}")

        elif action == "delete":
            review_id = request.POST.get("review_id")
            market_id = request.POST.get("market_id")

            # Проверяем, что отзыв существует
            review = execute_query(
                "SELECT user_id, user_name FROM reviews WHERE id = %s",
                (review_id,),
                fetch=True
            )

            if not review:
                context["error"] = "Отзыв не найден."
            else:
                author_id = review[0].get("user_id")
                author_name = review[0].get("user_name")
                user = request.user

                # Проверяем права
                if user.is_authenticated and (user.is_staff or user.is_superuser or author_id == user.id):
                    execute_query("DELETE FROM reviews WHERE id = %s", (review_id,), fetch=False)
                    return redirect(f"{reverse('markets:reviews')}?id={market_id}")
                else:
                    context["error"] = "Вы не можете удалить чужой отзыв."


    # --- Если рынок выбран, подтягиваем отзывы ---
    if context.get("selected_market"):
        market_id = context["selected_market"]["id"]
        reviews = execute_query(
            """
            SELECT id, user_name, rating, review_text
            FROM reviews
            WHERE market_id = %s
            ORDER BY id DESC
            """,
            (market_id,),
            fetch=True
        )
        context["reviews"] = reviews

    return render(request, "reviews.html", context)


 

# ===========================================
# 6) СОРТИРОВКА РЫНКОВ
# ===========================================
def sort_markets(request: HttpRequest) -> HttpResponse:
    """
    Сортировка рынков по выбранному полю и направлению.
    Поля: rating, city, state.
    Направления: asc (возрастание), desc (убывание).
    """

    # Читаем параметры из GET
    field = (request.GET.get("field") or "rating").strip()
    direction = (request.GET.get("direction") or "desc").strip().lower()

    per = _get_int(request, "per", default=10, min_v=5, max_v=100)
    page = _get_int(request, "page", default=1, min_v=1, max_v=10**9)

    # Общая SELECT-часть
    base_select = """
        SELECT
            m.id, m.name,
            l.city, l.state, l.zip,
            m.latitude, m.longitude,
            COALESCE((SELECT AVG(r.rating) FROM reviews r WHERE r.market_id = m.id), 0) AS avg_rating,
            (SELECT COUNT(r2.id) FROM reviews r2 WHERE r2.market_id = m.id) AS review_count
        FROM markets m
        JOIN locations l ON m.location_id = l.id
    """

    # ORDER BY
    if field == "city":
        order_sql = f"ORDER BY l.city {'ASC' if direction=='asc' else 'DESC'}, m.id ASC"
    elif field == "state":
        order_sql = f"ORDER BY l.state {'ASC' if direction=='asc' else 'DESC'}, m.id ASC"
    else:
        # по умолчанию рейтинг
        order_sql = f"ORDER BY avg_rating {'ASC' if direction=='asc' else 'DESC'}, review_count DESC, m.id ASC"

    # total
    count_sql = "SELECT COUNT(*) FROM markets m JOIN locations l ON m.location_id = l.id"
    total = execute_query(count_sql, fetch=True)[0]["count"]

    pages = max(1, ceil(max(0, total) / max(1, per)))
    page = min(page, pages)
    offset = (page - 1) * per

    sql = f"""
        {base_select}
        {order_sql}
        LIMIT %s OFFSET %s
    """
    rows = execute_query(sql, (per, offset), fetch=True) if total > 0 else []

    # Пагинация через универсальный хелпер
    pagination = build_pagination_context(request, total, default_per=10)

    # Собираем строку sort для шаблона (например rating_desc, city_asc и т.п.)
    sort = f"{field}_{direction}"

    ctx = {
        "rows": rows,
        "field": field,
        "direction": direction,
        "sort": sort,
    }
    ctx.update(pagination)
    return render(request, "sort.html", ctx)



# ===========================================
# 7) ПОИСК РЫНКОВ В РАДИУСЕ
# ===========================================
def search_by_radius(request: HttpRequest) -> HttpResponse:
    """
    Полный аналог Streamlit-раздела «Поиск по радиусу N миль от координат».
    - Вводим lat/lon и radius (в милях).
    - Валидируем координаты.
    - Считаем расстояние до каждого рынка (где координаты заданы), фильтруем по radius.
    - Пагинируем результат и сортируем по возрастанию дистанции.
    """

    # 1) Читаем входные параметры
    lat_input = request.GET.get("lat", "")
    lon_input = request.GET.get("lon", "")
    radius_str = request.GET.get("radius", "30")   # по умолчанию 30 миль
    per_str = request.GET.get("per", "10")
    page_str = request.GET.get("page", "1")

    # 2) Валидируем координаты
    coords = validate_coordinates(lat_input, lon_input)
    if not coords:
        # Координаты некорректны — отрисуем форму с сообщением
        return render(request, "radius.html", {
            "rows": [],
            "lat": lat_input,
            "lon": lon_input,
            "radius": radius_str,
            "per": 10,
            "page": 1,
            "pages": 1,
            "total": 0,
        })
    lat0, lon0 = coords

    # 3) Парсим радиус/страницу
    try:
        radius = max(0.1, float(radius_str.replace(",", ".")))
    except ValueError:
        radius = 30.0
    try:
        per = max(5, min(int(per_str), 100))
    except ValueError:
        per = 10
    try:
        page = max(1, int(page_str))
    except ValueError:
        page = 1

    # 4) Готовим выражение distance (мили), как и в sort_markets
    distance_expr = f"""
        2 * 3959 * ASIN(
            SQRT(
                POWER(SIN((({lat0} - m.latitude) * pi()/180.0)/2), 2) +
                COS(m.latitude * pi()/180.0) * COS({lat0} * pi()/180.0) *
                POWER(SIN((({lon0} - m.longitude) * pi()/180.0)/2), 2)
            )
        )
    """

    # 5) Считаем total (сколько рынков попадает в радиус)
    total_sql = f"""
        SELECT COUNT(*)
        FROM markets m
        WHERE m.latitude IS NOT NULL AND m.longitude IS NOT NULL
          AND {distance_expr} <= %s
    """
    total = execute_query(total_sql, (radius,), fetch=True)[0]["count"]

    # 6) Пагинация
    from math import ceil
    pages = max(1, ceil(max(0, total) / max(1, per)))
    page = min(page, pages)
    offset = (page - 1) * per

    # 7) Выборка текущей страницы (отсортировано по distance ASC)
    rows_sql = f"""
        SELECT
            m.id, m.name,
            {distance_expr} AS distance_miles,
            l.city, l.state, l.zip,
            m.latitude, m.longitude
        FROM markets m
        JOIN locations l ON l.id = m.location_id
        WHERE m.latitude IS NOT NULL AND m.longitude IS NOT NULL
          AND {distance_expr} <= %s
        ORDER BY distance_miles ASC, m.id ASC
        LIMIT %s OFFSET %s
    """
    rows = execute_query(rows_sql, (radius, per, offset), fetch=True) if total > 0 else []
    
    # Окно номеров страниц вокруг текущей (±2)
    win = 2
    start = max(1, page - win)
    end = min(pages, page + win)
    page_window = list(range(start, end + 1))


    return render(request, "radius.html", {
        "rows": rows,
        "lat": lat_input,
        "lon": lon_input,
        "radius": radius,
        "per": per,
        "page": page,
        "pages": pages,
        "total": total,
        "page_window": page_window,
        "error": "",
        "per_options": [10, 15, 20, 50, 100],  # варианты "на страницу" для select
    })


# ===========================================
# 8) УДАЛЕНИЕ РЫНКОВ
# ===========================================
@login_required  # требуем вход
@permission_required('markets.can_delete_market', raise_exception=True)  # требуем право на удаление рынка
def delete_market(request: HttpRequest) -> HttpResponse:
    """
    Удаление рынков — доступно только тем, у кого есть право 'markets.can_delete_market'.
    Если права нет — будет 403 (raise_exception=True).
    """
    ctx = {}

    # --- A) Удаление по ID ---
    if request.method == "POST" and request.POST.get("action") == "delete_by_id":
        try:
            market_id = int(request.POST.get("market_id", "0"))
        except ValueError:
            market_id = 0
        confirm = (request.POST.get("confirm") == "on")

        if market_id <= 0:
            ctx["error_direct"] = "Введите корректный ID (> 0)."
        elif not confirm:
            ctx["error_direct"] = "Поставьте галочку подтверждения."
        else:
            exists = execute_query("SELECT id FROM markets WHERE id = %s", (market_id,), fetch=True)
            if not exists:
                ctx["error_direct"] = f"Рынок с ID {market_id} не найден."
            else:
                # Сначала удаляем все зависимые записи (отзывы и связи категорий)
                execute_query("DELETE FROM reviews WHERE market_id = %s", (market_id,), fetch=False)
                execute_query("DELETE FROM market_categories WHERE market_id = %s", (market_id,), fetch=False)
                execute_query("DELETE FROM markets WHERE id = %s", (market_id,), fetch=False)
                ctx["success_direct"] = f"Рынок #{market_id} и связанные данные удалены."

    # --- B) Поиск и пагинация ---
    q = (request.GET.get("q") or "").strip()
    where, params = "", []
    if q:
        where = "WHERE (m.name ILIKE %s OR l.city ILIKE %s OR l.state ILIKE %s)"
        params = [f"%{q}%", f"%{q}%", f"%{q}%"]

    total = execute_query(
        f"SELECT COUNT(*) FROM markets m JOIN locations l ON l.id = m.location_id {where}",
        tuple(params),
        fetch=True
    )[0]["count"]

    pagination = build_pagination_context(request, total, default_per=10)

    rows = []
    if total > 0:
        rows = execute_query(
            f"""
            SELECT m.id, m.name, l.city, l.state, l.zip
            FROM markets m
            JOIN locations l ON l.id = m.location_id
            {where}
            ORDER BY m.id
            LIMIT %s OFFSET %s
            """,
            tuple(params) + (pagination["per"], pagination["offset"]),
            fetch=True
        )

    ctx.update({
        "q": q,
        "rows": rows,
        "total": total,
    })
    ctx.update(pagination)

    # --- C) Удаление строки из таблицы ---
    if request.method == "POST" and request.POST.get("action") == "delete_one":
        try:
            rid = int(request.POST.get("rid", "0"))
        except ValueError:
            rid = 0
        confirm_row = (request.POST.get("confirm_row") == "on")

        if rid <= 0:
            ctx["error_row"] = "Некорректный ID."
        elif not confirm_row:
            ctx["error_row"] = "Поставьте галочку подтверждения."
        else:
            execute_query("DELETE FROM reviews WHERE market_id = %s", (rid,), fetch=False)
            execute_query("DELETE FROM market_categories WHERE market_id = %s", (rid,), fetch=False)
            execute_query("DELETE FROM markets WHERE id = %s", (rid,), fetch=False)
            return redirect(f"{reverse('markets:delete_market')}?q={q}&page={pagination['page']}&per={pagination['per']}")

    return render(request, "delete_market.html", ctx)


# ---------------------------
# 9) Рынки по категориям
# ---------------------------

def markets_by_category(request: HttpRequest) -> HttpResponse:
    """
    Полный аналог Streamlit-функции render_markets_by_category:
    1) Загружаем все категории (id, name), сортируем по алфавиту.
    2) Текстовый фильтр по именам категорий (локально).
    3) Выбор категории (по category_id) через GET.
    4) Считаем COUNT рынков по выбранной категории.
    5) Берём страницу (LIMIT/OFFSET) и рендерим таблицу.
    """
    # 1) Загружаем категории из БД
    categories = execute_query(
        """
        SELECT id, name
        FROM categories
        ORDER BY name
        """,
        fetch=True
    ) or []

    # 2) Текстовый фильтр по GET ?q=
    q = (request.GET.get("q") or "").strip().lower()
    if q:
        categories_filtered = [c for c in categories if q in (c.get("name") or "").lower()]
    else:
        categories_filtered = categories

    # если категорий нет — отрендерим страницу без таблицы
    if not categories:
        return render(request, "by_category.html", {
            "categories": [],
            "categories_filtered": [],
            "q": q,
            "selected_id": 0,
            "total": 0,
            "rows": [],
            "per": 10,
            "page": 1,
            "pages": 1,
            "has_prev": False,
            "has_next": False,
            "prev_page": 1,
            "next_page": 1,
            "per_options": [5, 10, 15, 20, 50, 100],
        })

    # 3) Читаем параметры category_id, per, page
    def _get_int_from_get(name: str, default: int, lo: int, hi: int) -> int:
        raw = request.GET.get(name)
        try:
            v = int(raw)
        except (TypeError, ValueError):
            v = default
        return max(lo, min(v, hi))

    selected_id = _get_int_from_get(
        "category_id",
        default=(categories_filtered[0]["id"] if categories_filtered else 0),
        lo=0,
        hi=10**9,
    )
    per = _get_int_from_get("per", default=10, lo=5, hi=100)
    page = _get_int_from_get("page", default=1, lo=1, hi=10**9)

    total = 0
    rows = []

    if selected_id > 0:
        # 4) COUNT(*) рынков по категории
        total = execute_query(
            """
            SELECT COUNT(*)
            FROM markets m
            JOIN market_categories mc ON mc.market_id = m.id
            WHERE mc.category_id = %s
            """,
            (selected_id,),
            fetch=True
        )[0]["count"]

        # 5) LIMIT/OFFSET
        p = _paginate(total, per, page)
        rows = execute_query(
            """
            SELECT m.id, m.name, l.city, l.state
            FROM markets m
            JOIN market_categories mc ON mc.market_id = m.id
            JOIN locations l ON l.id = m.location_id
            WHERE mc.category_id = %s
            ORDER BY m.name
            LIMIT %s OFFSET %s
            """,
            (selected_id, p["per_page"], p["offset"]),
            fetch=True
        ) or []
    else:
        p = _paginate(0, per, page)

    # финальный render
    return render(request, "by_category.html", {
        "categories": categories,
        "categories_filtered": categories_filtered,
        "q": q,
        "selected_id": selected_id,
        "rows": rows,
        "total": total,
        "per": p["per_page"],
        "page": p["page"],
        "pages": p["pages"],
        "has_prev": p["has_prev"],
        "has_next": p["has_next"],
        "prev_page": p["prev_page"],
        "next_page": p["next_page"],
        "per_options": [5, 10, 15, 20, 50, 100],
    })


