echo "##active_line2##"
#!/bin/bash
echo "##active_line3##"
# Script utilitário para rodar o backend localmente sem precisar instalar globalmente
echo "##active_line4##"
cd "$(dirname "$0")/../src/backend" || exit 1
echo "##active_line5##"
export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "##active_line6##"
python3 server.py
echo "##active_line7##"
