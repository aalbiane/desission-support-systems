"""Модуль запросов: список запросов к Wolfram Alpha."""

# Каждый запрос: (категория, текст запроса).
# Первые 10 запросов - обязательные по заданию, последние 5 - по выбору.
QUERIES = [
    ("Математический расчет", "integrate x^2 sin^3 x dx"),
    ("Фактологический запрос", "population of Russia 2024"),
    ("Химический расчет", "molar mass of H2SO4"),
    ("Физический расчет", "kinetic energy of 5kg object at 10m/s"),
    ("Географический", "distance between Moscow and Saint Petersburg"),
    ("Финансовый", "100 USD to RUB"),
    ("Временной", "current time in Kazan"),
    ("Астрономический", "distance to Mars"),
    ("Медицинский", "body mass index 180cm 75kg"),
    ("Лингвистический", "translate hello to Russian"),
    # --- 5 запросов по выбору ---
    ("Алгебра (по выбору)", "solve x^2 - 5x + 6 = 0"),
    ("Химия (по выбору)", "boiling point of ethanol"),
    ("Питание (по выбору)", "calories in 100g banana"),
    ("География (по выбору)", "height of Mount Elbrus"),
    ("Физика (по выбору)", "speed of light in km/h"),
]
