# Mark Alfa

Este é o repositório oficial do Mark Alfa, um sistema composto por:
- **Backend (Python)**: Um servidor WebSocket local encapsulando o Open Interpreter gerenciado pelo systemd.
- **Frontend (Python)**: Uma interface gráfica nativa em CustomTkinter interagindo via WebSocket para controle.

## Requisitos e Dependências
- **SO**: Fedora (RPM) ou Ubuntu (DEB).
- **Python**: Versão 3.10 a 3.12 (`venv` isolado exigido no deploy). 
- **Hardware**: CPU x86_64 moderna (instruções AVX suportadas).
- **Dependências (Pip)**: `websockets`, `psutil`, `open-interpreter`, `customtkinter`, `setuptools<70.0.0`.

## Preparações de Ambiente (LLM Providers e API Keys)
O backend do Mark Alfa utiliza a biblioteca LiteLLM embutida no Open Interpreter, o que permite o uso dinâmico de diferentes provedores. **A responsabilidade de prover chaves e configurar o ambiente de sistema é puramente do Operador**. O Mark não automatiza criação de keys ou injeção forçada de credenciais no SO por razões de segurança.

Você pode usar modelos através de 2 mecanismos principais (configuráveis a qualquer momento via hotswap na UI do Mark):

### 1. Modelos Gemini via API Key simples (`gemini/...`)
Para acessar os modelos abertos do Google (ex: `gemini-2.5-flash`, `gemini-2.5-pro`):
Exporte no seu shell (se for rodar o `server.py` manualmente):
```bash
export GEMINI_API_KEY="sua_chave"
```
**No SystemD (Uso Produtivo Instalável):**
Crie um drop-in de override antes de ativar o daemon:
```bash
sudo mkdir -p /etc/systemd/system/jarvis-backend.service.d
sudo bash -c 'cat << EOF > /etc/systemd/system/jarvis-backend.service.d/override.conf
[Service]
Environment="GEMINI_API_KEY=sua_chave_aqui"
EOF'
sudo systemctl daemon-reload
```

### 2. Modelos Vertex AI via Conta de Serviço Google Cloud (`vertex_ai/...`)
Para acessar modelos de peso empresarial e Llama (ex: `vertex_ai/gemini-3.1-pro-preview-customtools` que é o padrão atual do Mark, ou `vertex_ai/llama-4-maverick-17b-128e-instruct-maas`), você precisa fornecer as credenciais via Application Default Credentials (JSON).

Exporte as seguintes variáveis no shell local (se for uso dev):
```bash
export VERTEXAI_PROJECT="id-do-seu-projeto-gcp"
export VERTEXAI_LOCATION="us-east5" # Região opcional. O backend forçará o override do frontend se configurado na interface.
export GOOGLE_APPLICATION_CREDENTIALS="/caminho/absoluto/para/sua/chave-de-servico.json"
```

**Exemplos de Camnho JSON por SO:**
- Fedora/Linux Geral: `/home/usuario/.config/gcloud/application_default_credentials.json`
- Ubuntu (Servidor): `/etc/gcp/mark-service-account.json`

**No SystemD (Uso Produtivo Instalável com Vertex AI):**
Da mesma forma, o daemon precisa herdar este Application Credentials e o Project. Configure no seu Drop-in:
```bash
sudo mkdir -p /etc/systemd/system/jarvis-backend.service.d
sudo bash -c 'cat << EOF > /etc/systemd/system/jarvis-backend.service.d/override.conf
[Service]
Environment="VERTEXAI_PROJECT=seu-projeto-123"
Environment="GOOGLE_APPLICATION_CREDENTIALS=/caminho/real/do/json/chave.json"
EOF'
sudo systemctl daemon-reload
```
A região padrão do projeto é `us-east5`. No entanto, você pode alterá-la dinamicamente escolhendo ou digitando uma região nova diretamente na Interface do Mark Alfa, que o backend atualizará a conexão Vertex em tempo real.

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
