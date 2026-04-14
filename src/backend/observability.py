import json
import logging
import re
from typing import Any

from config import now_timestamp


operations_logger = logging.getLogger("MarkOperations")
errors_logger = logging.getLogger("MarkErrors")

SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "secret",
    "token",
    "access_token",
    "refresh_token",
}

API_KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_\-]{8,}")
QUERY_SECRET_PATTERN = re.compile(
    r"(?i)\b((?:api[_-]?key|key|token|access[_-]?token|refresh[_-]?token)=)([^&\s\"']+)"
)
BEARER_PATTERN = re.compile(r"(?i)\b(Bearer\s+)([A-Za-z0-9._\-]+)")


def redact_secret(secret: str | None) -> str:
    if not isinstance(secret, str):
        return ""
    value = secret.strip()
    if not value:
        return ""
    if len(value) <= 8:
        return f"{value[:2]}...{value[-2:]}"
    return f"{value[:4]}...{value[-4:]}"


def redact_text(value: str | None) -> str:
    if not isinstance(value, str):
        return ""

    sanitized = QUERY_SECRET_PATTERN.sub(lambda match: f"{match.group(1)}***", value)
    sanitized = BEARER_PATTERN.sub(lambda match: f"{match.group(1)}***", sanitized)
    sanitized = API_KEY_PATTERN.sub(lambda match: redact_secret(match.group(0)), sanitized)
    return sanitized


def _must_redact(key_name: str) -> bool:
    lowered = key_name.lower()
    return (
        lowered in SENSITIVE_KEYS
        or lowered.endswith("_secret")
        or lowered.endswith("_token")
        or lowered == "key"
    )


def _safe_value(value: Any):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_name = str(key)
            if _must_redact(key_name):
                sanitized[key_name] = "***"
            else:
                sanitized[key_name] = _safe_value(item)
        return sanitized

    if isinstance(value, list):
        return [_safe_value(item) for item in value]

    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]

    if isinstance(value, BaseException):
        return redact_text(str(value))

    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str):
            return redact_text(value)
        return value

    return redact_text(str(value))


def _encode_payload(event: str, fields: dict[str, Any]) -> str:
    payload = {
        "timestamp": now_timestamp(),
        "event": event,
    }
    payload.update(_safe_value(fields))
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def log_operation(event: str, **fields):
    operations_logger.info(_encode_payload(event, fields))


def log_error(event: str, error: Any = None, **fields):
    if error is not None:
        fields["error"] = str(error)
    errors_logger.error(_encode_payload(event, fields))
