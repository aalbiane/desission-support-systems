"""Лабораторная работа №3. Экспертная система на основе нечёткой логики
для анализа погодных условий Казани, Москвы и Санкт-Петербурга.

Запуск:  python main.py
"""
import configparser
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from cities import CITIES, SEASON_RU, get_season
from climate import (archive_annual_means, archive_monthly_norm,
                     calculate_seasonal_norms, detect_anomalies, load_archive)
from fuzzy_system import TERMS_RU, WeatherFuzzySystem
from linguistic import numeric_to_linguistic
from recommendations import generate_recommendations
from visualization import (plot_comfort, plot_membership,
                           plot_seasonal_profiles, plot_trends)
from weather_api import get_current_weather, get_historical_weather

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"


class Tee:
    """Дублирует вывод программы на экран и в текстовый файл отчёта."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def read_config():
    """Читает API-ключ и число лет истории из config.ini."""
    parser = configparser.ConfigParser()
    if not parser.read(BASE_DIR / "config.ini", encoding="utf-8"):
        sys.exit("Не найден config.ini. Скопируйте config.example.ini и впишите ключ.")
    api_key = parser.get("openweathermap", "api_key", fallback="").strip()
    if not api_key or api_key == "YOUR_API_KEY":
        sys.exit("В config.ini не указан api_key (раздел [openweathermap]).")
    return api_key, parser.getint("history", "years", fallback=5)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)

    api_key, years = read_config()
    RESULTS_DIR.mkdir(exist_ok=True)
    report_file = open(RESULTS_DIR / "report.txt", "w", encoding="utf-8")
    sys.stdout = Tee(sys.stdout, report_file)

    now = datetime.now()
    season = get_season(now.month)
    print("ЭКСПЕРТНАЯ СИСТЕМА НЕЧЁТКОГО АНАЛИЗА ПОГОДЫ")
    print(f"Дата и время запуска: {now:%d.%m.%Y %H:%M}")

    # ---- [1] Исторические данные (Open-Meteo) ----
    print(f"\n[1] Загрузка исторических данных за {years} лет (Open-Meteo)...")
    history = {}
    for city, info in CITIES.items():
        df = get_historical_weather(city, info["lat"], info["lon"], years)
        if df is None or df.empty:
            sys.exit(f"Нет исторических данных для {city}, работа остановлена.")
        history[city] = df
        print(f"  {info['name_ru']}: {len(df)} записей "
              f"({df['date'].min():%d.%m.%Y} - {df['date'].max():%d.%m.%Y})")

    # ---- [2] Сезонные климатические нормы ----
    print("\n[2] Расчёт сезонных климатических норм...")
    norms = {city: calculate_seasonal_norms(df) for city, df in history.items()}
    norms_table = pd.concat(norms, names=["city", "season"]).reset_index()
    print(norms_table.to_string(index=False))
    norms_table.to_csv(RESULTS_DIR / "seasonal_norms.csv", index=False,
                       encoding="utf-8-sig")

    # ---- Многолетний архив метеостанций (температура с 1881 г.) ----
    archive = load_archive()
    print(f"\n    Многолетняя норма температуры месяца (архив, 1991-2020), "
          f"месяц {now.month}:")
    month_norm = {}
    for city, info in CITIES.items():
        month_norm[city] = archive_monthly_norm(archive, info["wmo"], now.month)
        print(f"  {info['name_ru']}: {month_norm[city]:+.1f} °C")

    # ---- [3] Текущая погода (OpenWeatherMap) ----
    print(f"\n[3] Получение текущих данных (OpenWeatherMap)...")
    print(f"Текущий сезон: {season} ({SEASON_RU[season]})")
    current = {}
    for city, info in CITIES.items():
        data = get_current_weather(city, api_key)
        if data:
            current[city] = data
            print(f"  {info['name_ru']}: {data['temperature']:.1f} °C, "
                  f"{data['description']}, влажность {data['humidity']}%, "
                  f"ветер {data['wind_speed']:.1f} м/с")
    if not current:
        sys.exit("Не удалось получить текущую погоду ни для одного города.")

    # ---- [4]-[6] Нечёткий анализ по каждому городу ----
    results = []
    for city, data in current.items():
        info = CITIES[city]
        row = norms[city].loc[season]
        print(f"\n--- Анализ для города {info['name_ru']} ---")
        print(f"Климат: {info['climate']}")
        print(f"Сейчас: температура {data['temperature']:.1f} °C "
              f"(ощущается как {data['feels_like']:.1f} °C), "
              f"влажность {data['humidity']}%, ветер {data['wind_speed']:.1f} м/с")
        print(f"Сезонная норма ({SEASON_RU[season]}): "
              f"{row['temperature_mean']:.1f} ± {row['temperature_std']:.1f} °C, "
              f"влажность {row['humidity_mean']:.0f}%, "
              f"ветер {row['wind_speed_mean']:.1f} м/с")

        # Нечёткая система города: термы температуры строятся от сезонной нормы
        system = WeatherFuzzySystem(city, season, row["temperature_mean"],
                                    row["temperature_std"])

        # [4] Фаззификация и лингвистические значения
        degrees = system.fuzzify(data["temperature"], data["humidity"],
                                 data["wind_speed"])
        labels = {}
        print("Лингвистические переменные:")
        for var, title in (("temperature", "Температура"),
                           ("humidity", "Влажность"), ("wind", "Ветер")):
            labels[var], detail = numeric_to_linguistic(degrees[var], var, season)
            print(f"  {title}: {labels[var]}  [{detail}]")

        # [5] Нечёткий вывод Мамдани
        score, level = system.evaluate(data["temperature"], data["humidity"],
                                       data["wind_speed"])
        level_ru = TERMS_RU["comfort"][level]
        print(f"Правил в базе: {len(system.rules)}")
        print(f"Уровень комфорта: {score:.1f} из 100 ({level_ru})")

        # [6] Аномалии и рекомендации
        anomalies = detect_anomalies(data, norms[city], season)
        print("Сравнение с сезонной нормой:")
        for a in anomalies:
            print(f"  {a['parameter']}: {a['value']:.1f} при норме {a['norm']:.1f} "
                  f"(z = {a['z']:+.2f}) - {a['status']}")
        deviation = data["temperature"] - month_norm[city]
        print(f"  Отклонение от многолетней нормы месяца: {deviation:+.1f} °C")

        recommendations = generate_recommendations(city, season, data, score,
                                                   level, anomalies)
        print("Рекомендации:")
        for text in recommendations:
            print(f"  - {text}")

        plot_membership(system, data, score,
                        RESULTS_DIR / f"membership_{city.replace(' ', '_')}.png")
        results.append({
            "city": city, "Город": info["name_ru"],
            "Температура, °C": round(data["temperature"], 1),
            "Влажность, %": data["humidity"],
            "Ветер, м/с": round(data["wind_speed"], 1),
            "Температура (линг.)": labels["temperature"],
            "Влажность (линг.)": labels["humidity"],
            "Ветер (линг.)": labels["wind"],
            "comfort_score": score, "comfort_level_ru": level_ru,
            "Комфорт, баллы": score, "Уровень комфорта": level_ru,
            "Аномалии": "; ".join(f"{a['parameter'].lower()} {a['direction']}"
                                  for a in anomalies
                                  if a["status"] != "в пределах нормы") or "нет",
            "Рекомендации": " ".join(recommendations),
        })
        last_system = system

    # ---- [7] Итоговая таблица и графики ----
    print("\n[7] Итоговая таблица")
    table = pd.DataFrame(results).drop(
        columns=["city", "comfort_score", "comfort_level_ru"])
    print(table.drop(columns=["Рекомендации"]).to_string(index=False))
    table.to_csv(RESULTS_DIR / "results.csv", index=False, encoding="utf-8-sig")

    print("\nБаза правил (пример для города "
          f"{CITIES[last_system.city]['name_ru']}):")
    for i, text in enumerate(last_system.rule_texts, 1):
        print(f"  {i}. {text}")

    plot_seasonal_profiles(norms, RESULTS_DIR / "seasonal_profiles.png")
    annual = {city: archive_annual_means(archive, info["wmo"])
              for city, info in CITIES.items()}
    plot_trends(annual, RESULTS_DIR / "trends.png")
    plot_comfort(results, RESULTS_DIR / "comfort.png")
    print(f"\nГрафики и таблицы сохранены в папке: {RESULTS_DIR}")

    sys.stdout = sys.__stdout__
    report_file.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
