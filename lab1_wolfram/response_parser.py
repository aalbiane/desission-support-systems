"""Модуль обработки: извлечение ключевых данных из JSON-ответа Wolfram Alpha."""


def _pod_text(pod):
    """Собирает текст всех подблоков (subpods) одного блока (pod)."""
    parts = [sp.get("plaintext", "").strip() for sp in pod.get("subpods", [])]
    return "\n".join(p for p in parts if p)


def parse_response(data):
    """Извлекает из полного ответа ключевые данные.

    Возвращает словарь:
      success        - распознал ли Wolfram Alpha запрос;
      interpretation - как Wolfram Alpha понял запрос;
      result         - основной результат;
      result_title   - название блока с основным результатом;
      extra          - до трёх дополнительных блоков (название -> текст);
      numpods        - общее число блоков в ответе.
    """
    qr = data.get("queryresult", {})
    pods = qr.get("pods", []) or []
    parsed = {
        "success": bool(qr.get("success")),
        "numpods": qr.get("numpods", 0),
        "interpretation": "",
        "result": "",
        "result_title": "",
        "extra": {},
    }
    if not parsed["success"]:
        # Запрос не распознан: показываем подсказки, если они есть
        tips = qr.get("didyoumeans") or qr.get("tips") or ""
        parsed["result"] = f"Запрос не распознан. {tips}".strip()
        return parsed

    # 1. Интерпретация запроса - блок с id "Input"
    input_pod = next((p for p in pods if p.get("id") == "Input"), None)
    if input_pod:
        parsed["interpretation"] = _pod_text(input_pod)

    # 2. Основной результат: блок с признаком primary, иначе блок "Result",
    #    иначе первый блок с текстом, не являющийся интерпретацией.
    result_pod = next((p for p in pods if p.get("primary")), None)
    if result_pod is None:
        result_pod = next((p for p in pods if p.get("id") == "Result"), None)
    if result_pod is None:
        result_pod = next((p for p in pods
                           if p is not input_pod and _pod_text(p)), None)
    if result_pod:
        parsed["result"] = _pod_text(result_pod)
        parsed["result_title"] = result_pod.get("title", "")

    # 3. Дополнительные сведения: первые три остальных блока с текстом
    for pod in pods:
        if pod is input_pod or pod is result_pod:
            continue
        text = _pod_text(pod)
        if text:
            parsed["extra"][pod.get("title", "")] = text
        if len(parsed["extra"]) == 3:
            break
    return parsed


def format_result(number, category, query, parsed):
    """Формирует удобочитаемый текст по одному запросу."""
    lines = [
        "=" * 70,
        f"Запрос {number}. {category}",
        f"Текст запроса : {query}",
    ]
    if parsed.get("error"):
        lines.append(f"ОШИБКА        : {parsed['error']}")
        return "\n".join(lines)
    if parsed["interpretation"]:
        lines.append("Интерпретация : " + parsed["interpretation"].replace("\n", "; "))
    title = f" ({parsed['result_title']})" if parsed["result_title"] else ""
    lines.append(f"Результат{title}:")
    lines.extend("    " + ln for ln in parsed["result"].split("\n"))
    for name, text in parsed["extra"].items():
        first_lines = text.split("\n")[:3]          # не более трёх строк
        lines.append(f"  - {name}: " + "; ".join(first_lines))
    return "\n".join(lines)
