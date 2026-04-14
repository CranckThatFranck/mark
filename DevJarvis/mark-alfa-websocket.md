# Mark Alfa WebSocket/JSON

Este documento descreve o contrato operacional atual entre o frontend do Mark Alfa e o backend Python via WebSocket/JSON. O objetivo e permitir que outro cliente, incluindo um Jarvis central, controle um backend local ou remoto sem depender do frontend CustomTkinter.

## Transporte

- protocolo: WebSocket
- endpoint padrao instalado: `ws://127.0.0.1:8765`
- backend rodando via `systemd`: `jarvis-backend.service`
- contrato serializado em JSON UTF-8

Envelope enviado pelo cliente:

```json
{
  "action": "nome_da_acao",
  "payload": {}
}
```

Resposta sincronizada:

```json
{
  "type": "action_response",
  "action": "nome_da_acao",
  "success": true,
  "data": {}
}
```

Falha sincronizada:

```json
{
  "type": "action_response",
  "action": "nome_da_acao",
  "success": false,
  "error": "descricao"
}
```

## Handshake inicial

Assim que a conexao e aceita, o backend envia `sync_state` sem o cliente precisar pedir.

Exemplo resumido:

```json
{
  "type": "sync_state",
  "state": {
    "mode": "agent",
    "model": "gemini/gemini-3.1-pro-preview-customtools",
    "status": "idle",
    "active_task": null,
    "history_revision": 12,
    "fallback_chain": [
      "gemini/gemini-3.1-pro-preview-customtools",
      "gemini/gemini-3.1-pro-preview",
      "gemini/gemini-2.5-pro",
      "gemini/gemini-3-flash-preview"
    ],
    "credentials": {
      "active_key_id": "abc123",
      "active_key_masked": "AIza...1234",
      "total_keys": 2,
      "source": "persisted",
      "keys": [
        {
          "id": "abc123",
          "label": "Principal",
          "masked": "AIza...1234",
          "is_active": true
        }
      ]
    },
    "paths": {
      "base_dir": "/var/lib/jarvis-mark",
      "rules_file": "/opt/jarvis/backend/product_config/initial_rules.txt",
      "rules_dir": "/opt/jarvis/backend/product_config"
    }
  },
  "models": {
    "builtin": [
      "gemini/gemini-3.1-pro-preview-customtools",
      "gemini/gemini-3.1-pro-preview",
      "gemini/gemini-2.5-pro",
      "gemini/gemini-3-flash-preview",
      "gemini/gemini-2.5-flash"
    ],
    "custom": [],
    "all": []
  },
  "history": []
}
```

Observacoes:
- `history` hoje e enviado no handshake.
- `fallback_chain` sempre vem sincronizado.
- `credentials` nunca inclui segredo completo.
- `paths.rules_file` e `paths.rules_dir` permitem abrir ou editar o arquivo oficial de regras do produto.

## Eventos de stream

Durante a execucao o backend publica eventos assincronos:

```json
{
  "type": "stream",
  "message_type": "message",
  "content": "trecho da resposta",
  "timestamp": "2026-04-14T14:14:47-03:00"
}
```

Tipos usados:
- `user`
- `message`
- `status`
- `code`
- `console`
- `system`

Eventos `system` cobrem, entre outros:
- fallback automatico de modelo
- rotacao automatica de chave
- retomada apos saneamento de tool call invalida
- reconexao do frontend

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
    "model": "gemini/gemini-3.1-pro-preview-customtools"
  }
}
```

### `get_status`

Retorna o mesmo bloco `state` usado em `sync_state`.

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

Retorna configuracao persistida do backend junto com fallback e catalogo publico de credenciais:

```json
{
  "type": "action_response",
  "action": "get_config",
  "success": true,
  "data": {
    "mode": "agent",
    "model": "gemini/gemini-3.1-pro-preview-customtools",
    "custom_models": [],
    "models": {
      "builtin": [],
      "custom": [],
      "all": []
    },
    "fallback_chain": [],
    "credentials": {
      "active_key_id": "abc123",
      "active_key_masked": "AIza...1234",
      "total_keys": 2,
      "source": "persisted",
      "keys": [
        {
          "id": "abc123",
          "label": "Principal",
          "masked": "AIza...1234",
          "is_active": true
        }
      ]
    }
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
- modelos extras Gemini entram em `custom_models`
- modelos nao-Gemini retornam `success=false`

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

### `get_api_keys`

Retorna o catalogo publico de chaves persistidas:

```json
{
  "type": "action_response",
  "action": "get_api_keys",
  "success": true,
  "data": {
    "active_key_id": "abc123",
    "active_key_masked": "AIza...1234",
    "total_keys": 2,
    "keys": [
      {
        "id": "abc123",
        "label": "Principal",
        "masked": "AIza...1234",
        "is_active": true
      }
    ]
  }
}
```

### `add_api_key`

Pedido:

```json
{
  "action": "add_api_key",
  "payload": {
    "label": "Backup",
    "key": "SEGREDO_COMPLETO_AQUI",
    "set_active": true
  }
}
```

Observacao:
- o segredo completo so aparece no pedido do cliente para o backend; nunca volta integralmente na resposta

### `update_api_key`

Pedido:

```json
{
  "action": "update_api_key",
  "payload": {
    "id": "abc123",
    "label": "Principal editada",
    "key": "NOVO_SEGREDO_OPCIONAL"
  }
}
```

### `delete_api_key`

Pedido:

```json
{
  "action": "delete_api_key",
  "payload": {
    "id": "abc123"
  }
}
```

### `select_api_key`

Pedido:

```json
{
  "action": "select_api_key",
  "payload": {
    "id": "abc123"
  }
}
```

### `rotate_api_key`

Pedido:

```json
{
  "action": "rotate_api_key"
}
```

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

Comportamento:
- aceita apenas uma tarefa por vez
- responde primeiro com `action_response`
- depois transmite `stream`
- ao final volta a publicar `sync_state` com `status=idle`

### `interrupt`

Pedido:

```json
{
  "action": "interrupt"
}
```

Efeito:
- interrompe a tarefa em andamento
- reconstrói o runner do agente
- envia evento tecnico `Tarefa interrompida pelo usuario`

## Contratos importantes

- segredos completos nunca devem aparecer em `sync_state`, `get_config`, `get_api_keys` ou logs estruturados
- fallback automatico de modelo e rotacao automatica de chave sao sinalizados via `stream` do tipo `system` e por novo `sync_state`
- o backend continua Gemini-only e rejeita provedores antigos ou modelos nao-Gemini
