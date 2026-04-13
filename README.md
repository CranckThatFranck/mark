# Mark Alfa

Este é o repositório oficial do Mark Alfa, um sistema composto por:
- **Backend (Python)**: Um servidor WebSocket e HTTP local, isolado por systemd, responsável por rodar o Open Interpreter encapsulado e gerenciar o estado da máquina.
- **Frontend (Python)**: Uma interface gráfica nativa em CustomTkinter que se conecta ao backend via WebSocket e exibe o chat e status de execução.

## Requisitos e Dependências
- **SO**: Fedora ou Ubuntu.
- **Python**: Versão 3.10 ou superior (Testado/Homologado no 3.12, preferível ambiente isolado `venv`).
- **Hardware**: Processador x86_64 compatível com instruções modernas, ou compilação forçada manual do `numpy` (caso use arquiteturas antigas como Pentium P6200).
- **Dependências de Sistema**: `systemd`.
- **Bibliotecas do Backend** (instalar via pip): `websockets`, `psutil`, `open-interpreter`, `setuptools<70.0.0`.
- **Bibliotecas do Frontend** (instalar via pip): `customtkinter`, `websockets`.

## Preparações de Ambiente
A API da sua LLM favorita (ex: GEMINI, OPENAI, ANTHROPIC) deve estar exportada nas variáveis de ambiente globais do usuário alvo que instalará ou do root, dependendo da instalação. Exemplo:
```bash
export GEMINI_API_KEY="sua_chave"
```

## Instalação (Produto Instalável Final)

### Backend
Os pacotes gerados em `.rpm` (RedHat/Fedora) ou `.deb` (Debian/Ubuntu) instalam os arquivos do backend no diretório oficial raiz `/opt/jarvis/backend`.
Durante a instalação, o serviço do systemd é ativado automaticamente.
Para gerenciar o serviço:
```bash
sudo systemctl enable --now jarvis-backend
sudo systemctl start jarvis-backend
sudo systemctl stop jarvis-backend
sudo systemctl restart jarvis-backend
sudo systemctl status jarvis-backend
```

### Frontend
Os pacotes do frontend instalam os arquivos em `/opt/jarvis/frontend` e configuram um atalho `.desktop` em `/usr/share/applications/mark-alfa.desktop`. Você pode abrir o programa buscando por "Mark Alfa" no seu launcher do sistema (ex: GNOME, XFCE).

## Uso Local (Sem Instalar no Root)
Caso queira testar a aplicação clonada sem invadir o `/opt/jarvis`:
1. Instale as dependências: `pip install -r requirements.txt` (ou instale os módulos listados acima manualmente num venv).
2. Rode o backend: `./scripts/run_backend_local.sh`
3. Em outra aba de terminal, rode o frontend: `python3 src/frontend/app.py`

## Operação e Troubleshooting
- **Interrupção (Kill Switch):** Pode ser ativada diretamente pela UI (botão vermelho "KILL SWITCH"). Ela força o isolamento de PID/PGID e derruba a árvore de processos ou loops de repetição infinitos causados pela IA, restabelecendo o backend de volta a "idle".
- **Logs e Persistência:**
  - O Backend armazena os dados do `AgentContext` dinamicamente baseando-se no diretório `~/Documents/JarvisMinion` (caso exista) ou criando como fallback o diretório `~/Documents/JarvisMark`.
  - Configurações e Logs residem em `config.json` e `backend.log` (diretamente dentro dessa pasta persistente detectada na `/home/` ou equivalente ao ambiente de execução do systemd).
- **Problemas de Conexão WebSocket:** Verifique se a porta `8765/tcp` está sendo bloqueada ou em uso por outro processo (`sudo fuser 8765/tcp`).
- **Problemas com Numpy/ImportError no Backend:** Verifique sua versão de CPU ou reinstale as bibliotecas (`pip install --force-reinstall numpy==1.26.4`) e ajuste a versão do `setuptools`.

## Divisão e Distinção de Ambientes
Este repositório respeita uma separação e portabilidade claras:
1. **Ambiente Atual (O Agente Jarvis)**: A instância que desenvolveu este código usa os arquivos localizados diretamente em `/home/francisco/Documentos/JarvisMinion`. Ela age como operária.
2. **Ambiente Instalável (Produto Futuro)**: O Mark Alfa criado residirá em `/opt/jarvis`, abstraído de nomes de usuário ou arquivos `.bashrc` amarrados, sendo 100% plug-and-play e preparado para ser distribuído. A instalação `.rpm` / `.deb` assume sempre esta raiz independente.

---
Desenvolvido por Jarvis/Mark 1 para Gaia Works. Documentação e contratos JSON de WebSockets podem ser vistos na pasta `AgentContext/`.
