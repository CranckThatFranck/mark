## A fazer
- Validar a rodada final no produto instalado: abrir frontend, trocar modelo, enviar mensagens em sequencia, verificar reconexao, painel tecnico, copia de texto, timestamps e artefatos RPM/DEB.

## Fazendo
- Revisar a politica de persistencia do backend instalado e integrar um arquivo padrao de regras iniciais do produto em caminho instalavel e documentado.

## Feito
- 2026-04-14 Investigada a perda de comunicacao frontend/backend: o daemon seguia vivo, mas o frontend colapsava qualquer erro de transporte no estado "Backend desconectado" e o servidor ainda deixava handshakes abortados/fechamentos abruptos poluirem o fluxo principal como erro fatal.
- 2026-04-14 Backend e frontend endurecidos contra falhas temporarias de transporte/handshake: reconexao automatica agora distingue backend indisponivel de falha de comunicacao com daemon vivo, `sync_state` reidrata a sessao apos reconectar, historico ganhou timestamps persistidos e o backend passou a tratar `ConnectionClosedError`, stream parcial e handshakes abortados sem derrubar o servico.
- 2026-04-14 UX do frontend ampliada com conversa principal dominante, painel tecnico secundario colapsavel e redimensionavel, texto selecionavel por mouse, timestamps visiveis e botoes de copiar para mensagens e eventos tecnicos, alem de atalhos para abrir o arquivo ou a pasta das regras do produto.
- 2026-04-14 Rodada encerrada com repositório, TODOList, backend instalado em /opt, frontend validado por smoke e RPMs finais `jarvis-backend-1.0.0-1.fc43.noarch.rpm` e `jarvis-frontend-1.0.0-1.fc43.noarch.rpm` gerados e conferidos nesta máquina.
- 2026-04-14 README, contrato JSON, criterios de aceite e scripts de packaging atualizados para refletir o produto final Gemini-only via GOOGLE_API_KEY; requirements explicitos adicionados, RPMs regenerados e reinstalados, override do systemd reduzido para a chave de API e validacoes locais concluídas no artefato instalado.
- 2026-04-14 Frontend CustomTkinter ajustado para consumir o catalogo do backend, remover selecao geografica legada e melhorar a hierarquia visual do chat com conversa principal destacada e fluxo tecnico separado; reconexao com backend vivo reidrata historico e modelos persistidos na UI.
- 2026-04-14 Backend e persistencia corrigidos para operar somente com Gemini via GOOGLE_API_KEY; modelo padrao definido em `gemini/gemini-3-flash-preview`, provedores antigos removidos do fluxo do daemon, catalogo de modelos vindo do backend, historico da sessao ativa devolvido no handshake e modelos Gemini customizados persistidos no backend.
- 2026-04-14 Auditoria real do repositório, do serviço instalado e da documentacao concluida; reabertos itens porque o estado encontrado divergia do README/TODO e ainda havia rastros operacionais antigos e arquivos de packaging quebrados.
