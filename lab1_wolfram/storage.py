"""Модуль обработки: сохранение полных ответов и извлечённых данных в файлы."""
import json
import re
from pathlib import Path


def _slug(text):
    """Преобразует текст запроса в безопасное имя файла."""
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()[:40]


def save_raw(results_dir: Path, number, query, data):
    """Сохраняет полный JSON-ответ одного запроса в results/raw/."""
    raw_dir = results_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{number:02d}_{_slug(query)}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def save_summary(results_dir: Path, records, text_report):
    """Сохраняет извлечённые данные: results.json и results.txt."""
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path = results_dir / "results.json"
    txt_path = results_dir / "results.txt"
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    txt_path.write_text(text_report, encoding="utf-8")
    return json_path, txt_path
