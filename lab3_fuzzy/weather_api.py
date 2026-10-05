"""Получение данных: текущая погода (OpenWeatherMap) и история (Open-Meteo)."""
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
CACHE_DIR = Path(__file__).resolve().parent / "data" / "cache"


def get_current_weather(city, api_key):
    """Этап 1. Текущие погодные данные города из OpenWeatherMap.

    Возвращает словарь с показателями или None при ошибке.
    """
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "ru"}
    try:
        response = requests.get(OWM_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {
            "city": city,
            "timestamp": datetime.now(),
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "wind_gust": data["wind"].get("gust", 0),
            "description": data["weather"][0]["description"],
        }
    except requests.exceptions.HTTPError as exc:
        # Текст исключения содержит адрес с ключом, поэтому выводим только код
        print(f"Ошибка получения данных для {city}: HTTP {exc.response.status_code}")
    except (requests.exceptions.RequestException, KeyError, ValueError) as exc:
        print(f"Ошибка получения данных для {city}: {type(exc).__name__}")
    return None


def get_historical_weather(city, lat, lon, years=5, use_cache=True):
    """Этап 2. Суточные исторические данные за последние годы из Open-Meteo.

    Возвращает DataFrame со столбцами: date, temperature, humidity, wind_speed.
    Загруженные данные сохраняются в data/cache, чтобы не запрашивать их повторно
    в тот же день.
    """
    end = date.today() - timedelta(days=7)        # архив обновляется с задержкой
    start = end.replace(year=end.year - years)
    cache_file = CACHE_DIR / f"{city.replace(' ', '_')}_{start}_{end}.csv"
    if use_cache and cache_file.exists():
        return pd.read_csv(cache_file, parse_dates=["date"])

    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "daily": "temperature_2m_mean,relative_humidity_2m_mean,wind_speed_10m_mean",
        "wind_speed_unit": "ms",
        "timezone": "Europe/Moscow",
    }
    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=60)
        response.raise_for_status()
        daily = response.json()["daily"]
    except (requests.exceptions.RequestException, KeyError, ValueError) as exc:
        print(f"Ошибка получения истории для {city}: {type(exc).__name__}")
        return None

    df = pd.DataFrame({
        "date": pd.to_datetime(daily["time"]),
        "temperature": daily["temperature_2m_mean"],
        "humidity": daily["relative_humidity_2m_mean"],
        "wind_speed": daily["wind_speed_10m_mean"],
    }).dropna()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_file, index=False)
    return df
