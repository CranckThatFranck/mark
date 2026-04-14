import os
import sys
from pathlib import Path

# Constantes do Produto Instalável Futuro
INSTALL_DIR = Path("/opt/jarvis")
BACKEND_DIR = INSTALL_DIR / "backend"
FRONTEND_DIR = INSTALL_DIR / "frontend"

def get_base_dir() -> Path:
    """
    Retorna o diretório base operacional do Jarvis.
    Tenta detectar se há uma pasta JarvisMinion ou equivalente no diretório Documents/Documentos do usuário.
    Se não encontrar, fallback para um caminho padrão.
    """
    home = Path.home()
    
    # Prioridades de busca
    possible_paths = [
        home / "Documentos" / "JarvisMinion",
        home / "Documents" / "JarvisMinion",
        home / "Documentos" / "JarvisMark",
        home / "Documents" / "JarvisMark",
        home / "JarvisMinion"
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path
            
    # Fallback se não existir (no ambiente instalável ele deve criar isso)
    fallback = home / "Documents" / "JarvisMark"
    return fallback

BASE_DIR = get_base_dir()
LOGS_DIR = BASE_DIR
MEMORY_LOG = BASE_DIR / "MemoriaDoJarvis.log"
CHANGE_LOG = BASE_DIR / "change.log"

# Modelos suportados e Padroes
DEFAULT_MODEL = "gemini/gemini-3.1-pro-preview"
DEFAULT_REGION = "us-east5"

SUPPORTED_MODELS = [
    "vertex_ai/gemini-3.1-pro-preview-customtools",
    "vertex_ai/gemini-3.1-pro-preview",
    "vertex_ai/gemini-3-flash-preview",
    "vertex_ai/gemini-3.1-flash-lite-preview",
    "vertex_ai/gemini-2.5-flash",
    "vertex_ai/gemini-2.5-pro",
    "vertex_ai/llama-4-scout-17b-16e-instruct-maas",
    "vertex_ai/llama-4-maverick-17b-128e-instruct-maas",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229"
]

# Configurações do Servidor
WS_HOST = "127.0.0.1"
WS_PORT = 8765

