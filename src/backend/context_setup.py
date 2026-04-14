import logging

from config import (
    BACKEND_LOG,
    BASE_DIR,
    CHANGE_LOG,
    CONFIG_FILE,
    CONTEXTS_DIR,
    DEFAULT_INITIAL_RULES,
    ERRORS_LOG,
    INITIAL_RULES_FILE,
    MEMORY_LOG,
    OPERATIONS_LOG,
    SESSION_FILE,
    STATE_DIR,
    TRASH_DIR,
)


logger = logging.getLogger(__name__)


def _touch_text_file(path, initial_content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(initial_content, encoding="utf-8")


def prepare_context_structure():
    """Garante a estrutura minima de contexto operacional do Mark."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    _touch_text_file(MEMORY_LOG, "=== Inicio do Log de Memoria do Mark ===\n")
    _touch_text_file(CHANGE_LOG, "=== Inicio do Log de Alteracoes do Mark ===\n")
    _touch_text_file(BACKEND_LOG, "")
    _touch_text_file(OPERATIONS_LOG, "")
    _touch_text_file(ERRORS_LOG, "")
    _touch_text_file(INITIAL_RULES_FILE, DEFAULT_INITIAL_RULES)

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Contexto operacional ativo em {BASE_DIR}")
    logger.info(f"Arquivo padrao de regras iniciais em {INITIAL_RULES_FILE}")


if __name__ == "__main__":
    prepare_context_structure()
    print(f"Estrutura de contexto garantida em {BASE_DIR}")
