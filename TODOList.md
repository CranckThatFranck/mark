## A fazer
- Ajustar a interface do frontend para consumir somente modelos Gemini vindos do backend, remover regiao/zona e separar visualmente conversa principal, status, codigo, console e fluxo tecnico.
- Atualizar README.md, contrato JSON e documentacao impactada para refletir Gemini-only via GOOGLE_API_KEY, recuperacao de sessao, persistencia de modelos customizados e uso local/instalado.
- Corrigir empacotamento RPM/DEB, remover sobras quebradas de arquivos de servico/scripts, regenerar artefatos finais e validar instalacao/comportamento local.
- Fechar a rodada com validacoes finais, evidencias, limpeza da TODOList e relatorio de encerramento coerente com o que foi realmente executado.

## Fazendo
- Corrigir backend e persistencia para operar somente com Gemini via GOOGLE_API_KEY, definir modelo padrao `gemini/gemini-3-flash-preview`, remover Vertex/GPT/Claude/regiao, recuperar historico da sessao ativa no handshake e persistir modelos customizados Gemini.

## Feito
- 2026-04-14 Auditoria real do repositório, do serviço instalado e da documentacao concluida; reabertos itens porque o estado encontrado divergia do README/TODO e ainda havia rastros operacionais de Vertex, GPT, Claude, regiao/zona e arquivos de packaging quebrados.
