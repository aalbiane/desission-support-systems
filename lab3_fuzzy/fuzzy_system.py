"""Нечёткая экспертная система (алгоритм Мамдани, библиотека scikit-fuzzy)."""
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from cities import SEASON_RU_GEN

# Какой уровень комфорта даёт каждый терм температуры в разные сезоны.
# Зимой потепление воспринимается хорошо, летом сильная жара - плохо.
TEMPERATURE_COMFORT = {
    "winter": {"much_colder": "bad", "colder": "bad", "normal": "medium",
               "warmer": "good", "much_warmer": "medium"},
    "spring": {"much_colder": "bad", "colder": "medium", "normal": "good",
               "warmer": "good", "much_warmer": "good"},
    "summer": {"much_colder": "bad", "colder": "medium", "normal": "good",
               "warmer": "medium", "much_warmer": "bad"},
    "autumn": {"much_colder": "bad", "colder": "medium", "normal": "good",
               "warmer": "good", "much_warmer": "good"},
}

# Русские названия термов (лингвистические значения)
TERMS_RU = {
    "temperature": {"much_colder": "значительно холоднее нормы",
                    "colder": "холоднее нормы", "normal": "нормально",
                    "warmer": "теплее нормы",
                    "much_warmer": "значительно теплее нормы"},
    "humidity": {"dry": "сухо", "normal": "нормальная влажность", "high": "сыро"},
    "wind": {"calm": "штиль или слабый ветер", "moderate": "умеренный ветер",
             "strong": "сильный ветер"},
    "comfort": {"bad": "низкий", "medium": "средний", "good": "высокий"},
}


class WeatherFuzzySystem:
    """Нечёткая система оценки погодного комфорта для города и сезона.

    Антецеденты (входы): температура, влажность, скорость ветра.
    Консеквент (выход): уровень комфорта от 0 до 100.
    Функции принадлежности температуры строятся от сезонной нормы города
    (среднее mean_temp и стандартное отклонение std_temp), поэтому одна и та же
    температура получает разные лингвистические значения в разных городах
    и сезонах.
    """

    T_MIN, T_MAX = -45, 45

    def __init__(self, city, season, mean_temp, std_temp):
        self.city = city
        self.season = season
        self.mean_temp = float(mean_temp)
        # Ограничиваем отклонение, чтобы термы не вырождались и не выходили
        # за границы универсума
        self.std_temp = float(np.clip(std_temp, 2.0, 8.0))

        # --- Антецеденты ---
        self.temperature = ctrl.Antecedent(
            np.arange(self.T_MIN, self.T_MAX + 1, 1), "temperature")
        self.humidity = ctrl.Antecedent(np.arange(0, 101, 1), "humidity")
        self.wind = ctrl.Antecedent(np.arange(0, 31, 1), "wind")
        # --- Консеквент ---
        self.comfort = ctrl.Consequent(np.arange(0, 101, 1), "comfort")

        self._define_membership_functions()
        self.rules, self.rule_texts = self._build_rules()
        self.system = ctrl.ControlSystem(self.rules)
        self.simulation = ctrl.ControlSystemSimulation(self.system)

    # ------------------------------------------------------------------
    def _define_membership_functions(self):
        """Функции принадлежности всех переменных."""
        m, s = self.mean_temp, self.std_temp
        u = self.temperature.universe
        # Температура: пять термов относительно сезонной нормы города
        self.temperature["much_colder"] = fuzz.trapmf(
            u, [self.T_MIN, self.T_MIN, m - 2.5 * s, m - 1.5 * s])
        self.temperature["colder"] = fuzz.trimf(
            u, [m - 2.5 * s, m - 1.5 * s, m - 0.5 * s])
        self.temperature["normal"] = fuzz.trimf(
            u, [m - 1.5 * s, m, m + 1.5 * s])
        self.temperature["warmer"] = fuzz.trimf(
            u, [m + 0.5 * s, m + 1.5 * s, m + 2.5 * s])
        self.temperature["much_warmer"] = fuzz.trapmf(
            u, [m + 1.5 * s, m + 2.5 * s, self.T_MAX, self.T_MAX])

        # Влажность (общая для всех городов), %
        h = self.humidity.universe
        self.humidity["dry"] = fuzz.trapmf(h, [0, 0, 30, 45])
        self.humidity["normal"] = fuzz.trapmf(h, [35, 50, 70, 85])
        self.humidity["high"] = fuzz.trapmf(h, [75, 90, 100, 100])

        # Скорость ветра, м/с
        w = self.wind.universe
        self.wind["calm"] = fuzz.trapmf(w, [0, 0, 2, 4])
        self.wind["moderate"] = fuzz.trimf(w, [2, 5, 9])
        self.wind["strong"] = fuzz.trapmf(w, [7, 12, 30, 30])

        # Уровень комфорта, баллы 0-100
        c = self.comfort.universe
        self.comfort["bad"] = fuzz.trapmf(c, [0, 0, 20, 40])
        self.comfort["medium"] = fuzz.trimf(c, [30, 50, 70])
        self.comfort["good"] = fuzz.trapmf(c, [60, 80, 100, 100])

    # ------------------------------------------------------------------
    def _build_rules(self):
        """База правил «ЕСЛИ ..., ТО ...»: общие, сезонные и для конкретного города."""
        t, h, w, c = self.temperature, self.humidity, self.wind, self.comfort
        rules, texts = [], []

        def add(antecedent, level, text):
            rules.append(ctrl.Rule(antecedent, c[level]))
            texts.append(f"ЕСЛИ {text}, ТО комфорт {TERMS_RU['comfort'][level]}")

        # 1. Сезонные правила по температуре (покрывают весь диапазон значений)
        for term, level in TEMPERATURE_COMFORT[self.season].items():
            add(t[term], level,
                f"температура «{TERMS_RU['temperature'][term]}» для {SEASON_RU_GEN[self.season]}")

        # 2. Общие правила по ветру и влажности
        add(w["strong"], "bad", "ветер сильный")
        add(t["normal"] & w["calm"] & h["normal"], "good",
            "температура нормальная И ветер слабый И влажность нормальная")
        add(h["high"] & (t["colder"] | t["much_colder"]), "bad",
            "сыро И холоднее нормы")
        add(h["dry"] & w["moderate"], "medium", "сухо И ветер умеренный")

        # 3. Специфические правила городов (экспертные знания)
        if self.city == "Saint Petersburg":
            # Морской климат: сырость с ветром переносится тяжело
            add(h["high"] & (w["moderate"] | w["strong"]), "bad",
                "сыро И ветер умеренный или сильный (Санкт-Петербург)")
        elif self.city == "Kazan":
            # Континентальный климат: мороз в штиль переносится легче
            add(t["colder"] & w["calm"] & (h["dry"] | h["normal"]), "medium",
                "холоднее нормы И штиль И воздух не сырой (Казань)")
            add(t["much_colder"] & (w["moderate"] | w["strong"]), "bad",
                "значительно холоднее нормы И ветер (Казань)")
        elif self.city == "Moscow":
            if self.season == "summer":
                # Волны жары и «остров тепла» в центре города
                add((t["warmer"] | t["much_warmer"]) & w["calm"], "bad",
                    "теплее нормы И штиль - волна жары (Москва)")
            # Шквалистый ветер с осадками
            add(h["high"] & w["strong"], "bad",
                "сыро И сильный ветер - шквал (Москва)")
        return rules, texts

    # ------------------------------------------------------------------
    def fuzzify(self, temperature, humidity, wind):
        """Фаззификация: степени принадлежности входных значений всем термам."""
        values = {"temperature": (self.temperature, temperature),
                  "humidity": (self.humidity, humidity),
                  "wind": (self.wind, wind)}
        result = {}
        for name, (variable, value) in values.items():
            u = variable.universe
            value = float(np.clip(value, u.min(), u.max()))
            result[name] = {
                term: round(float(fuzz.interp_membership(u, variable[term].mf, value)), 2)
                for term in variable.terms
            }
        return result

    def evaluate(self, temperature, humidity, wind):
        """Нечёткий вывод Мамдани. Возвращает (балл комфорта, название уровня)."""
        sim = self.simulation
        # Значения вне универсума приводим к его границам
        sim.input["temperature"] = float(np.clip(temperature, self.T_MIN, self.T_MAX))
        sim.input["humidity"] = float(np.clip(humidity, 0, 100))
        sim.input["wind"] = float(np.clip(wind, 0, 30))
        sim.compute()                      # агрегирование, активация, аккумуляция,
        score = float(sim.output["comfort"])   # дефаззификация (центр тяжести)

        # Лингвистическое значение результата - терм с наибольшей принадлежностью
        u = self.comfort.universe
        degrees = {term: float(fuzz.interp_membership(u, self.comfort[term].mf, score))
                   for term in self.comfort.terms}
        level = max(degrees, key=degrees.get)
        return round(score, 1), level
