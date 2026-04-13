# Mark Alfa

Este é o repositório oficial do Mark Alfa, um sistema composto por:
- **Backend (Python)**: Um servidor WebSocket local encapsulando o Open Interpreter gerenciado pelo systemd.
- **Frontend (Python)**: Uma interface gráfica nativa em CustomTkinter interagindo via WebSocket para controle.

## Requisitos e Dependências
- **SO**: Fedora (RPM) ou Ubuntu (DEB).
- **Python**: Versão 3.10 a 3.12 (`venv` isolado exigido no deploy). 
- **Hardware**: CPU x86_64 moderna (instruções AVX suportadas).
- **Dependências (Pip)**: `websockets`, `psutil`, `open-interpreter`, `customtkinter`, `setuptools<70.0.0`.

## Preparações de Ambiente (API Keys)
O Open Interpreter e provedores LLM exigem chaves de API.
Para uso em terminal ou desenvolvimento, exporte-as no shell (ex: `~/.bashrc`):
```bash
export GEMINI_API_KEY="sua_chave"
export OPENAI_API_KEY="sua_chave"
```
**Atenção para uso Produtivo (SystemD):** Serviços do sistema operacional não herdam o shell do usuário automaticamente. Para o backend funcionar no modo Instalável de sistema, a chave deve ser declarada nativamente no drop-in do systemd **antes do daemon iniciar**:
```bash
sudo mkdir -p /etc/systemd/system/jarvis-backend.service.d
sudo bash -c 'cat << EOF > /etc/systemd/system/jarvis-backend.service.d/override.conf
[Service]
Environment="GEMINI_API_KEY=sua_chave"
EOF'
sudo systemctl daemon-reload
```

## Instalação (Produto Instalável Final)
O Produto oficial e final opera independentemente do diretório de onde o código fonte foi baixado. Ele é instalado como sistema.

**1. Instalação do Backend (`jarvis-backend`)**
Baixe ou compile o `.rpm` / `.deb` respectivo e instale.
A instalação jogará a pasta do backend para o destino `/opt/jarvis/backend/`.
- Após garantir as premissas de ambiente com `override.conf` das chaves:
```bash
sudo systemctl enable --now jarvis-backend
```

**2. Instalação do Frontend (`jarvis-frontend`)**
O pacote `.rpm` / `.deb` colocará o código de interface em `/opt/jarvis/frontend/` e criará um launcher global Desktop.
Você pode abrir o software buscando por "Mark Alfa" no seu menu de aplicações (GNOME, XFCE).

## Uso Local (Modo Desenvolvedor)
Se você não instalou via RPM/DEB e quer rodar os scripts da pasta de clone:
1. `pip install -r requirements.txt` (use venv).
2. `./scripts/run_backend_local.sh`
3. `python3 src/frontend/app.py`

## Divisão e Distinção de Ambientes
O design da aplicação respeita as seguintes divisões lógicas estritas para não misturar dados:

- **Ambiente de Desenvolvimento (O Agente Jarvis)**: A instância que desenvolve (Agente Autônomo) vive na pasta local do usuário em `/home/francisco/Documentos/JarvisMinion`. Estes arquivos e contextos são do agente desenvolvedor, não do produto Mark Alfa.
- **Ambiente Instalável (O Produto Mark Alfa)**: Os pacotes instaláveis são abstraídos de usuário. Residem globalmente em `/opt/jarvis/`.
- **Política de Contexto Dinâmico**: Embora os binários residam em `/opt`, o estado em tempo de execução do Mark Alfa (persistência, logs, config) busca um diretório dinâmico do usuário atual. Se ele encontrar um `~/Documents/JarvisMark` ou equivalente no home do usuário que iniciar a interface/sessão, ele salva `config.json` e logs (`backend.log`) lá, nunca sujando as permissões de `/opt/`.

## Troubleshooting & Operação
- **Interrupção (Kill Switch):** O botão vermelho no Frontend injeta o comando `interrupt` que forçadamente desativa a árvore de PID e Grupo PID do Open Interpreter em loops problemáticos, garantindo limpeza da RAM e retornando pro estado ocioso.
- **Conexão Falha (Erro 111):** Verifique o systemd `sudo systemctl status jarvis-backend` para conferir se o daemon quebrou por falha nas API_KEYs.

---
Desenvolvido pela Gaia Works. Veja a pasta `AgentContext/` para especificações operacionais JSON e arquitetura.
