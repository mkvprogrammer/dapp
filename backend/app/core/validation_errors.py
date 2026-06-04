"""
Человекочитаемые сообщения об ошибках валидации Pydantic (на русском).
"""

from typing import Any

from fastapi.exceptions import RequestValidationError

# Подписи полей в JSON-теле запроса → как показывать пользователю
FIELD_LABELS: dict[str, str] = {
    "student_id": "ITMO ID",
    "full_name": "ФИО",
    "password": "Пароль",
    "refresh_token": "Токен обновления",
    "access_token": "Токен доступа",
    "name": "Название",
    "resource_name": "Название ресурса",
    "duration_seconds": "Длительность (сек.)",
    "resource_limit": "Лимит ресурса",
    "amount": "Сумма ставки",
    "refund_rate": "Процент возврата",
    "penalty_schedule": "График штрафов",
    "initial_supply": "Начальная эмиссия",
    "project_id": "Проект",
    "auction_id": "Аукцион",
    "amount": "Количество токенов",
    "lesson_start_at": "Время начала занятия",
}


def _field_label(loc: tuple[str | int, ...]) -> str:
    """Имя поля из loc (пропускаем body/query/path)."""
    parts = [str(x) for x in loc if x not in ("body", "query", "path", "header")]
    if not parts:
        return "Запрос"
    name = parts[-1]
    if isinstance(name, str) and name.isdigit():
        return "Элемент списка"
    return FIELD_LABELS.get(name, name.replace("_", " ").capitalize())


def _format_one_error(err: dict[str, Any]) -> str:
    loc = tuple(err.get("loc") or ())
    label = _field_label(loc)
    err_type = err.get("type", "")
    ctx = err.get("ctx") or {}

    if err_type == "missing":
        return f"{label}: обязательное поле"
    if err_type == "string_too_short":
        n = ctx.get("min_length", "?")
        return f"{label}: не менее {n} символов"
    if err_type == "string_too_long":
        n = ctx.get("max_length", "?")
        return f"{label}: не более {n} символов"
    if err_type in ("string_type", "int_type", "float_type", "bool_type", "decimal_type"):
        return f"{label}: неверный тип данных"
    if err_type == "uuid_parsing":
        return f"{label}: неверный формат UUID"
    if err_type in ("int_parsing", "float_parsing", "decimal_parsing"):
        return f"{label}: должно быть числом"
    if err_type == "greater_than":
        return f"{label}: должно быть больше {ctx.get('gt', '?')}"
    if err_type == "greater_than_equal":
        return f"{label}: должно быть не меньше {ctx.get('ge', '?')}"
    if err_type == "less_than":
        return f"{label}: должно быть меньше {ctx.get('lt', '?')}"
    if err_type == "less_than_equal":
        return f"{label}: должно быть не больше {ctx.get('le', '?')}"
    if err_type == "value_error":
        return f"{label}: некорректное значение"
    if err_type == "json_invalid":
        return "Некорректный JSON в теле запроса"
    if err_type == "model_attributes_type":
        return "Тело запроса должно быть JSON-объектом"

    # Запасной вариант: убираем английский префикс Value error / Assertion failed
    raw = str(err.get("msg", "некорректное значение"))
    for prefix in ("Value error, ", "Assertion failed, "):
        if raw.startswith(prefix):
            raw = raw[len(prefix) :]
    return f"{label}: {raw}"


def format_validation_errors(exc: RequestValidationError) -> str:
    """Одна строка для поля detail в ответе API."""
    messages = [_format_one_error(e) for e in exc.errors()]
    return "; ".join(messages) if messages else "Неверные данные запроса"
