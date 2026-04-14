import json
import logging

from config import (
    CONFIG_FILE,
    DEFAULT_MODEL,
    SESSION_FILE,
    dedupe_models,
    is_allowed_custom_model,
    is_supported_model,
    normalize_model,
)


logger = logging.getLogger(__name__)


def _read_json(path):
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        logger.error(f"Erro ao ler {path}: {exc}")
        return None


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def default_config():
    return {
        "mode": "agent",
        "model": DEFAULT_MODEL,
        "custom_models": [],
    }


def sanitize_config(config_data):
    sanitized = default_config()

    if isinstance(config_data, dict):
        mode = config_data.get("mode", "agent")
        if mode in {"agent", "plan"}:
            sanitized["mode"] = mode

        custom_models = [
            normalize_model(model_name)
            for model_name in config_data.get("custom_models", [])
            if is_allowed_custom_model(model_name)
        ]
        sanitized["custom_models"] = dedupe_models(custom_models)

        configured_model = normalize_model(config_data.get("model"))
        if configured_model in sanitized["custom_models"] or is_supported_model(configured_model):
            sanitized["model"] = configured_model

        if is_allowed_custom_model(sanitized["model"]) and sanitized["model"] not in sanitized["custom_models"]:
            sanitized["custom_models"].append(sanitized["model"])

    return sanitized


def load_config():
    persisted = _read_json(CONFIG_FILE)
    sanitized = sanitize_config(persisted)
    if persisted != sanitized:
        save_config(sanitized)
    return sanitized


def save_config(config_data: dict):
    sanitized = sanitize_config(config_data)
    _write_json(CONFIG_FILE, sanitized)
    return sanitized


def default_session_state():
    return {"history": []}


def sanitize_session_state(session_data):
    if not isinstance(session_data, dict):
        return default_session_state()

    history = []
    for item in session_data.get("history", []):
        if not isinstance(item, dict):
            continue

        message_type = normalize_model(item.get("message_type"))
        content = item.get("content")
        if message_type not in {"user", "message", "status", "code", "console", "system"}:
            continue
        if not isinstance(content, str) or not content:
            continue

        history.append(
            {
                "message_type": message_type,
                "content": content,
            }
        )

    return {"history": history}


def load_session_state():
    persisted = _read_json(SESSION_FILE)
    sanitized = sanitize_session_state(persisted)
    if persisted != sanitized:
        save_session_state(sanitized)
    return sanitized


def save_session_state(session_data: dict):
    sanitized = sanitize_session_state(session_data)
    _write_json(SESSION_FILE, sanitized)
    return sanitized
