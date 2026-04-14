import json
import logging
import os

from config import (
    CREDENTIALS_FILE,
    CONFIG_FILE,
    DEFAULT_MODEL,
    INITIAL_RULES_FILE,
    DEFAULT_INITIAL_RULES,
    SESSION_FILE,
    dedupe_models,
    is_allowed_custom_model,
    now_timestamp,
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


def _ensure_dir_permissions(path):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.exists():
            os.chmod(path.parent, 0o700)
    except Exception:
        # Em alguns ambientes o chmod pode falhar por permissao/SO.
        pass


def _ensure_file_permissions(path, mode):
    if mode is None:
        return
    try:
        if path.exists():
            os.chmod(path, mode)
    except Exception:
        pass


def _write_json(path, payload, file_mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    if file_mode is not None:
        _ensure_dir_permissions(path)
        _ensure_file_permissions(path, file_mode)


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


def _sanitize_timestamp(value):
    if isinstance(value, str) and value.strip():
        return value.strip()
    return now_timestamp()


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
                "timestamp": _sanitize_timestamp(item.get("timestamp")),
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


def default_credentials_state():
    return {
        "active_key_id": None,
        "keys": [],
    }


def _sanitize_key_id(value):
    if not isinstance(value, str):
        return ""
    return value.strip()


def _sanitize_label(value, fallback):
    if not isinstance(value, str):
        return fallback
    label = value.strip()
    return label or fallback


def _sanitize_secret(value):
    if not isinstance(value, str):
        return ""
    return value.strip()


def mask_secret(secret: str | None) -> str:
    if not isinstance(secret, str):
        return ""
    value = secret.strip()
    if not value:
        return ""
    if len(value) <= 8:
        return f"{value[:2]}...{value[-2:]}"
    return f"{value[:4]}...{value[-4:]}"


def sanitize_credentials_state(credentials_data):
    sanitized = default_credentials_state()
    if not isinstance(credentials_data, dict):
        return sanitized

    keys = []
    seen = set()
    for index, item in enumerate(credentials_data.get("keys", []), start=1):
        if not isinstance(item, dict):
            continue

        key_id = _sanitize_key_id(item.get("id"))
        if not key_id or key_id in seen:
            continue

        secret = _sanitize_secret(item.get("secret"))
        if not secret:
            continue

        label = _sanitize_label(item.get("label"), f"Gemini key {index}")
        created_at = _sanitize_timestamp(item.get("created_at"))
        updated_at = _sanitize_timestamp(item.get("updated_at"))

        seen.add(key_id)
        keys.append(
            {
                "id": key_id,
                "label": label,
                "secret": secret,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    sanitized["keys"] = keys

    active_key_id = _sanitize_key_id(credentials_data.get("active_key_id"))
    if active_key_id and any(item["id"] == active_key_id for item in keys):
        sanitized["active_key_id"] = active_key_id
    elif keys:
        sanitized["active_key_id"] = keys[0]["id"]

    return sanitized


def load_credentials_state():
    persisted = _read_json(CREDENTIALS_FILE)
    sanitized = sanitize_credentials_state(persisted)
    if persisted != sanitized:
        save_credentials_state(sanitized)
    else:
        _ensure_dir_permissions(CREDENTIALS_FILE)
        _ensure_file_permissions(CREDENTIALS_FILE, 0o600)
    return sanitized


def save_credentials_state(credentials_data: dict):
    sanitized = sanitize_credentials_state(credentials_data)
    _write_json(CREDENTIALS_FILE, sanitized, file_mode=0o600)
    return sanitized


def build_public_credentials_catalog(credentials_data: dict):
    sanitized = sanitize_credentials_state(credentials_data)
    keys = []
    active_id = sanitized.get("active_key_id")
    for item in sanitized.get("keys", []):
        keys.append(
            {
                "id": item["id"],
                "label": item["label"],
                "masked": mask_secret(item.get("secret")),
                "is_active": item["id"] == active_id,
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
            }
        )

    active_masked = ""
    for item in keys:
        if item["is_active"]:
            active_masked = item.get("masked", "")
            break

    return {
        "active_key_id": active_id,
        "active_key_masked": active_masked,
        "total_keys": len(keys),
        "keys": keys,
    }


def load_initial_rules() -> str:
    if not INITIAL_RULES_FILE.exists():
        return DEFAULT_INITIAL_RULES

    try:
        rules_text = INITIAL_RULES_FILE.read_text(encoding="utf-8").strip()
    except Exception as exc:
        logger.error(f"Erro ao ler {INITIAL_RULES_FILE}: {exc}")
        return DEFAULT_INITIAL_RULES

    return rules_text or DEFAULT_INITIAL_RULES
