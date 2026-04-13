import json
import logging
from pathlib import Path
from config import BASE_DIR, DEFAULT_MODEL

logger = logging.getLogger(__name__)

CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    """Carrega as configuracoes persistidas, ou retorna as padroes se nao existir."""
    try:
        BASE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create BASE_DIR {BASE_DIR}: {e}")
    default_config = {
        "mode": "agent",
        "model": DEFAULT_MODEL
    }
    
    if not CONFIG_FILE.exists():
        save_config(default_config)
        return default_config
        
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            # Atualiza configs salvas com chaves padrao faltantes
            merged = {**default_config, **data}
            return merged
    except Exception as e:
        logger.error(f"Erro ao ler {CONFIG_FILE}: {e}")
        return default_config

def save_config(config_data: dict):
    """Salva o dicionário de configuração no disco."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        logger.error(f"Erro ao salvar {CONFIG_FILE}: {e}")

