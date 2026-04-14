import os
from datetime import datetime
from pathlib import Path


INSTALL_DIR = Path("/opt/jarvis")
INSTALL_BACKEND_DIR = INSTALL_DIR / "backend"
FRONTEND_DIR = INSTALL_DIR / "frontend"
CURRENT_BACKEND_DIR = Path(__file__).resolve().parent
PRODUCT_CONFIG_DIR = CURRENT_BACKEND_DIR / "product_config"
INITIAL_RULES_FILE = PRODUCT_CONFIG_DIR / "initial_rules.txt"
INSTALLED_STATE_DIR = Path("/var/lib/jarvis-mark")


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
DEFAULT_INITIAL_RULES = """Voce e o Mark Alfa, um agente local operando pelo backend instalado do produto.

Regras globais iniciais:
- responda em portugues do Brasil, salvo pedido explicito do usuario por outro idioma;
- seja direto, tecnico e cuidadoso com impacto em arquivos, processos e sistema;
- preserve a arquitetura existente antes de propor refatores amplos;
- explique riscos relevantes, mas sem transformar cada resposta em discurso longo;
- quando produzir codigo, prefira caminhos reais, comandos executaveis e conteudo final utilizavel.
"""


def _get_home_dir() -> Path:
    home = os.environ.get("HOME")
    if home:
        return Path(home).expanduser()
    return Path.home()


def _installed_layout_active() -> bool:
    return CURRENT_BACKEND_DIR == INSTALL_BACKEND_DIR


def _legacy_home_base_dir(home: Path) -> Path:
    for dirname in ("Documents", "Documentos"):
        candidate = home / dirname
        if candidate.exists() and candidate.is_dir():
            return candidate / "JarvisMark"
    return home / "JarvisMark"


def _resolve_legacy_installed_state_dir() -> Path | None:
    root_home = Path("/root")
    for candidate in (
        root_home / "Documents" / "JarvisMark",
        root_home / "Documentos" / "JarvisMark",
        root_home / "JarvisMark",
    ):
        if candidate.exists():
            return candidate
    return None


def get_base_dir() -> Path:
    override = os.environ.get("MARK_BASE_DIR")
    if override:
        return Path(override).expanduser()

    if _installed_layout_active():
        legacy_dir = _resolve_legacy_installed_state_dir()
        if legacy_dir is not None:
            return legacy_dir
        return INSTALLED_STATE_DIR

    home = _get_home_dir()
    return _legacy_home_base_dir(home)


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


def now_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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
