# Mark Alfa

Este é o repositório oficial do Mark Alfa, um sistema composto por:
- **Backend (Python)**: Um servidor WebSocket local encapsulando o Open Interpreter rodando em background (SystemD).
- **Frontend (Python)**: Uma interface gráfica nativa em CustomTkinter interagindo via WebSocket para controle.

## Requisitos e Pré-Instalações (Dependências Externas)
- **SO**: Fedora (RPM) ou Ubuntu (DEB).
- **Python**: Versão 3.10 a 3.12 (exigido ambiente isolado `venv` no servidor).
- **Hardware**: CPU x86_64 compatível com AVX/SSE4 (Para `numpy 2.x`). Caso utilize hardware antigo (Ex: Pentium P6200), você deve compilar manualmente a versão legado `numpy==1.26.4`.
- **Dependências (Pip)**: O pacote `.rpm`/`.deb` espera que o ambiente global do servidor possua um python ou forneça essas libs: `websockets`, `psutil`, `open-interpreter`, `customtkinter`, `setuptools<70.0.0` e, **OBRIGATÓRIO para usar a rota de modelos Vertex AI, o pacote `google-cloud-aiplatform`**.
- **Nota do RPM:** Os pacotes RPM/DEB empacotam apenas a estrutura base da aplicação em `/opt/jarvis`. A gerência do `venv` ou Python System-wide é pré-requisito externo do sistema operacional e de quem o opera.

## Configuração de Ambiente (API Keys & Cloud)
A responsabilidade por configurar credenciais, JSONs e exportar variáveis de sistema **pertence puramente ao Operador Humano**. A aplicação apenas consome o que o sistema operacional lhe dá.

O Mark permite Hotswap de modelos na UI. Cada provedor requer uma var diferente:

### 1. Modelos Gemini Básicos (`gemini/...`)
Exige a var genérica:
`GOOGLE_API_KEY="sua_chave"`

### 2. Modelos Vertex AI Enterprise (`vertex_ai/...`)
Exige as variáveis de projeto, autenticação explícita JSON e o pacote `google-cloud-aiplatform`:
`GOOGLE_APPLICATION_CREDENTIALS="/caminho/real/do/json/chave.json"`
`VERTEXAI_PROJECT="meu-projeto-123"`
`VERTEXAI_LOCATION="us-east5"` (opcional, padrão do Mark é `us-east5`).

*Exemplo de caminhos comuns para o JSON no SO:*
- Fedora/Desktop: `/home/usuario/Documentos/credentials/chave-vertex.json`
- Ubuntu/Server: `/etc/gcp/chave-vertex.json`

## Instalação (Produto Instalável Final)

**1. Instalação do Backend e Frontend**
Baixe os pacotes `.rpm` (RedHat) ou `.deb` (Debian) e instale:
`sudo rpm -ivh jarvis-backend-1.0.0-1.x86_64.rpm`
`sudo rpm -ivh jarvis-frontend-1.0.0-1.x86_64.rpm`
- O código fonte do backend vai para `/opt/jarvis/backend/`
- O código do frontend vai para `/opt/jarvis/frontend/` e gera um launcher global (`/usr/share/applications/mark-alfa.desktop`)

**2. Configuração e Autostart do Daemon**
Serviços em Systemd **não herdam** exports de `.bashrc` do usuário logado. Portanto, você é obrigado a prover as credenciais listadas acima em um `override.conf` para o daemon subir:
```bash
sudo mkdir -p /etc/systemd/system/jarvis-backend.service.d
sudo bash -c 'cat << EOF > /etc/systemd/system/jarvis-backend.service.d/override.conf
[Service]
Environment="GOOGLE_API_KEY=sua_chave_gemini"
Environment="GOOGLE_APPLICATION_CREDENTIALS=/etc/sua_chave_vertex.json"
Environment="VERTEXAI_PROJECT=seu_projeto"
EOF'
sudo systemctl daemon-reload
```
Por padrão, ao instalar via `.rpm` e recarregar, execute `sudo systemctl enable --now jarvis-backend` e o servidor iniciará junto com a máquina.

## Operação e Uso Local (Dev)
- **Modo Desenvolvedor (Terminal):** Se você quer apenas rodar o repositório sem instalar, exporte as variáveis no bash, rode `pip install -r requirements.txt`, inicie o backend com `./scripts/run_backend_local.sh` e o frontend com `python3 src/frontend/app.py`.
- **Hotswap no Frontend:** Você pode selecionar novos modelos pelo Dropdown. A opção `"Customizado (Digitar ID)"` permite injetar um nome não listado. O mesmo ocorre no dropdown de `"Regiões"` (útil para Llama MAAS). As escolhas persistem sessão a sessão.
- **Interrupção:** O botão "KILL SWITCH" aborta via PID Group a execução presa e devolve o motor pro idle.

## Divisão e Distinção de Ambientes
Este repositório respeita regras arquiteturais pesadas:
- **Ambiente Atual (Agente Jarvis):** A IA operária que lê esse repositório roda do terminal restrito local e possui como fonte da verdade estrita o `~/jarvis_rules.txt`. Ela tem um diário em `MemoriaDoJarvis.log`. **Isso é interno ao desenvolvimento do Jarvis e não um requisito futuro do Produto em /opt.**
- **Produto Instalável (Mark Alfa):** A instalação no diretório global `/opt/jarvis/` pertence a uma abstração diferente. O estado persistente dinâmico é salvo em `~/Documents/JarvisMark` do usuário final do sistema pra evitar falhas de permissão no root.

---
Desenvolvido por Gaia Works. O ecossistema completo dos Contratos JSON WS reside em `AgentContext/`.
