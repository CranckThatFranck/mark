# Mark Alfa

Mark Alfa e um agente local Gemini-only com duas partes:
- backend Python em daemon `systemd`, encapsulando o Open Interpreter;
- frontend desktop em Python + CustomTkinter, falando com o backend por WebSocket/JSON.

Esta arvore continua o projeto existente e preserva a arquitetura ja consolidada da branch `markWorking`.

## Resumo operacional

- projeto Gemini-only: o backend aceita apenas modelos com prefixo `gemini/`
- modelo padrao atual: `gemini/gemini-3.1-pro-preview-customtools`
- cadeia obrigatoria de fallback automatico:
  - `gemini/gemini-3.1-pro-preview-customtools`
  - `gemini/gemini-3.1-pro-preview`
  - `gemini/gemini-2.5-pro`
  - `gemini/gemini-3-flash-preview`
- catalogo nativo adicional:
  - `gemini/gemini-2.5-flash`
- destino padrao do frontend instalado: `ws://127.0.0.1:8765`
- logs tecnicos do produto instalado: `/var/log/jarvis/`

## Arquitetura preservada

- backend principal: [src/backend/server.py](/home/francisco/Documentos/repos/mark/src/backend/server.py)
- runner do agente: [src/backend/agent_runner.py](/home/francisco/Documentos/repos/mark/src/backend/agent_runner.py)
- saneamento de tool calls: [src/backend/tool_sanitizer.py](/home/francisco/Documentos/repos/mark/src/backend/tool_sanitizer.py)
- credenciais Gemini: [src/backend/credentials.py](/home/francisco/Documentos/repos/mark/src/backend/credentials.py)
- observabilidade: [src/backend/observability.py](/home/francisco/Documentos/repos/mark/src/backend/observability.py)
- frontend desktop: [src/frontend/app.py](/home/francisco/Documentos/repos/mark/src/frontend/app.py)
- contrato WebSocket: [DevJarvis/mark-alfa-websocket.md](/home/francisco/Documentos/repos/mark/DevJarvis/mark-alfa-websocket.md)

## Modelos Gemini

Modelos builtin devolvidos pelo backend:
- `gemini/gemini-3.1-pro-preview-customtools`
- `gemini/gemini-3.1-pro-preview`
- `gemini/gemini-2.5-pro`
- `gemini/gemini-3-flash-preview`
- `gemini/gemini-2.5-flash`

Modelos extras:
- qualquer modelo Gemini digitado manualmente no frontend com prefixo `gemini/`

Modelos rejeitados:
- qualquer modelo nao-Gemini, incluindo GPT, Claude e Vertex legado

## Saneamento de tool calling

O backend agora trata tool calls invalidas antes que um `function.arguments` malformado interrompa a tarefa.

Fluxo real:
1. toda mensagem outbound e todo completion inbound passam por uma camada de saneamento LiteLLM/Open Interpreter;
2. `function.arguments` e `function_call.arguments` sao convertidos para JSON canonico sempre que isso for possivel;
3. chamadas `execute` recebem tratamento especial:
   - string simples vira `{"code":"..."}`
   - literal Python vira JSON canonico
   - objetos/listas sao normalizados
   - payload invalido e envelopado de forma segura em vez de quebrar `json.loads()`
4. quando um payload invalido ainda escapa e gera erro recuperavel, o runner classifica esse erro como `invalid_tool_payload`, registra o evento e tenta retomar a tarefa sem reiniciar do zero

Eventos relevantes gerados no log estruturado:
- `tool_call_payload_sanitized`
- `invalid_tool_payload_detected`
- `tool_call_payload_retry`

## Fallback automatico de modelo

O fallback automatico e executado pelo backend, nunca pelo frontend.

Politica:
- tool call invalida ou payload invalido nao dispara fallback imediatamente
- primeiro o backend tenta saneamento e retomada da tarefa
- erro de quota pode acionar rotacao automatica da proxima API key Gemini persistida
- se nao houver outra chave persistida util, ou se a falha for de provider/rate limit/token limit, o backend tenta a proxima etapa da cadeia de fallback

Ordem obrigatoria:
1. `gemini/gemini-3.1-pro-preview-customtools`
2. `gemini/gemini-3.1-pro-preview`
3. `gemini/gemini-2.5-pro`
4. `gemini/gemini-3-flash-preview`

Erros recuperaveis tratados:
- quota esgotada
- rate limit
- indisponibilidade temporaria do provider
- token/context limit

Eventos relevantes:
- `quota_limit_detected`
- `rate_limit_detected`
- `provider_unavailable_detected`
- `token_limit_detected`
- `model_fallback_success`
- `model_fallback_switch_failed`
- `model_fallback_exhausted`

Sinalizacao ao operador:
- o frontend recebe uma mensagem tecnica explicita quando o fallback automatico entra
- o `sync_state` tambem e atualizado com o novo modelo ativo

## API keys Gemini

O backend agora suporta varias API keys Gemini gerenciadas pelo proprio produto.

### Fontes de credencial

Ordem de prioridade em runtime:
1. chave persistida marcada como ativa no produto
2. `GOOGLE_API_KEY` ou `GEMINI_API_KEY` do ambiente, apenas quando nao existir chave persistida ativa

Isso permite:
- instalacao via daemon com credencial persistida do produto
- fallback para variavel de ambiente Gemini em ambientes mais simples
- rotacao manual sem depender exclusivamente de override de ambiente

### Persistencia

Arquivo de credenciais do produto:
- `estado/credentials.json` dentro do base dir ativo do produto

Em instalacoes novas, o base dir tende a ser:
- `/var/lib/jarvis-mark`

Em hosts atualizados que ja tinham arvores legadas, o backend preserva automaticamente o base dir legado encontrado:
- `/root/Documents/JarvisMark`
- `/root/Documentos/JarvisMark`
- `/root/JarvisMark`

Seguranca:
- o arquivo de credenciais e salvo com permissao `0600`
- a pasta de estado usada para credenciais e forçada para `0700` quando possivel
- segredos completos nunca saem em `sync_state`, `get_config`, logs estruturados, eventos do frontend ou README

### Rotacao

Rotacao manual:
- o operador pode cadastrar, editar, selecionar e rotacionar a chave ativa pelo frontend

Rotacao automatica:
- em erro de quota, o backend tenta a proxima chave persistida antes de cair para o proximo modelo da cadeia
- a rotacao automatica atualiza o estado publicado ao frontend e registra:
  - `gemini_api_key_rotated_auto`
  - `frontend_notified_runtime_state_change`

## Frontend do operador

O frontend agora entrega:
- confirmacao explicita quando a troca manual de modelo funciona
- confirmacao explicita quando a troca manual de modelo falha
- menu de selecao da API key Gemini ativa
- cadastro manual de nova chave
- edicao de label e segredo de uma chave existente
- selecao manual da chave ativa
- rotacao manual da chave ativa
- painel tecnico com feedback operacional sobre fallback, reconexao e trocas de chave/modelo

Mensagens visiveis importantes:
- `Troca manual de modelo confirmada com sucesso: ...`
- `Falha na troca manual de modelo para ...`
- `API key Gemini cadastrada com sucesso.`
- `API key Gemini atualizada com sucesso.`
- `API key Gemini ativa alterada manualmente.`
- `Rotacao manual da API key Gemini concluida.`
- `Fallback automatico de modelo ativado: ...`

## Observabilidade em `/var/log/jarvis/`

O produto instalado agora escreve logs tecnicos claros em `/var/log/jarvis/`.

Arquivos:
- `/var/log/jarvis/backend.log`
- `/var/log/jarvis/operations.log`
- `/var/log/jarvis/errors.log`

Finalidade:
- `backend.log`: log textual tradicional do backend
- `operations.log`: eventos estruturados de fluxo operacional
- `errors.log`: erros estruturados e falhas fatais

Eventos rastreados incluem:
- boot do backend
- abertura/fechamento/reconexao do frontend
- inicio/fim de tarefa
- erro fatal
- troca manual de modelo com sucesso ou falha
- fallback automatico
- quota/rate limit/token limit/provider unavailable
- tool call invalida
- saneamento de payload
- aplicacao de API key ativa
- cadastro, selecao, edicao e rotacao de chaves

Os logs estruturados passam por redacao de campos sensiveis para evitar vazamento de segredo completo.

## Persistencia e diretorios

Produto instalado:
- codigo: `/opt/jarvis/backend`, `/opt/jarvis/frontend`, `/opt/jarvis/venv`
- estado: `/var/lib/jarvis-mark` em instalacoes novas, com preservacao de arvores legadas quando existentes
- logs: `/var/log/jarvis`

Arquivos dinamicos principais:
- `estado/config.json`
- `estado/session.json`
- `estado/credentials.json`
- `logs/backend.log`
- `logs/operations.log`
- `logs/errors.log`
- `logs/change.log`
- `memoria/MemoriaDoJarvis.log`

## Regras iniciais do produto

Arquivo oficial:
- `/opt/jarvis/backend/product_config/initial_rules.txt`

Na arvore do repositorio:
- [src/backend/product_config/initial_rules.txt](/home/francisco/Documentos/repos/mark/src/backend/product_config/initial_rules.txt)

O frontend expoe:
- `Abrir regras`
- `Abrir pasta das regras`
- atalho `Ctrl+Shift+R`

## Dependencias

Backend: [requirements-backend.txt](/home/francisco/Documentos/repos/mark/requirements-backend.txt)
- `setuptools<70.0.0`
- `numpy<2`
- `websockets>=15,<16`
- `psutil>=5.9,<8`
- `open-interpreter`

Frontend: [requirements-frontend.txt](/home/francisco/Documentos/repos/mark/requirements-frontend.txt)
- `setuptools<70.0.0`
- `websockets>=15,<16`
- `customtkinter>=5.2,<6`

Observacao importante:
- o pin `numpy<2` evita falha de `Illegal instruction` observada nesta maquina ao importar `open-interpreter` em instalacao limpa

## Instalacao por pacote

### RPM

Gerar:

```bash
./build_rpm.sh
```

Instalar ou atualizar:

```bash
sudo rpm -Uvh ./jarvis-backend-1.0.0-*.rpm ./jarvis-frontend-1.0.0-*.rpm
```

### DEB

Gerar:

```bash
./build_deb.sh
```

Instalar:

```bash
sudo dpkg -i ./jarvis-backend_1.0.0_all.deb ./jarvis-frontend_1.0.0_all.deb
```

Os scripts de instalacao tambem garantem:
- criacao de `/var/lib/jarvis-mark`
- criacao de `/var/log/jarvis`

No frontend empacotado, o desktop entry usa:
- `Icon=/opt/jarvis/frontend/assets/jarvisicon.svg`

## Credenciais por ambiente vs credenciais persistidas

### Usando apenas ambiente

Exemplo de override do `systemd`:

```bash
sudo mkdir -p /etc/systemd/system/jarvis-backend.service.d

sudo tee /etc/systemd/system/jarvis-backend.service.d/override.conf >/dev/null <<'EOF'
[Service]
Environment="GOOGLE_API_KEY=SUA_CHAVE_AQUI"
# ou:
# Environment="GEMINI_API_KEY=SUA_CHAVE_AQUI"
EOF

sudo systemctl daemon-reload
sudo systemctl restart jarvis-backend.service
```

### Usando credenciais persistidas do produto

Fluxo recomendado:
1. abrir o frontend
2. conectar no backend
3. usar o menu `API Key Gemini ativa`
4. clicar em `Cadastrar API key Gemini...`
5. opcionalmente editar ou selecionar outra chave
6. usar `Rotacionar` quando quiser trocar a chave ativa manualmente

Comportamento:
- a chave persistida ativa passa a ter prioridade sobre `GOOGLE_API_KEY` e `GEMINI_API_KEY`
- o segredo nao volta completo para a UI
- a UI mostra apenas valor mascarado

## Execucao local de desenvolvimento

Criar venv e instalar dependencias:

```bash
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip "setuptools<70.0.0"
.venv/bin/pip install -r requirements-backend.txt -r requirements-frontend.txt
```

Subir backend local em porta alternativa:

```bash
MARK_PYTHON_BIN="$PWD/.venv/bin/python" \
MARK_BASE_DIR="$PWD/.tmp/mark-state" \
MARK_LOG_DIR="/var/log/jarvis" \
MARK_WS_PORT=8877 \
scripts/run_backend_local.sh
```

Subir frontend local apontando para essa instancia:

```bash
MARK_PYTHON_BIN="$PWD/.venv/bin/python" \
MARK_WS_HOST=127.0.0.1 \
MARK_WS_PORT=8877 \
scripts/run_frontend_local.sh
```

## Validacoes recomendadas

Backend rapido:

```bash
.venv/bin/python tests/test_backend.py
```

Smoke backend real contra instancia local:

```bash
MARK_WS_HOST=127.0.0.1 MARK_WS_PORT=8877 MARK_LOG_DIR=/var/log/jarvis .venv/bin/python tests/smoke_backend.py
```

Smoke frontend real:

```bash
MARK_WS_HOST=127.0.0.1 MARK_WS_PORT=8877 .venv/bin/python tests/smoke_frontend.py
```

Essas validacoes cobrem:
- saneamento de tool call invalida com falha controlada
- fallback automatico e rotacao automatica de chave em testes de runner
- troca manual de modelo com feedback visual
- cadastro, edicao, selecao e rotacao manual de API keys Gemini
- logs estruturados sem segredo exposto
- reconexao do frontend
- persistencia de sessao e catalogo de modelos

## Estado do projeto

Esta rodada mantem o Mark Alfa estritamente Gemini-only e nao reintroduz Vertex, GPT ou Claude.
