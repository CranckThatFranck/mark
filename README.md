# Mark Alfa

Mark Alfa e um agente local com duas partes:
- backend Python em daemon `systemd`, encapsulando o Open Interpreter;
- frontend desktop em Python + CustomTkinter, falando com o backend via WebSocket/JSON.

Esta arvore finaliza o produto instalavel em `/opt/jarvis`, sem confundir isso com o ambiente atual do agente desenvolvedor nesta maquina.

## Visao geral final

- backend padrao: `gemini/gemini-3-flash-preview`
- modelos nativos suportados:
  - `gemini/gemini-3-flash-preview`
  - `gemini/gemini-3.1-pro-preview-customtools`
  - `gemini/gemini-3.1-pro-preview`
  - `gemini/gemini-2.5-pro`
  - `gemini/gemini-2.5-flash`
- modelos extras: qualquer modelo Gemini informado manualmente no frontend com prefixo `gemini/`
- credencial consumida pela aplicacao: somente `GOOGLE_API_KEY`
- transporte: quando o backend continua vivo e ocorre erro de WebSocket/handshake/transporte, o frontend trata isso como falha temporaria de comunicacao e tenta reconectar automaticamente
- sessao: no handshake inicial ou de reconexao o frontend recebe estado, catalogo de modelos e historico persistido da sessao ativa
- UX: conversa principal dominante, painel tecnico secundario colapsavel e redimensionavel, autoscroll operacional, texto selecionavel por mouse, timestamps visiveis, botoes de copiar e input multilinha com `Shift+Enter`

## Arquitetura preservada

- backend: [src/backend/server.py](/home/francisco/Documentos/repos/mark/src/backend/server.py)
- frontend: [src/frontend/app.py](/home/francisco/Documentos/repos/mark/src/frontend/app.py)
- cliente WebSocket do frontend: [src/frontend/ws_client.py](/home/francisco/Documentos/repos/mark/src/frontend/ws_client.py)
- protocolo: [AgentContext/02-contrato-json-mark-alfa.md](/home/francisco/Documentos/repos/mark/AgentContext/02-contrato-json-mark-alfa.md)
- unit file: [packaging/systemd/jarvis-backend.service](/home/francisco/Documentos/repos/mark/packaging/systemd/jarvis-backend.service)

O backend e a fonte de verdade para:
- modelo atual
- modo atual
- catalogo de modelos nativos e customizados
- historico da sessao ativa
- caminhos operacionais relevantes, incluindo o arquivo de regras iniciais do produto

## Requisitos

### Sistema

- Fedora para `.rpm` ou Debian/Ubuntu para `.deb`
- Python 3.12
- `systemd`
- ambiente grafico para o frontend

### Dependencias Python

Backend: [requirements-backend.txt](/home/francisco/Documentos/repos/mark/requirements-backend.txt)
- `open-interpreter`
- `websockets`
- `psutil`

Frontend: [requirements-frontend.txt](/home/francisco/Documentos/repos/mark/requirements-frontend.txt)
- `customtkinter`
- `websockets`

Os pacotes criam ou reaproveitam `/opt/jarvis/venv` e instalam essas dependencias nele.

## Credenciais

O Mark Alfa nao gerencia credenciais. O operador humano precisa deixar `GOOGLE_API_KEY` disponivel no ambiente do processo.

Exemplo de override do `systemd`:

```bash
sudo mkdir -p /etc/systemd/system/jarvis-backend.service.d

sudo tee /etc/systemd/system/jarvis-backend.service.d/override.conf >/dev/null <<'EOF'
[Service]
Environment="GOOGLE_API_KEY=SUA_CHAVE_AQUI"
EOF

sudo systemctl daemon-reload
sudo systemctl restart jarvis-backend.service
```

## Contexto operacional e persistencia

### Codigo instalavel

- `/opt/jarvis/backend`
- `/opt/jarvis/frontend`
- `/opt/jarvis/venv`

### Politica atual de persistencia

Para o produto instalado, a politica preferencial agora e:
- estado e trilha operacional em `/var/lib/jarvis-mark`
- diretoria criada tambem pelo `systemd` via `StateDirectory=jarvis-mark`

Para nao quebrar a instalacao atual desta maquina, o backend preserva automaticamente um contexto legado ja existente sob:
- `/root/Documents/JarvisMark`
- `/root/Documentos/JarvisMark`
- `/root/JarvisMark`

Se nenhuma dessas arvores legadas existir, o backend instalado passa a usar `/var/lib/jarvis-mark`.

Em execucao local de desenvolvimento, a politica continua:
- primeiro `~/Documents/JarvisMark`
- senao `~/Documentos/JarvisMark`
- fallback: `~/JarvisMark`
- override opcional: `MARK_BASE_DIR=/caminho/desejado`

### Arquivos principais do contexto dinamico

- `estado/config.json`
- `estado/session.json`
- `logs/backend.log`
- `logs/change.log`
- `memoria/MemoriaDoJarvis.log`

## Arquivo padrao de regras iniciais

O arquivo padrao de regras globais do produto instalado e:

- `/opt/jarvis/backend/product_config/initial_rules.txt`

No codigo-fonte desta arvore, o mesmo arquivo esta em:

- [src/backend/product_config/initial_rules.txt](/home/francisco/Documentos/repos/mark/src/backend/product_config/initial_rules.txt)

Comportamento real do backend:
- no boot, o backend garante que esse arquivo exista
- o conteudo e carregado como referencia global inicial do agente
- hoje esse conteudo e injetado em `interpreter.custom_instructions`, preservando o `system_message` base do Open Interpreter

No frontend:
- botao `Abrir regras`
- botao `Abrir pasta das regras`
- atalho `Ctrl+Shift+R` para abrir rapidamente esse arquivo

Importante:
- esse arquivo do produto instalado e distinto do `~/jarvis_rules.txt` citado no ambiente atual do agente desenvolvedor
- `~/jarvis_rules.txt` nao faz parte do contrato do produto distribuivel

## Comportamento de conexao e reconexao

### Quando tudo esta normal

Ao conectar, o frontend recebe:
- `sync_state`
- catalogo de modelos
- historico completo da sessao ativa

### Quando o backend continua vivo, mas o transporte falha

Exemplos:
- `ConnectionClosedError`
- `no close frame received or sent`
- handshake interrompido
- cliente fechado ou abortado no meio da conexao

Comportamento final:
- o backend nao trata isso como queda fatal do daemon
- handshakes abortados deixam de poluir o fluxo principal como erro fatal no log do servico
- o frontend mostra falha temporaria de comunicacao em vez de queda definitiva do backend
- a UI continua tentando reconectar automaticamente
- quando a reconexao entra, o historico da sessao ativa reaparece pelo handshake

## Frontend final

O frontend agora entrega:
- conversa principal visualmente dominante
- painel tecnico como trilha secundaria
- painel tecnico colapsavel
- painel tecnico redimensionavel verticalmente pelo usuario
- autoscroll na conversa principal e no painel tecnico quando o usuario esta no fim
- preservacao da leitura quando o usuario sobe manualmente para revisar mensagens antigas
- campo de entrada multilinha com crescimento vertical conforme novas linhas
- `Shift+Enter` para quebra de linha
- `Enter` simples para envio
- texto copiavel por selecao com mouse nas mensagens e nos eventos tecnicos
- timestamps visiveis nas mensagens principais e nos eventos tecnicos
- botoes `Copiar` nas mensagens, saidas tecnicas, codigo e console

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

## Backend via systemd

Comandos principais:

```bash
sudo systemctl start jarvis-backend
sudo systemctl stop jarvis-backend
sudo systemctl restart jarvis-backend
sudo systemctl status jarvis-backend
sudo journalctl -u jarvis-backend -f
```

## Frontend e launcher

O launcher grafico instalado e [packaging/frontend/desktop/mark-alfa.desktop](/home/francisco/Documentos/repos/mark/packaging/frontend/desktop/mark-alfa.desktop).

Com o pacote instalado, o frontend abre por:
- menu de aplicativos: `Mark Alfa`
- ou manualmente: `/opt/jarvis/venv/bin/python /opt/jarvis/frontend/app.py`

## Uso local sem instalar

Backend:

```bash
./scripts/run_backend_local.sh
```

Frontend:

```bash
./scripts/run_frontend_local.sh
```

Esses scripts preferem `/opt/jarvis/venv/bin/python` quando ele ja existe.

## Testes e validacao local desta rodada

Os principais testes locais usados nesta rodada foram:
- [tests/test_backend.py](/home/francisco/Documentos/repos/mark/tests/test_backend.py)
- [tests/smoke_backend.py](/home/francisco/Documentos/repos/mark/tests/smoke_backend.py)
- [tests/smoke_frontend.py](/home/francisco/Documentos/repos/mark/tests/smoke_frontend.py)

O smoke do frontend cobre:
- conexao ao backend
- troca de modelo
- envio de multiplas mensagens
- autoscroll da conversa principal
- autoscroll do painel tecnico
- preservacao de leitura ao sair manualmente do fim do chat
- input multilinha expansivel
- `Shift+Enter` para nova linha e `Enter` para envio
- falha temporaria de transporte com reconexao
- reidratacao do historico apos reconexao
- painel tecnico colapsavel
- timestamps e copia para area de transferencia

## Troubleshooting

- backend nao sobe:
  - confirme `GOOGLE_API_KEY`
  - confira `sudo systemctl status jarvis-backend`
  - confira `sudo journalctl -u jarvis-backend -n 100`
- frontend abre sem conectar:
  - confirme que o backend esta em `ws://127.0.0.1:8765`
  - aguarde a reconexao automatica ou clique em `Sincronizar`
- frontend mostra falha temporaria de comunicacao:
  - o backend pode continuar vivo; a UI tentara reconectar sozinha
  - nas tarefas longas atuais o loop de rede do backend continua responsivo durante o streaming do agente, reduzindo timeouts de handshake na reconexao
  - confira `journalctl` para confirmar que o daemon nao caiu
- modelo customizado nao aparece:
  - use prefixo `gemini/`
  - verifique `estado/config.json`
- historico nao voltou:
  - confirme que o backend nao foi reiniciado entre o fechamento e a reabertura do frontend
  - verifique `estado/session.json`

## Produto instalavel x ambiente atual do desenvolvedor

Este repositorio trata do produto Mark Alfa instalavel.
O ambiente atual do agente desenvolvedor nesta maquina continua separado e pode citar `~/jarvis_rules.txt` ou `JarvisMinion`, mas isso e apenas referencia do ambiente do agente, nao requisito do produto distribuivel.
