echo "##active_line2##"
# Mark Alfa
echo "##active_line3##"

echo "##active_line4##"
Este é o repositório oficial do Mark Alfa, um sistema composto por:
echo "##active_line5##"
- **Backend (Python)**: Um servidor WebSocket e HTTP local, isolado por systemd, responsável por rodar o Open Interpreter encapsulado e gerenciar o estado da máquina.
echo "##active_line6##"
- **Frontend (Python)**: Uma interface gráfica nativa em CustomTkinter que se conecta ao backend via WebSocket e exibe o chat e status de execução.
echo "##active_line7##"

echo "##active_line8##"
## Requisitos e Dependências
echo "##active_line9##"
- SO: Fedora ou Ubuntu.
echo "##active_line10##"
- Python 3.10+
echo "##active_line11##"
- Bibliotecas do Backend: `websockets`, `psutil`, `open-interpreter`.
echo "##active_line12##"
- Bibliotecas do Frontend: `customtkinter`, `websockets`.
echo "##active_line13##"

echo "##active_line14##"
## Instalação (Produto Final)
echo "##active_line15##"

echo "##active_line16##"
**Backend:**
echo "##active_line17##"
Os pacotes gerados em `.rpm` ou `.deb` instalam os arquivos do backend no diretório oficial `/opt/jarvis/backend` e ativam o serviço do systemd associado:
echo "##active_line18##"
```bash
echo "##active_line19##"
sudo systemctl enable --now jarvis-backend
echo "##active_line20##"
```
echo "##active_line21##"

echo "##active_line22##"
**Frontend:**
echo "##active_line23##"
Os pacotes do frontend instalam os arquivos em `/opt/jarvis/frontend` e configuram um atalho `.desktop` em `/usr/share/applications/mark-alfa.desktop`.
echo "##active_line24##"

echo "##active_line25##"
## Operação e Troubleshooting
echo "##active_line26##"
- **Execução Local Sem Instalar:** Use o script `./scripts/run_backend_local.sh`. Em seguida, execute o `python3 src/frontend/app.py`.
echo "##active_line27##"
- **Interrupção (Kill Switch):** Pode ser ativada diretamente pela UI (botão vermelho). Ela força o isolamento de PID/PGID e derruba a árvore de subprocessos travada.
echo "##active_line28##"
- **Logs e Persistência:**
echo "##active_line29##"
  - O Backend armazena os dados do `AgentContext` dinamicamente com base no `~/Documents/JarvisMinion` ou `~/Documents/JarvisMark`.
echo "##active_line30##"
  - Configurações e Logs residem em `config.json` e `backend.log`.
echo "##active_line31##"

echo "##active_line32##"
## Divisão de Ambientes
echo "##active_line33##"
Este repositório preserva a separação entre:
echo "##active_line34##"
1. **O ambiente atual do agente Jarvis**: que trabalha e executa suas tarefas em `/home/francisco/Documentos/JarvisMinion` e neste próprio repositório.
echo "##active_line35##"
2. **O ambiente do Produto Instalável Futuro**: onde a aplicação backend e frontend residem em `/opt/jarvis` (como descrito acima).
echo "##active_line36##"

echo "##active_line37##"
## Documentação Completa
echo "##active_line38##"
A documentação detalhada (roadmap, arquitetura, política e contratos) está na pasta `AgentContext/`.
echo "##active_line39##"
