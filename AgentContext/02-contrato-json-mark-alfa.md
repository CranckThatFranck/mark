# Contrato JSON do Mark Alfa

## Objetivo
Padronizar toda a comunicação entre frontend, backend e futuro master node.

## Escopo deste Contrato
Este contrato define o protocolo de comunicação do produto Mark Alfa em construção, especialmente entre:
- backend instalável do Mark
- frontend instalável do Mark
- futuro master node

Importante:
Este documento descreve o protocolo oficial do produto em construção.
Ele não redefine automaticamente o ambiente atual do agente já funcional no terminal desta máquina.

## Regra Geral
1. Toda mensagem trafega em JSON.
2. Toda mensagem deve conter `action` quando enviada ao backend.
3. Toda resposta estruturada deve conter `type`.
4. Toda resposta final de ação deve conter status.
5. O protocolo deve ser tolerante a expansão futura.

## Versão do Protocolo
Campo recomendado em todas as mensagens:
`"protocol_version": "1.0"`

## Ações de Entrada

### 1. execute_task
Uso:
Executar tarefa ou conversar com o agente.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "execute_task",
  "task": "analise os logs e diga se o serviço está saudável",
  "mode": "plan"
}

Regras:
- `task` é obrigatório
- `mode` aceita `plan` ou `agent`
- se `mode` não vier, assumir `agent`

### 2. change_model
Uso:
Trocar o modelo sem perder contexto operacional do backend.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "change_model",
  "model": "gemini/gemini-2.5-flash"
}

### 3. interrupt
Uso:
Interromper imediatamente a tarefa atual.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "interrupt"
}

### 4. get_status
Uso:
Consultar estado atual do backend.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "get_status"
}

### 5. healthcheck
Uso:
Validar se o backend está vivo e responsivo.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "healthcheck"
}

### 6. get_config
Uso:
Ler configuração persistida do agente.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "get_config"
}

### 7. update_config
Uso:
Atualizar configuração persistida do agente.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "update_config",
  "config": {
    "agent_name": "Mark 1",
    "master_host": "100.114.61.59",
    "target_host": "localhost"
  }
}

### 8. get_models
Uso:
Listar modelos disponíveis para hotswap.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "get_models"
}

### 9. shutdown_backend
Uso:
Solicitar desligamento gracioso do backend.

Exemplo:
{
  "protocol_version": "1.0",
  "action": "shutdown_backend"
}

## Tipos de Saída

### sync_state
Enviado ao conectar no WebSocket.

Exemplo:
{
  "type": "sync_state",
  "protocol_version": "1.0",
  "current_model": "gemini/gemini-3-flash-preview",
  "default_mode": "agent",
  "agent_name": "Mark 1",
  "status": "idle"
}

### system
Mensagens de sistema.

Exemplo:
{
  "type": "system",
  "message": "Conexão estabelecida com sucesso."
}

### status
Atualizações de ciclo de vida.

Exemplo START:
{
  "type": "status",
  "phase": "START",
  "action": "execute_task"
}

Exemplo END:
{
  "type": "status",
  "phase": "END",
  "action": "execute_task"
}

### user
Eco formatado da mensagem do usuário.

Exemplo:
{
  "type": "user",
  "content": "analise os logs e diga se o serviço está saudável"
}

### message
Mensagem natural do agente.

Exemplo:
{
  "type": "message",
  "content": "Analisei os logs e encontrei dois warnings, mas nenhum erro fatal."
}

### code
Código que o agente pretende executar ou gerou.

Exemplo:
{
  "type": "code",
  "language": "bash",
  "content": "journalctl -u mark-backend.service -n 100"
}

### console
Saída de execução.

Exemplo:
{
  "type": "console",
  "stream": "stdout",
  "content": "service active (running)"
}

### action_response
Resposta final estruturada.

Exemplo sucesso:
{
  "type": "action_response",
  "action": "change_model",
  "status": "success",
  "current_model": "gemini/gemini-2.5-flash"
}

Exemplo erro:
{
  "type": "action_response",
  "action": "update_config",
  "status": "error",
  "error_code": "INVALID_CONFIG",
  "message": "Campo target_host ausente ou inválido."
}

## Regras de Erro
1. Todo erro deve responder com `type = action_response`
2. Todo erro deve conter:
- `status = error`
- `error_code`
- `message`

## Regras de Compatibilidade
1. Campos novos podem ser adicionados no futuro sem quebrar clientes antigos.
2. Clientes devem ignorar campos desconhecidos.
3. Campos obrigatórios não podem ser removidos sem nova versão de protocolo.

## Regras de Coerência de Estado
1. O frontend deve refletir o estado real devolvido pelo backend.
2. O backend é a fonte de verdade para:
- modo atual
- modelo atual
- status do daemon
- configuração persistente do agente
3. O protocolo deve evitar ambiguidades entre estado visual e estado operacional real.

## Regra Final
O protocolo deve ser simples, estável e explícito.
Toda ambiguidade removida aqui economiza erros de implementação no backend, frontend e master.
