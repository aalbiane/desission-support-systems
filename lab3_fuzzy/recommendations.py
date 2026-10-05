"""Этап 6. Формирование рекомендаций по результатам нечёткого анализа."""


def generate_recommendations(city, season, current, comfort_score, comfort_level,
                             anomalies):
    """Возвращает список текстовых рекомендаций."""
    temp = current["temperature"]
    humidity = current["humidity"]
    wind = current["wind_speed"]
    rec = []

    # 1. По итоговому уровню комфорта (результат нечёткого вывода)
    if comfort_level == "good":
        rec.append("Погода комфортная: подходящее время для прогулок.")
    elif comfort_level == "medium":
        rec.append("Комфорт средний: одевайтесь по погоде, длительные прогулки "
                   "лучше сократить.")
    else:
        rec.append("Комфорт низкий: по возможности ограничьте время на улице.")

    # 2. По выявленным аномалиям
    for a in anomalies:
        if a["status"] == "в пределах нормы":
            continue
        rec.append(f"{a['parameter']} {a['direction']} для сезона "
                   f"({a['status']}, z = {a['z']:+.2f}).")
        if a["key"] == "temperature" and a["z"] < -1:
            rec.append("Холоднее обычного: наденьте дополнительный тёплый слой.")
        if a["key"] == "temperature" and a["z"] > 1 and season == "summer":
            rec.append("Жарче обычного: пейте больше воды, избегайте солнца днём.")

    # 3. Специфические рекомендации городов (экспертные знания)
    if city == "Kazan":
        if season == "winter" and temp < -15:
            rec.append("Сильный мороз: в разных районах города температура может "
                       "отличаться до 5 °C, утром особенно холодно.")
        if wind > 10:
            rec.append("Порывистый ветер: держитесь дальше от деревьев и "
                       "рекламных конструкций.")
    elif city == "Moscow":
        if season == "summer" and temp > 23:
            rec.append("Волна жары: в историческом центре жарче из-за недостатка "
                       "зелени, выбирайте парки.")
        if humidity > 85 and wind > 8:
            rec.append("Возможен шквал с ливнем: возьмите зонт, не паркуйтесь "
                       "под деревьями.")
    elif city == "Saint Petersburg":
        if humidity > 85 and temp < 5:
            rec.append("Сыро и холодно: непромокаемая одежда обязательна.")
        if wind > 10:
            rec.append("Сильный ветер: в прибрежных районах ветер сильнее.")

    # 4. Общие рекомендации
    if wind > 15:
        rec.append("Очень сильный ветер: уберите лёгкие вещи с балкона.")
    if humidity < 30:
        rec.append("Низкая влажность: увлажняйте кожу, пейте воду.")
    if humidity > 85:
        rec.append("Высокая влажность: возможны осадки.")
    if -3 < temp <= 2:
        rec.append("Температура около нуля: возможен гололёд.")
    return rec
