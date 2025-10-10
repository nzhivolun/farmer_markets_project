# web/markets/utils.py

# ============================================================
# validate_coordinates — простая проверка широты/долготы.
# Возвращает кортеж (lat, lon) как float, либо None если некорректно.
# Это перенос базовой логики из app.utils.validate_coordinates.
# ============================================================

from typing import Optional, Tuple

def validate_coordinates(lat_str: str, lon_str: str) -> Optional[Tuple[float, float]]:
    # Удаляем пробелы по краям на всякий случай
    lat_str = (lat_str or "").strip()
    lon_str = (lon_str or "").strip()

    if not lat_str or not lon_str:
        return None

    try:
        lat = float(lat_str.replace(",", "."))
        lon = float(lon_str.replace(",", "."))
    except ValueError:
        # Не удалось привести строку к числу
        return None

    # Проверим допустимый диапазон координат
    if not (-90.0 <= lat <= 90.0):
        return None
    if not (-180.0 <= lon <= 180.0):
        return None

    return (lat, lon)
