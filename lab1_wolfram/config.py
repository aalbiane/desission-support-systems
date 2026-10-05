"""Модуль конфигурации: чтение настроек и API-ключа из файла config.ini."""
import configparser
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.ini"


class ConfigError(Exception):
    """Ошибка конфигурации (нет файла, нет ключа и т.п.)."""


@dataclass
class Settings:
    """Настройки программы, прочитанные из config.ini."""
    app_id: str          # API-ключ (AppID) Wolfram Alpha
    base_url: str        # адрес Full Results API
    timeout: int         # тайм-аут одного запроса, с
    retries: int         # число повторных попыток при сетевой ошибке
    pause: float         # пауза между запросами, с
    results_dir: Path    # каталог для результатов
    log_file: Path       # файл журнала


def load_settings(path: Path = CONFIG_PATH) -> Settings:
    """Читает config.ini и возвращает объект Settings."""
    if not path.exists():
        raise ConfigError(
            f"Не найден файл конфигурации {path}. "
            "Скопируйте config.example.ini в config.ini и впишите свой AppID."
        )
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")

    app_id = parser.get("wolfram", "app_id", fallback="").strip()
    if not app_id or app_id == "YOUR_APP_ID":
        raise ConfigError("В config.ini не указан app_id (раздел [wolfram]).")

    return Settings(
        app_id=app_id,
        base_url=parser.get("wolfram", "base_url",
                            fallback="https://api.wolframalpha.com/v2/query"),
        timeout=parser.getint("network", "timeout", fallback=30),
        retries=parser.getint("network", "retries", fallback=3),
        pause=parser.getfloat("network", "pause", fallback=1.0),
        results_dir=BASE_DIR / parser.get("output", "results_dir", fallback="results"),
        log_file=BASE_DIR / parser.get("output", "log_file", fallback="logs/wolfram.log"),
    )
