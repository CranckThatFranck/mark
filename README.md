# Mark Alfa

Mark Alfa e um agente local com duas partes:
- backend Python em daemon `systemd`, encapsulando o Open Interpreter;
- frontend desktop em Python + CustomTkinter, falando com o backend via WebSocket/JSON.

O projeto desta arvore e a finalizacao do produto instalavel em `/opt/jarvis`, sem confundir isso com o ambiente atual do agente desenvolvedor nesta maquina.

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
- reconexao: ao reabrir o frontend com backend vivo, a sessao ativa reaparece no handshake
- persistencia de modelos: modelos Gemini adicionados manualmente voltam na lista ao reabrir

## Arquitetura preservada

- backend: [src/backend/server.py](/home/francisco/Documentos/repos/mark/src/backend/server.py)
- frontend: [src/frontend/app.py](/home/francisco/Documentos/repos/mark/src/frontend/app.py)
- protocolo: [AgentContext/02-contrato-json-mark-alfa.md](/home/francisco/Documentos/repos/mark/AgentContext/02-contrato-json-mark-alfa.md)
- unit file: [packaging/systemd/jarvis-backend.service](/home/francisco/Documentos/repos/mark/packaging/systemd/jarvis-backend.service)

O backend e a fonte de verdade para:
- modelo atual
- modo atual
- catalogo de modelos nativos e customizados
- historico da sessao ativa

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

## Contexto operacional

Codigo instalavel:
- `/opt/jarvis/backend`
- `/opt/jarvis/frontend`
- `/opt/jarvis/venv`

Contexto dinamico do runtime:
- primeiro `~/Documents/JarvisMark`
- senao `~/Documentos/JarvisMark`
- fallback: `~/JarvisMark`
- override opcional: `MARK_BASE_DIR=/caminho/desejado`

Arquivos principais do contexto:
- `estado/config.json`
- `estado/session.json`
- `logs/backend.log`
- `logs/change.log`
- `memoria/MemoriaDoJarvis.log`

## Instalacao por pacote

### RPM

Gere os pacotes:

```bash
./build_rpm.sh
```

Instale:

```bash
sudo rpm -Uvh ./jarvis-backend-1.0.0-*.rpm ./jarvis-frontend-1.0.0-*.rpm
```

### DEB

Os arquivos de controle e scripts de pos-instalacao estao em:
- [packaging/deb/backend/control](/home/francisco/Documentos/repos/mark/packaging/deb/backend/control)
- [packaging/deb/backend/postinst](/home/francisco/Documentos/repos/mark/packaging/deb/backend/postinst)
- [packaging/deb/frontend/control](/home/francisco/Documentos/repos/mark/packaging/deb/frontend/control)
- [packaging/deb/frontend/postinst](/home/francisco/Documentos/repos/mark/packaging/deb/frontend/postinst)

Instalacao esperada:

```bash
sudo dpkg -i ./jarvis-backend_*.deb ./jarvis-frontend_*.deb
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

## Comportamento final da sessao

### Recuperacao de sessao

O backend salva a sessao ativa em `estado/session.json`.
Ao conectar ou reconectar, o frontend recebe:
- estado atual
- catalogo de modelos
- historico da sessao ativa

Se o frontend for fechado e aberto de novo enquanto o backend continua vivo, a conversa reaparece sem perder continuidade.

### Persistencia de modelos customizados

Modelos Gemini adicionados manualmente no frontend:
- sao validados pelo backend como `gemini/...`
- entram em `custom_models` no `config.json`
- reaparecem na lista do frontend no proximo handshake

## Troubleshooting

- backend nao sobe:
  - confirme `GOOGLE_API_KEY`
  - confira `sudo systemctl status jarvis-backend`
  - confira `sudo journalctl -u jarvis-backend -n 100`
- frontend abre sem conectar:
  - confirme que o backend esta em `ws://127.0.0.1:8765`
  - clique em `Sincronizar` ou reinicie o backend
- modelo customizado nao aparece:
  - use prefixo `gemini/`
  - verifique `estado/config.json`
- historico nao voltou:
  - confirme que o backend nao foi reiniciado entre o fechamento e a reabertura do frontend
  - verifique `estado/session.json`

## Ambiente atual do desenvolvedor x produto instalavel

Este repositorio trata do produto Mark Alfa instalavel.
O ambiente atual do agente desenvolvedor nesta maquina continua separado e pode citar `~/jarvis_rules.txt` ou `JarvisMinion`, mas isso e apenas referencia do ambiente do agente, nao requisito do produto distribuivel.
