"""Лабораторная работа №1. Интеграция экспертной системы Wolfram Alpha через API.

Программа последовательно выполняет запросы из queries.py, извлекает из
JSON-ответов ключевые данные, выводит их на экран и сохраняет в файлы.

Запуск:  python main.py
"""
import logging
import sys
import time
from datetime import datetime

from config import ConfigError, load_settings
from queries import QUERIES
from response_parser import format_result, parse_response
from storage import save_raw, save_summary
from wolfram_client import WolframAPIError, WolframClient, WolframNetworkError


def setup_logging(log_file):
    """Настраивает журнал: подробные записи в файл, предупреждения - на экран."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[file_handler, console_handler],
    )


def main():
    # Корректный вывод кириллицы и спецсимволов в консоли Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # 1. Конфигурация
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"Ошибка конфигурации: {exc}")
        return 1

    setup_logging(settings.log_file)
    log = logging.getLogger("main")
    log.info("Запуск программы, запросов: %d", len(QUERIES))

    client = WolframClient(settings.app_id, settings.base_url,
                           settings.timeout, settings.retries)

    records = []      # извлечённые данные по всем запросам
    blocks = []       # текстовые блоки для экрана и results.txt
    ok_count = 0

    # 2. Последовательное выполнение запросов
    for number, (category, query) in enumerate(QUERIES, start=1):
        try:
            data = client.query(query)                               # запрос
            raw_path = save_raw(settings.results_dir, number, query, data)
            parsed = parse_response(data)                            # обработка
            parsed["raw_file"] = str(raw_path.relative_to(settings.results_dir))
            if parsed["success"]:
                ok_count += 1
            else:
                log.warning("Запрос «%s» не распознан Wolfram Alpha", query)
        except (WolframAPIError, WolframNetworkError) as exc:
            # Ошибка одного запроса не останавливает всю программу
            log.error("Запрос «%s» завершился ошибкой: %s", query, exc)
            parsed = {"success": False, "error": str(exc)}

        block = format_result(number, category, query, parsed)
        print(block)
        blocks.append(block)
        records.append({"number": number, "category": category,
                        "query": query, **parsed})
        time.sleep(settings.pause)        # пауза, чтобы не перегружать API

    # 3. Сохранение результатов
    header = (f"Результаты запросов к Wolfram Alpha API\n"
              f"Дата выполнения: {datetime.now():%d.%m.%Y %H:%M:%S}\n"
              f"Успешно: {ok_count} из {len(QUERIES)}\n")
    json_path, txt_path = save_summary(settings.results_dir, records,
                                       header + "\n".join(blocks) + "\n")

    print("=" * 70)
    print(f"Успешно выполнено запросов: {ok_count} из {len(QUERIES)}")
    print(f"Полные ответы (JSON): {settings.results_dir / 'raw'}")
    print(f"Извлечённые данные:   {json_path.name}, {txt_path.name}")
    print(f"Журнал работы:        {settings.log_file}")
    log.info("Завершено: успешно %d из %d", ok_count, len(QUERIES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
