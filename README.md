# Mark Alfa

Este é o repositório oficial do Mark Alfa, um sistema de agente de IA local composto por:
- **Backend (Python)**: Um servidor WebSocket que encapsula o Open Interpreter, gerenciado como um serviço `systemd`.
- **Frontend (Python)**: Uma interface gráfica nativa em CustomTkinter que atua como cliente WebSocket para controle e visualização.

## Pré-requisitos e Dependências

A instalação via pacotes RPM/DEB lida com a cópia dos arquivos da aplicação, mas o ambiente da máquina de destino precisa ser preparado pelo operador.

### 1. Requisitos do Sistema
- **SO**: Fedora (RPM) ou Ubuntu/Debian (DEB).
- **Python**: Versão **3.12**. Versões mais recentes (como 3.14+) podem causar falhas de compilação em dependências críticas como o `tiktoken`.
- **Dependências de Sistema**: `systemd`, `python3.12-venv`.
- **Hardware**: CPU x86-64 com suporte a instruções AVX. Arquiteturas mais antigas exigirão compilação manual de dependências como `numpy`.

### 2. Dependências Python
O instalador criará um ambiente virtual em `/opt/jarvis/venv` e instalará as seguintes bibliotecas via `pip`. É responsabilidade do operador garantir que o `pip` e as ferramentas de build (`gcc`, `rust`, etc.) estejam disponíveis.
- `websockets`
- `psutil`
- `open-interpreter` (e suas sub-dependências como `litellm`, `google-cloud-aiplatform`)
- `customtkinter`
- `setuptools<70.0.0` (crítico para compatibilidade)
- `numpy==1.26.4` (se compilando em hardware antigo)

### 3. Configuração de Credenciais (Responsabilidade do Operador)
O Mark Alfa **não** gerencia credenciais. Ele apenas consome variáveis de ambiente que devem ser previamente configuradas.

**Opção A: Modelos via API Key (Ex: `gemini/...`)**
- Use para modelos como `gemini/gemini-pro`.
- A aplicação procura pela variável `GOOGLE_API_KEY`.

**Opção B: Modelos via Vertex AI (Ex: `vertex_ai/...`)**
- Use para modelos como o padrão `gemini/gemini-3.1-pro-preview` ou `vertex_ai/llama-4...`.
- A aplicação procura por:
  - `GOOGLE_APPLICATION_CREDENTIALS`: Caminho absoluto para o arquivo JSON da sua conta de serviço.
  - `VERTEXAI_PROJECT`: O ID do seu projeto no Google Cloud.
  - `VERTEXAI_LOCATION_DEFAULT`: A região padrão (opcional, fallback para `us-east5`).

**Como configurar para o serviço `systemd`:**
Crie um arquivo de override para injetar as variáveis no ambiente do serviço:
```bash
# Crie o diretório se não existir
sudo mkdir -p /etc/systemd/system/jarvis-backend.service.d

# Crie o arquivo de configuração
sudo bash -c 'cat << EOF > /etc/systemd/system/jarvis-backend.service.d/override.conf
[Service]
Environment="GOOGLE_API_KEY=SUA_CHAVE_AQUI"
Environment="GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/seu/arquivo.json"
Environment="VERTEXAI_PROJECT=seu-projeto-gcp"
Environment="VERTEXAI_LOCATION_DEFAULT=us-east5"
EOF'

# Recarregue o systemd
sudo systemctl daemon-reload
```

## Instalação e Uso

### 1. Instalação via Pacotes
- **Localize os pacotes `.rpm` ou `.deb`** gerados na raiz do repositório.
- **Instale** usando o gerenciador de pacotes do seu sistema:
  - Fedora: `sudo rpm -ivh jarvis-backend-*.rpm && sudo rpm -ivh jarvis-frontend-*.rpm --nodeps`
  - Ubuntu/Debian: `sudo dpkg -i jarvis-backend-*.deb && sudo dpkg -i jarvis-frontend-*.deb`
  (Nota: pode ser necessário `sudo apt-get install -f` para resolver dependências como `python3-tk`).

### 2. Pós-Instalação
- **Backend**: O serviço `jarvis-backend` será habilitado para iniciar no boot. Controle-o com:
  - `sudo systemctl start jarvis-backend`
  - `sudo systemctl stop jarvis-backend`
  - `sudo systemctl status jarvis-backend`
  - `sudo journalctl -u jarvis-backend -f` (para ver os logs em tempo real)
- **Frontend**: Um launcher "Mark Alfa" será criado no seu menu de aplicativos.

### 3. Funcionalidades da Interface
- **Seleção de Modelo**: Escolha um dos modelos pré-configurados ou selecione "Customizado" para digitar um ID de modelo do LiteLLM.
- **Seleção de Região**: Escolha uma região ou selecione "Customizada" para usar uma diferente. A mudança é aplicada em tempo real (hotswap).

## Política de Diretórios e Contexto
- **Diretório de Instalação**: A aplicação é instalada em `/opt/jarvis/` (backend, frontend e venv).
- **Contexto Dinâmico**: Os arquivos de execução (logs, `config.json`) são salvos dinamicamente no diretório do usuário que executa o processo (para o backend, será o usuário `root` se não for alterado no `override.conf`). O caminho padrão é `~/Documents/JarvisMark`.

## Referência do Agente Desenvolvedor
O agente (Jarvis) que desenvolveu este projeto opera em um ambiente separado em `/home/francisco/Documentos/JarvisMinion`, seguindo as regras de seu próprio arquivo de constituição (`~/jarvis_rules.txt`). Esta é uma referência do ambiente de desenvolvimento e não um requisito para o produto Mark Alfa.
