# Contrato JSON do Mark Alfa

## Objetivo

Padronizar a comunicacao entre frontend e backend do Mark Alfa.
O backend e a fonte de verdade para estado, catalogo de modelos e historico da sessao ativa.

## Regras gerais

1. Toda mensagem enviada ao backend usa JSON.
2. Toda mensagem de entrada tem `action`.
3. Toda mensagem estruturada de saida tem `type`.
4. O backend aceita apenas modelos Gemini com prefixo `gemini/`.
5. Campos desconhecidos devem ser ignorados pelos clientes para manter compatibilidade.
6. Nao existem mais campos operacionais legados de geografia ou provedores alternativos no protocolo.

## Envelope de entrada

Formato base:

```json
{
  "action": "nome_da_acao",
  "payload": {}
}
```

## Acoes de entrada

### `healthcheck`

```json
{
  "action": "healthcheck"
}
```

### `get_status`

```json
{
  "action": "get_status"
}
```

### `get_models`

```json
{
  "action": "get_models"
}
```

### `get_config`

```json
{
  "action": "get_config"
}
```

### `change_mode`

```json
{
  "action": "change_mode",
  "payload": {
    "mode": "plan"
  }
}
```

Modos validos:
- `agent`
- `plan`

### `change_model`

```json
{
  "action": "change_model",
  "payload": {
    "model": "gemini/gemini-2.5-flash"
  }
}
```

Regras:
- modelos nativos validos vem do proprio backend
- modelos customizados sao aceitos quando usam prefixo `gemini/`
- modelos invalidos retornam erro estruturado

### `update_config`

```json
{
  "action": "update_config",
  "payload": {
    "config": {
      "mode": "agent",
      "model": "gemini/gemini-3.1-pro-preview"
    }
  }
}
```

### `execute_task`

```json
{
  "action": "execute_task",
  "payload": {
    "prompt": "Analise os logs do backend."
  }
}
```

### `interrupt`

```json
{
  "action": "interrupt"
}
```

## Tipos de saida

### `sync_state`

Enviado no handshake e tambem em atualizacoes de estado.

Exemplo do handshake:

```json
{
  "type": "sync_state",
  "state": {
    "mode": "agent",
    "model": "gemini/gemini-3-flash-preview",
    "status": "idle",
    "active_task": null,
    "history_revision": 4
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
      "content": "Oi"
    },
    {
      "message_type": "message",
      "content": "Ola"
    }
  ]
}
```

Observacoes:
- `history` aparece no handshake de conexao/reconexao
- em broadcasts comuns o backend pode enviar apenas `state` e `models`

### `stream`

Fluxo incremental da sessao ativa:

```json
{
  "type": "stream",
  "message_type": "message",
  "content": "Analise concluida."
}
```

Tipos validos de `message_type`:
- `user`
- `message`
- `status`
- `code`
- `console`
- `system`

### `action_response`

```json
{
  "type": "action_response",
  "action": "change_model",
  "success": true,
  "data": {
    "model": "gemini/gemini-2.5-flash",
    "models": {
      "builtin": [],
      "custom": [],
      "all": []
    }
  }
}
```

Exemplo de erro:

```json
{
  "type": "action_response",
  "action": "change_model",
  "success": false,
  "error": "Apenas modelos Gemini com prefixo gemini/ sao suportados"
}
```

## Regras de coerencia

1. O frontend nao deve manter lista hardcoded de modelos como fonte principal.
2. O frontend deve usar o catalogo recebido do backend.
3. O frontend deve reconstruir a sessao a partir de `history` no handshake.
4. O backend deve persistir `config.json` e `session.json` no contexto operacional dinamico.
