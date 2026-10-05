"""Этап 4. Преобразование чисел в лингвистические переменные."""
from cities import SEASON_RU_GEN
from fuzzy_system import TERMS_RU


def numeric_to_linguistic(degrees, var_name, season):
    """Выбирает лингвистическое значение по степеням принадлежности.

    degrees  - словарь {терм: степень} для переменной var_name
               (результат WeatherFuzzySystem.fuzzify);
    Возвращает (название лучшего терма, строку со всеми ненулевыми степенями),
    например: ("холоднее нормы для осени", "холоднее нормы (0.8), нормально (0.13)").
    """
    names = TERMS_RU[var_name]
    best = max(degrees, key=degrees.get)
    label = names[best]
    if var_name == "temperature" and best != "normal":
        label += f" для {SEASON_RU_GEN[season]}"
    elif var_name == "temperature":
        label = f"нормально для {SEASON_RU_GEN[season]}"
    parts = [f"{names[t]} ({d:.2f})" for t, d in degrees.items() if d > 0]
    return label, ", ".join(parts)
