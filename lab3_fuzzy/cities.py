"""Справочник городов и экспертные знания о климате (из задания)."""

# Категориальные цвета городов на графиках (порядок фиксирован)
CITIES = {
    "Kazan": {
        "name_ru": "Казань", "lat": 55.7887, "lon": 49.1221, "wmo": 27595,
        "color": "#2a78d6",
        "climate": "Умеренно-континентальный климат с морозной зимой и "
                   "умеренно жарким летом.",
    },
    "Moscow": {
        "name_ru": "Москва", "lat": 55.7558, "lon": 37.6173, "wmo": 27612,
        "color": "#eb6834",
        "climate": "Умеренно-континентальный климат с тенденцией к "
                   "субтропическому типу летом.",
    },
    "Saint Petersburg": {
        "name_ru": "Санкт-Петербург", "lat": 59.9343, "lon": 30.3351, "wmo": 26063,
        "color": "#1baf7a",
        "climate": "Морской климат с чертами континентального, частая смена "
                   "воздушных масс.",
    },
}

SEASONS = ["winter", "spring", "summer", "autumn"]
SEASON_RU = {"winter": "зима", "spring": "весна", "summer": "лето", "autumn": "осень"}
SEASON_RU_GEN = {"winter": "зимы", "spring": "весны", "summer": "лета", "autumn": "осени"}


def get_season(month):
    """Определение сезона по номеру месяца."""
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"
