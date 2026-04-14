## A fazer
- Fechar a rodada com evidencias finais, limpeza da TODOList e relatorio de encerramento coerente com o que foi realmente executado.

## Fazendo
- Consolidar o encerramento desta rodada no repositório, conferindo os artefatos RPM finais, os arquivos alterados e a coerencia final da TODOList.

## Feito
- 2026-04-14 README, contrato JSON, criterios de aceite e scripts de packaging atualizados para refletir o produto final Gemini-only via GOOGLE_API_KEY; requirements explicitos adicionados, RPMs regenerados e reinstalados, override do systemd reduzido para a chave de API e validacoes locais concluídas no artefato instalado.
- 2026-04-14 Frontend CustomTkinter ajustado para consumir o catalogo do backend, remover selecao geografica legada e melhorar a hierarquia visual do chat com conversa principal destacada e fluxo tecnico separado; reconexao com backend vivo reidrata historico e modelos persistidos na UI.
- 2026-04-14 Backend e persistencia corrigidos para operar somente com Gemini via GOOGLE_API_KEY; modelo padrao definido em `gemini/gemini-3-flash-preview`, provedores antigos removidos do fluxo do daemon, catalogo de modelos vindo do backend, historico da sessao ativa devolvido no handshake e modelos Gemini customizados persistidos no backend.
- 2026-04-14 Auditoria real do repositório, do serviço instalado e da documentacao concluida; reabertos itens porque o estado encontrado divergia do README/TODO e ainda havia rastros operacionais antigos e arquivos de packaging quebrados.
