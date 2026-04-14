import os
from pathlib import Path


INSTALL_DIR = Path("/opt/jarvis")
BACKEND_DIR = INSTALL_DIR / "backend"
FRONTEND_DIR = INSTALL_DIR / "frontend"


DEFAULT_MODEL = "gemini/gemini-3-flash-preview"
BUILTIN_MODELS = [
    "gemini/gemini-3-flash-preview",
    "gemini/gemini-3.1-pro-preview-customtools",
    "gemini/gemini-3.1-pro-preview",
    "gemini/gemini-2.5-pro",
    "gemini/gemini-2.5-flash",
]
SUPPORTED_MODELS = BUILTIN_MODELS[:]
LEGACY_ENV_KEYS = (
    "GOOGLE_APPLICATION_CREDENTIALS",
    "VERTEXAI_PROJECT",
    "VERTEXAI_LOCATION",
    "VERTEX_LOCATION",
    "VERTEXAI_LOCATION_DEFAULT",
)


def _get_home_dir() -> Path:
    home = os.environ.get("HOME")
    if home:
        return Path(home).expanduser()
    return Path.home()


def get_base_dir() -> Path:
    override = os.environ.get("MARK_BASE_DIR")
    if override:
        return Path(override).expanduser()

    home = _get_home_dir()
    for dirname in ("Documents", "Documentos"):
        candidate = home / dirname
        if candidate.exists() and candidate.is_dir():
            return candidate / "JarvisMark"
    return home / "JarvisMark"


BASE_DIR = get_base_dir()
LOGS_DIR = BASE_DIR / "logs"
MEMORY_DIR = BASE_DIR / "memoria"
STATE_DIR = BASE_DIR / "estado"
CONTEXTS_DIR = BASE_DIR / "contextos"
TRASH_DIR = BASE_DIR / "lixo"

MEMORY_LOG = MEMORY_DIR / "MemoriaDoJarvis.log"
CHANGE_LOG = LOGS_DIR / "change.log"
BACKEND_LOG = LOGS_DIR / "backend.log"
CONFIG_FILE = STATE_DIR / "config.json"
SESSION_FILE = STATE_DIR / "session.json"


def normalize_model(model_name: str | None) -> str:
    if not model_name:
        return ""
    return model_name.strip()


def is_gemini_model(model_name: str | None) -> bool:
    return normalize_model(model_name).startswith("gemini/")


def is_allowed_custom_model(model_name: str | None) -> bool:
    normalized = normalize_model(model_name)
    return is_gemini_model(normalized) and normalized not in BUILTIN_MODELS


def is_supported_model(model_name: str | None) -> bool:
    normalized = normalize_model(model_name)
    return normalized in BUILTIN_MODELS or is_allowed_custom_model(normalized)


def dedupe_models(model_names):
    unique = []
    seen = set()
    for raw_name in model_names:
        normalized = normalize_model(raw_name)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


WS_HOST = os.environ.get("MARK_WS_HOST", "127.0.0.1")
WS_PORT = int(os.environ.get("MARK_WS_PORT", "8765"))
