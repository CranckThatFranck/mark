# Mark Alfa WebSocket/JSON

Este documento descreve o contrato operacional atual entre o frontend do Mark Alfa e o backend Python via WebSocket/JSON. O objetivo e permitir que outro cliente, incluindo um Jarvis central, consiga controlar um backend local ou remoto sem depender do frontend CustomTkinter.

## Transporte

- protocolo: WebSocket
- endpoint padrao instalado: `ws://127.0.0.1:8765`
- backend rodando via `systemd`: `jarvis-backend.service`
- contrato serializado em JSON UTF-8

Cada mensagem enviada pelo cliente usa o envelope:

```json
{
  "action": "nome_da_acao",
  "payload": {}
}
```

Cada resposta sincrona do backend usa:

```json
{
  "type": "action_response",
  "action": "nome_da_acao",
  "success": true,
  "data": {}
}
```

Em falhas:

```json
{
  "type": "action_response",
  "action": "nome_da_acao",
  "success": false,
  "error": "descricao"
}
```

## Handshake inicial

Assim que uma conexao e aceita, o backend envia `sync_state` sem o cliente precisar pedir:

```json
{
  "type": "sync_state",
  "state": {
    "mode": "agent",
    "model": "gemini/gemini-3-flash-preview",
    "status": "idle",
    "active_task": null,
    "history_revision": 12,
    "paths": {
      "base_dir": "/var/lib/jarvis-mark",
      "rules_file": "/opt/jarvis/backend/product_config/initial_rules.txt",
      "rules_dir": "/opt/jarvis/backend/product_config"
    }
  },
  "models": {
    "builtin": [
      "gemini/gemini-3-flash-preview",
      "gemini/gemini-3.1-pro-preview-customtools",
      "gemini/gemini-3.1-pro-preview",
      "gemini/gemini-2.5-pro",
      "gemini/gemini-2.5-flash"
    ],
    "custom": [
      "gemini/gemini-2.5-flash-exp"
    ],
    "all": [
      "gemini/gemini-3-flash-preview",
      "gemini/gemini-3.1-pro-preview-customtools",
      "gemini/gemini-3.1-pro-preview",
      "gemini/gemini-2.5-pro",
      "gemini/gemini-2.5-flash",
      "gemini/gemini-2.5-flash-exp"
    ]
  },
  "history": [
    {
      "message_type": "user",
      "content": "Responda apenas com a palavra teste.",
      "timestamp": "2026-04-14T14:14:46-03:00"
    }
  ]
}
```

Observacoes:

- `history` sempre vem no handshake atual.
- `paths.rules_file` e `paths.rules_dir` permitem a um cliente externo abrir ou editar o arquivo padrao de regras iniciais do produto instalado.
- `history_revision` ajuda um cliente a saber se houve mudanca de historico entre sincronizacoes.

## Eventos de stream

Durante uma execucao o backend publica eventos assíncronos:

```json
{
  "type": "stream",
  "message_type": "message",
  "content": "trecho da resposta",
  "timestamp": "2026-04-14T14:14:47-03:00"
}
```

Tipos hoje usados:

- `user`: prompt do operador
- `message`: resposta principal do agente
- `status`: estado operacional
- `code`: bloco de codigo
- `console`: saida de terminal/execucao
- `system`: evento tecnico interno

O backend tambem persiste esses eventos no historico da sessao ativa.

## Acoes suportadas

### `healthcheck`

Pedido:

```json
{"action": "healthcheck"}
```

Resposta:

```json
{
  "type": "action_response",
  "action": "healthcheck",
  "success": true,
  "data": {
    "status": "ok",
    "model": "gemini/gemini-3-flash-preview"
  }
}
```

### `get_status`

Retorna o mesmo bloco estrutural de `state` usado em `sync_state`.

### `get_models`

Retorna o catalogo Gemini completo:

```json
{
  "type": "action_response",
  "action": "get_models",
  "success": true,
  "data": {
    "builtin": [],
    "custom": [],
    "all": []
  }
}
```

### `get_config`

Retorna configuracao persistida do backend:

```json
{
  "type": "action_response",
  "action": "get_config",
  "success": true,
  "data": {
    "mode": "agent",
    "model": "gemini/gemini-3-flash-preview",
    "custom_models": []
  }
}
```

### `update_config`

Atualiza configuracao persistida do backend.

Pedido:

```json
{
  "action": "update_config",
  "payload": {
    "config": {
      "mode": "plan",
      "model": "gemini/gemini-2.5-flash"
    }
  }
}
```

Efeitos:

- altera `mode` e/ou `model`
- persiste `estado/config.json`
- dispara novo `sync_state` para conexoes ativas
- responde com `action_response`

### `change_model`

Atalho focado em troca de modelo.

Pedido:

```json
{
  "action": "change_model",
  "payload": {
    "model": "gemini/gemini-2.5-flash"
  }
}
```

Regras:

- somente modelos `gemini/`
- os modelos builtin sao fixos
- modelos Gemini extras podem ser adicionados manualmente
- se o modelo nao for builtin e respeitar `gemini/`, ele entra em `custom_models`

### `change_mode`

Pedido:

```json
{
  "action": "change_mode",
  "payload": {
    "mode": "agent"
  }
}
```

Valores aceitos:

- `agent`
- `plan`

### `execute_task`

Pedido:

```json
{
  "action": "execute_task",
  "payload": {
    "prompt": "Explique o estado atual do repositorio."
  }
}
```

Fluxo:

1. backend responde `action_response` com `success=true`
2. backend publica `stream` com `message_type=user`
3. backend publica eventos `status`, `message`, `code`, `console` e `system`
4. backend atualiza `state.status` para `running`
5. ao terminar, faz broadcast de `sync_state` com `status=idle`

Se ja existir tarefa em andamento, responde erro:

```json
{
  "type": "action_response",
  "action": "execute_task",
  "success": false,
  "error": "Uma tarefa ja esta em execucao"
}
```

### `interrupt`

Interrompe a tarefa em execucao e recria o `AgentRunner`.

Pedido:

```json
{"action": "interrupt"}
```

Efeitos:

- encerra subprocessos do interpretador quando presentes
- reseta estado de execucao
- publica evento `system` com interrupcao
- faz broadcast de `sync_state`

### Acao desconhecida

Qualquer acao nao implementada recebe:

```json
{
  "type": "action_response",
  "action": "acao_desconhecida",
  "success": false,
  "error": "Acao desconhecida"
}
```

## Historico da sessao

O historico e persistido em `estado/session.json` dentro do `base_dir` ativo do backend.

Campos por item:

- `message_type`
- `content`
- `timestamp`

Mesclagem atual:

- `message`, `code` e `console` consecutivos podem ser concatenados no backend para formar blocos maiores.

## Reconexao e tolerancia a falhas

Comportamento esperado para clientes remotos:

- `ConnectionClosedError`, handshake interrompido e `no close frame received or sent` nao significam queda fatal do daemon;
- se o cliente reconectar, ele recebe novo `sync_state` com o historico da sessao ativa;
- durante tarefas longas o backend continua aceitando novas conexoes, porque o streaming do agente nao bloqueia mais o loop principal de rede.

## Regras iniciais do produto instalado

O backend instalado usa como referencia global inicial:

- `/opt/jarvis/backend/product_config/initial_rules.txt`

Esse arquivo:

- nao substitui `~/jarvis_rules.txt` do ambiente do agente desenvolvedor;
- e o caminho oficial do produto distribuido;
- aparece em `sync_state.state.paths.rules_file`.

## Integracao remota recomendada

Para um Jarvis central falando com varios backends Mark Alfa:

1. abrir WebSocket no endpoint remoto
2. aguardar `sync_state`
3. armazenar `state`, `models`, `history` e `paths`
4. usar `change_model` e `change_mode` conforme o perfil da tarefa
5. disparar `execute_task`
6. consumir `stream`
7. em reconexao, confiar no novo `sync_state` para reidratar sessao

## Fontes no repositorio

- backend: [src/backend/server.py](/home/francisco/Documentos/repos/mark/src/backend/server.py)
- protocolo: [src/backend/protocol.py](/home/francisco/Documentos/repos/mark/src/backend/protocol.py)
- estado: [src/backend/state.py](/home/francisco/Documentos/repos/mark/src/backend/state.py)
- cliente WebSocket do frontend: [src/frontend/ws_client.py](/home/francisco/Documentos/repos/mark/src/frontend/ws_client.py)
