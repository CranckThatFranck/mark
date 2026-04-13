import re

with open("/home/francisco/Documentos/repos/mark/src/backend/context_setup.py", "r") as f:
    content = f.read()

# Precisamos garantir que na linha de 'BASE_DIR.mkdir(parents=True, exist_ok=True)' 
# do contexto, isso execute mesmo se cair no fallback root e ele for usado pelo config.py
# Vamos dar apply no context_setup e sync src pra /opt
