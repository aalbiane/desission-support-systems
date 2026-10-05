"""Модуль запросов: клиент Wolfram Alpha Full Results API."""
import logging
import time

import requests

logger = logging.getLogger(__name__)


class WolframAPIError(Exception):
    """Ошибка, которую вернул сам API (неверный ключ, ошибка сервера и т.п.)."""


class WolframNetworkError(Exception):
    """Сетевая ошибка: нет соединения, тайм-аут и т.п."""


class WolframClient:
    """Клиент для выполнения запросов к Wolfram Alpha."""

    def __init__(self, app_id, base_url, timeout=30, retries=3):
        self.app_id = app_id
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()

    def query(self, input_text):
        """Выполняет запрос и возвращает полный JSON-ответ (словарь).

        При сетевых ошибках запрос повторяется self.retries раз.
        """
        params = {
            "appid": self.app_id,
            "input": input_text,
            "output": "json",        # ответ в формате JSON
            "format": "plaintext",   # содержимое блоков - простой текст
        }
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                logger.info("Запрос «%s» (попытка %d из %d)",
                            input_text, attempt, self.retries)
                response = self.session.get(self.base_url, params=params,
                                            timeout=self.timeout)
            except requests.exceptions.RequestException as exc:
                # Ошибки сети: нет соединения, тайм-аут, обрыв и т.д.
                # В текст ошибки попадает только её тип: полный текст содержит
                # адрес запроса вместе с API-ключом, его нельзя писать в журнал.
                last_error = type(exc).__name__
                logger.warning("Сетевая ошибка: %s", last_error)
                time.sleep(attempt)          # пауза перед повтором
                continue

            # Ошибки уровня HTTP (например, 403 при неверном AppID)
            if response.status_code != 200:
                raise WolframAPIError(
                    f"HTTP {response.status_code}: {response.text[:200]}")

            try:
                data = response.json()
            except ValueError as exc:
                raise WolframAPIError(f"Ответ не является JSON: {exc}") from exc

            # Ошибки уровня API приходят внутри queryresult
            result = data.get("queryresult", {})
            if result.get("error"):
                err = result["error"]
                msg = err.get("msg", err) if isinstance(err, dict) else err
                raise WolframAPIError(f"API вернул ошибку: {msg}")

            logger.info("Ответ получен: success=%s, блоков=%s",
                        result.get("success"), result.get("numpods"))
            return data

        raise WolframNetworkError(
            f"Не удалось выполнить запрос после {self.retries} попыток: {last_error}")
