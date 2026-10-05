"""Климатические нормы по сезонам, многолетний архив и выявление аномалий."""
from pathlib import Path

import pandas as pd

from cities import SEASONS, get_season

ARCHIVE_FILE = Path(__file__).resolve().parent / "data" / "wr316844.txt"


def calculate_seasonal_norms(history):
    """Этап 3. Климатические нормы по сезонам для одного города.

    history - DataFrame из get_historical_weather.
    Возвращает DataFrame: индекс - сезон, столбцы - среднее, стандартное
    отклонение, минимум и максимум температуры, средние и отклонения
    влажности и скорости ветра.
    """
    df = history.copy()
    df["season"] = df["date"].dt.month.map(get_season)
    norms = df.groupby("season").agg(
        temperature_mean=("temperature", "mean"),
        temperature_std=("temperature", "std"),
        temperature_min=("temperature", "min"),
        temperature_max=("temperature", "max"),
        humidity_mean=("humidity", "mean"),
        humidity_std=("humidity", "std"),
        wind_speed_mean=("wind_speed", "mean"),
        wind_speed_std=("wind_speed", "std"),
    )
    return norms.reindex(SEASONS).round(2)


def load_archive(path=ARCHIVE_FILE):
    """Загружает многолетний архив (файл из «Погода.zip»).

    Формат строки: индекс ВМО; год; месяц; день; средняя температура; осадки.
    """
    df = pd.read_csv(path, sep=";", header=None, skipinitialspace=True,
                     names=["wmo", "year", "month", "day", "temperature", "precip"])
    return df


def archive_monthly_norm(archive, wmo, month, start=1991, end=2020):
    """Многолетняя норма температуры месяца (по умолчанию за 1991-2020 гг.)."""
    part = archive[(archive["wmo"] == wmo) & (archive["month"] == month)
                   & archive["year"].between(start, end)]
    return float(part["temperature"].mean())


def archive_annual_means(archive, wmo, min_days=330):
    """Среднегодовая температура по годам (годы с пропусками отбрасываются)."""
    part = archive[archive["wmo"] == wmo].dropna(subset=["temperature"])
    grouped = part.groupby("year")["temperature"].agg(["mean", "count"])
    return grouped[grouped["count"] >= min_days]["mean"]


def detect_anomalies(current, norms, season):
    """Этап 6. Сравнение текущих показателей с сезонной нормой.

    Для каждого показателя считается z-оценка: (значение - среднее) / отклонение.
    |z| > 2 - аномалия, 1 < |z| <= 2 - заметное отклонение, иначе - норма.
    Возвращает список словарей по трём показателям.
    """
    names = {"temperature": "Температура", "humidity": "Влажность",
             "wind_speed": "Скорость ветра"}
    row = norms.loc[season]
    result = []
    for key, title in names.items():
        mean, std = row[f"{key}_mean"], row[f"{key}_std"]
        z = (current[key] - mean) / std if std else 0.0
        if abs(z) > 2:
            status = "аномалия"
        elif abs(z) > 1:
            status = "заметное отклонение"
        else:
            status = "в пределах нормы"
        direction = "выше нормы" if z > 0 else "ниже нормы"
        result.append({"parameter": title, "key": key, "value": current[key],
                       "norm": mean, "std": std, "z": round(float(z), 2),
                       "status": status, "direction": direction})
    return result
