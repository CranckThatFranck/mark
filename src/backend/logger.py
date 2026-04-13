import logging
import sys
from pathlib import Path
from config import BASE_DIR

def setup_logger():
    """Configura o logger com persistência no arquivo de log do backend."""
    # Garante diretório
    log_file = BASE_DIR / "backend.log"
    
    # Criar um logger customizado
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Previne handlers duplicados
    if logger.handlers:
        logger.handlers.clear()
        
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler de Arquivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Handler de Console (Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Inicializa ao importar
backend_logger = setup_logger()
