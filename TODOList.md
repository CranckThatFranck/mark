## A fazer
- Corrigir empacotamento RPM/DEB, remover sobras quebradas de arquivos de servico/scripts, regenerar artefatos finais e validar instalacao/comportamento local.
- Fechar a rodada com validacoes finais, evidencias, limpeza da TODOList e relatorio de encerramento coerente com o que foi realmente executado.

## Fazendo
- Atualizar README.md, contrato JSON e documentacao impactada para refletir Gemini-only via GOOGLE_API_KEY, recuperacao de sessao, persistencia de modelos customizados e uso local/instalado.

## Feito
- 2026-04-14 Frontend CustomTkinter ajustado para consumir o catalogo do backend, remover completamente regiao/zona e melhorar a hierarquia visual do chat com conversa principal destacada e fluxo tecnico separado; reconexao com backend vivo reidrata historico e modelos persistidos na UI.
- 2026-04-14 Backend e persistencia corrigidos para operar somente com Gemini via GOOGLE_API_KEY; modelo padrao definido em `gemini/gemini-3-flash-preview`, Vertex/GPT/Claude/regiao removidos do fluxo do daemon, catalogo de modelos vindo do backend, historico da sessao ativa devolvido no handshake e modelos Gemini customizados persistidos no backend.
- 2026-04-14 Auditoria real do repositório, do serviço instalado e da documentacao concluida; reabertos itens porque o estado encontrado divergia do README/TODO e ainda havia rastros operacionais de Vertex, GPT, Claude, regiao/zona e arquivos de packaging quebrados.
