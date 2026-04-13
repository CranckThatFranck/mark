echo "##active_line2##"
import re
echo "##active_line3##"

echo "##active_line4##"
# Consertando o erro do config.json tentar ser salvo ANTES do context_setup rodar
echo "##active_line5##"
# Isso ocorre porque `state.py` importa e chama `load_config()` que por sua vez tenta salvar config default.
echo "##active_line6##"
# Precisamos que o config_manager e state.py criem a estrutura de pastas on-the-fly SE ELA NÃO EXISTIR, para evitar race condition global.
echo "##active_line7##"

echo "##active_line8##"
with open("/home/francisco/Documentos/repos/mark/src/backend/config_manager.py", "r") as f:
echo "##active_line9##"
    content = f.read()
echo "##active_line10##"

echo "##active_line11##"
patch = """
echo "##active_line12##"
def load_config():
echo "##active_line13##"
    \"\"\"Carrega as configurações persistidas, ou retorna as padrões se não existir.\"\"\"
echo "##active_line14##"
    BASE_DIR.mkdir(parents=True, exist_ok=True)
echo "##active_line15##"
"""
echo "##active_line16##"
content = re.sub(r'def load_config\(\):.*?\"\"\"Carrega as configurações persistidas, ou retorna as padrões se não existir\.\"\"\"', patch.strip(), content, flags=re.DOTALL)
echo "##active_line17##"

echo "##active_line18##"
with open("/home/francisco/Documentos/repos/mark/src/backend/config_manager.py", "w") as f:
echo "##active_line19##"
    f.write(content)
echo "##active_line20##"
