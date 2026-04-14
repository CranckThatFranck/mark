import json
import os
from pathlib import Path


DEFAULT_BACKEND_HOST = "127.0.0.1"


def get_frontend_config_file() -> Path:
    override = os.environ.get("MARK_FRONTEND_CONFIG_FILE")
    if override:
        return Path(override).expanduser()

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_root = Path(xdg_config_home).expanduser()
    else:
        config_root = Path.home() / ".config"

    return config_root / "jarvis-mark" / "frontend.json"


def normalize_backend_host(value: str | None) -> str:
    if not isinstance(value, str):
        return DEFAULT_BACKEND_HOST

    host = value.strip()
    if not host:
        return DEFAULT_BACKEND_HOST

    if host.startswith("ws://"):
        host = host[5:]
    elif host.startswith("wss://"):
        host = host[6:]

    host = host.split("/", 1)[0].strip()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]

    if host.count(":") == 1:
        base, maybe_port = host.rsplit(":", 1)
        if maybe_port.isdigit():
            host = base

    return host or DEFAULT_BACKEND_HOST


def default_frontend_config() -> dict:
    return {"backend_host": DEFAULT_BACKEND_HOST}


def sanitize_frontend_config(payload) -> dict:
    sanitized = default_frontend_config()
    if isinstance(payload, dict):
        sanitized["backend_host"] = normalize_backend_host(payload.get("backend_host"))
    return sanitized


def load_frontend_config() -> dict:
    config_file = get_frontend_config_file()
    if not config_file.exists():
        return default_frontend_config()

    try:
        with open(config_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return default_frontend_config()

    sanitized = sanitize_frontend_config(payload)
    if sanitized != payload:
        save_frontend_config(sanitized)
    return sanitized


def save_frontend_config(payload: dict) -> dict:
    sanitized = sanitize_frontend_config(payload)
    config_file = get_frontend_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as handle:
        json.dump(sanitized, handle, indent=2, ensure_ascii=False)
    return sanitized
