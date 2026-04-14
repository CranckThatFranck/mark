## A fazer
- Nenhum item pendente nesta rodada.

## Fazendo
- Nenhum item em andamento.

## Feito
- 2026-04-14 Rodada reaberta apenas nos itens impactados por saneamento de tool calling, fallback Gemini, observabilidade, credenciais persistidas e validacoes finais.
- 2026-04-14 Backend endurecido para tool calling Gemini com camada de saneamento em `src/backend/tool_sanitizer.py` e retomada controlada em `src/backend/agent_runner.py`, evitando que `function.arguments` invalido derrube a continuidade da tarefa quando houver recuperacao possivel.
- 2026-04-14 Diferenciacao operacional consolidada entre payload/tool call invalida e falhas recuperaveis de provider: o runner prioriza saneamento para `invalid_tool_payload` e so entra em fallback para quota, rate limit, indisponibilidade temporaria e token/context limit.
- 2026-04-14 Politica de fallback automatico consolidada no backend com cadeia fixa `gemini/gemini-3.1-pro-preview-customtools -> gemini/gemini-3.1-pro-preview -> gemini/gemini-2.5-pro -> gemini/gemini-3-flash-preview`, com notificacao ao frontend e logs estruturados do motivo da troca.
- 2026-04-14 Suporte a varias API keys Gemini persistidas concluido: o backend agora cadastra, edita, seleciona e rotaciona a chave ativa, grava `estado/credentials.json` com permissao restrita e usa a chave persistida ativa com fallback para `GOOGLE_API_KEY` apenas quando nao houver chave do produto ativa.
- 2026-04-14 Rotacao automatica de chave Gemini antes do fallback de modelo concluida para erro de quota, com atualizacao de estado enviada ao frontend e sem exposicao do segredo completo em `sync_state`, `get_config`, logs ou eventos.
- 2026-04-14 Frontend concluido com confirmacao explicita de troca manual de modelo com sucesso ou falha e com operacao manual de API keys Gemini pela barra lateral.
- 2026-04-14 Observabilidade tecnica consolidada em `/var/log/jarvis/` com `backend.log`, `operations.log` e `errors.log`, cobrindo inicio/fim de tarefa, reconexao do frontend, saneamento de payload, tool call invalida, quota, rate limit, token limit, fallback e erros fatais.
- 2026-04-14 README reescrito para documentar logs em `/var/log/jarvis/`, fallback automatico entre modelos, rotacao de chaves Gemini, diferenca entre credenciais de ambiente e credenciais persistidas do produto e o fluxo de operacao pelo frontend.
- 2026-04-14 Suite de validacao atualizada para cobrir credenciais persistidas, edicao/selecao/rotacao de API keys, mascaramento de segredos, fallback do runner e saneamento de tool call.
- 2026-04-14 Dependencias estabilizadas para instalacao limpa: `requirements-backend.txt` passou a fixar `numpy<2` para evitar `Illegal instruction` observado nesta maquina ao importar `open-interpreter` via instalacao nova.
