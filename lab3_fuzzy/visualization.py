"""Этап 7. Визуализация: функции принадлежности, сезонные профили, тренды."""
import matplotlib
matplotlib.use("Agg")                     # рисуем в файлы, без окна
import matplotlib.pyplot as plt
import numpy as np

from cities import CITIES, SEASON_RU, SEASONS
from fuzzy_system import TERMS_RU

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
TERM_COLORS = ["#2a78d6", "#1baf7a", "#eda100", "#eb6834", "#e34948"]

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "figure.facecolor": "white", "axes.facecolor": "white", "axes.axisbelow": True,
})


def plot_membership(system, current, score, path):
    """Функции принадлежности трёх входов и выхода с отметкой текущих значений."""
    city_ru = CITIES[system.city]["name_ru"]
    panels = [
        (system.temperature, "temperature", "Температура, °C", current["temperature"]),
        (system.humidity, "humidity", "Влажность, %", current["humidity"]),
        (system.wind, "wind", "Скорость ветра, м/с", current["wind_speed"]),
        (system.comfort, "comfort", "Уровень комфорта, баллы", score),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5))
    for ax, (variable, key, xlabel, value) in zip(axes.ravel(), panels):
        for color, term in zip(TERM_COLORS, variable.terms):
            ax.plot(variable.universe, variable[term].mf, color=color, lw=2,
                    label=TERMS_RU[key][term])
        ax.axvline(value, color=INK, lw=1.5, ls="--")
        name = "результат" if key == "comfort" else "сейчас"
        ax.set_title(f"{xlabel.split(',')[0]} ({name}: {value:.1f})", loc="left")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Степень принадлежности")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8, frameon=False, loc="upper center",
                  bbox_to_anchor=(0.5, -0.22), ncol=3)
    fig.suptitle(f"{city_ru}: функции принадлежности ({SEASON_RU[system.season]})",
                 fontsize=13, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_seasonal_profiles(norms_by_city, path):
    """Сезонные профили городов: средние температура, влажность и ветер."""
    measures = [("temperature_mean", "Средняя температура, °C"),
                ("humidity_mean", "Средняя влажность, %"),
                ("wind_speed_mean", "Средняя скорость ветра, м/с")]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
    x = np.arange(len(SEASONS))
    width = 0.26
    for ax, (column, title) in zip(axes, measures):
        for i, (city, norms) in enumerate(norms_by_city.items()):
            ax.bar(x + (i - 1) * width, norms[column].values, width * 0.92,
                   color=CITIES[city]["color"], label=CITIES[city]["name_ru"])
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([SEASON_RU[s] for s in SEASONS])
        ax.set_title(title, loc="left")
        ax.grid(axis="x", visible=False)
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Сезонные климатические профили городов (Open-Meteo)",
                 fontsize=13, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_trends(annual_by_city, path):
    """Тренды среднегодовой температуры по многолетнему архиву."""
    fig, axes = plt.subplots(len(annual_by_city), 1, figsize=(12, 9), sharex=True)
    for ax, (city, series) in zip(axes, annual_by_city.items()):
        color = CITIES[city]["color"]
        years = series.index.values
        ax.plot(years, series.values, color=color, lw=1, alpha=0.45,
                label="среднегодовая температура")
        ax.plot(years, series.rolling(10, min_periods=5, center=True).mean(),
                color=color, lw=2.2, label="скользящее среднее за 10 лет")
        k, b = np.polyfit(years, series.values, 1)       # линейный тренд
        ax.plot(years, k * years + b, color=INK, lw=1.2, ls="--",
                label=f"линейный тренд: {k * 100:+.2f} °C за 100 лет")
        ax.set_title(CITIES[city]["name_ru"], loc="left")
        ax.set_ylabel("°C")
        ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    axes[-1].set_xlabel("Год")
    fig.suptitle("Тренды среднегодовой температуры (архив метеостанций)",
                 fontsize=13, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_comfort(results, path):
    """Итоговый уровень комфорта по городам."""
    fig, ax = plt.subplots(figsize=(8, 4.2))
    names = [CITIES[r["city"]]["name_ru"] for r in results]
    scores = [r["comfort_score"] for r in results]
    bars = ax.bar(names, scores, width=0.5,
                  color=[CITIES[r["city"]]["color"] for r in results])
    for bar, r in zip(bars, results):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{r['comfort_score']:.1f}\n{r['comfort_level_ru']}",
                ha="center", va="bottom", color=INK, fontsize=10)
    ax.set_ylim(0, 115)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel("Уровень комфорта, баллы")
    ax.set_title("Результат нечёткого вывода: уровень комфорта", loc="left")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
