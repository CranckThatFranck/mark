from config import (
    BACKEND_LOG,
    BASE_DIR,
    CHANGE_LOG,
    CONFIG_FILE,
    CONTEXTS_DIR,
    MEMORY_LOG,
    SESSION_FILE,
    STATE_DIR,
    TRASH_DIR,
)


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

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    prepare_context_structure()
    print(f"Estrutura de contexto garantida em {BASE_DIR}")
