import os
import shutil
from pathlib import Path
from config import BASE_DIR

def prepare_context_structure():
    """
    Garante que a estrutura mínima do contexto do Jarvis exista no ambiente onde o backend vai rodar.
    Cria a pasta base, os logs de memória se não existirem, e a pasta lixo.
    """
    # Garante o diretório principal
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Garante os diretórios internos
    lixo_dir = BASE_DIR / "lixo"
    lixo_dir.mkdir(exist_ok=True)
    
    contextos_dir = BASE_DIR / "contextos"
    contextos_dir.mkdir(exist_ok=True)
    
    # Garante os logs base
    memoria_log = BASE_DIR / "MemoriaDoJarvis.log"
    if not memoria_log.exists():
        memoria_log.write_text("=== Início do Log de Memória do Jarvis ===\n")
        
    change_log = BASE_DIR / "change.log"
    if not change_log.exists():
        change_log.write_text("=== Início do Log de Alterações ===\n")

if __name__ == "__main__":
    prepare_context_structure()
    print(f"Estrutura de contexto garantida em {BASE_DIR}")
