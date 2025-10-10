# web/markets/db.py

# ============================================================
# Простой хелпер для выполнения SQL-запросов в Django.
# Мы намеренно делаем интерфейс очень похожим на app.db.execute_query:
#   execute_query(sql: str, params: tuple = (), fetch: bool = False) -> list[dict] | None
# - Если fetch=True, вернём список словарей (строки из БД).
# - Если fetch=False, просто выполним запрос (INSERT/UPDATE/DELETE) и вернём None.
#
# Это позволит переносить логику из Streamlit (ui_markets_streamlit.py) практически без изменений.
# ============================================================

from typing import Iterable, List, Dict, Optional, Tuple
from django.db import connection

def execute_query(sql: str, params: Iterable = (), fetch: bool = False) -> Optional[List[Dict]]:
    """
    Унифицированный вызов SQL:
    - sql     — строка SQL с плейсхолдерами %s
    - params  — кортеж/список параметров
    - fetch   — если True, вернуть данные как список словарей (имя_колонки -> значение)
    """
    # Открываем курсор через django.db.connection — соединение управляет Django.
    with connection.cursor() as cur:
        # Выполняем запрос с параметрами (даже если params пуст)
        cur.execute(sql, tuple(params))
        if not fetch:
            # Если нам не нужны результаты — просто выходим, коммит сделает Django автоматически
            return None

        # Если нужны строки — получаем имена колонок и строки, формируем список словарей
        columns = [col[0] for col in cur.description]
        rows = cur.fetchall()
        result: List[Dict] = []
        for row in rows:
            # Склеиваем имена колонок и значения в словарь
            d = {}
            for idx, col in enumerate(columns):
                d[col] = row[idx]
            result.append(d)
        return result
