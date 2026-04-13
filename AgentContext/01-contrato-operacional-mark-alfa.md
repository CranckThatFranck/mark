# Contrato Operacional do Mark Alfa

## Objetivo
Este documento define as regras operacionais obrigatórias para a construção do Mark Alfa no repositório `/home/francisco/Documentos/repos/mark`.

## Regra de Distinção de Ambientes
Existem dois ambientes diferentes que não devem ser confundidos:

1. Ambiente atual do agente já funcional nesta máquina
- É o Mark/Jarvis que já roda hoje no terminal
- Opera no contexto real atual do Francisco
- Usa:
  - `/home/francisco/Documentos/repos/mark`
  - `/home/francisco/Documentos/JarvisMinion`

2. Ambiente-alvo do produto em construção
- É o backend e frontend instaláveis do Mark Alfa
- Deve seguir as regras de portabilidade e instalação definidas no `AgentContext`
- Deve prever:
  - instalação principal em `/opt/jarvis`
  - backend em `/opt/jarvis/backend`
  - frontend em `/opt/jarvis/frontend`
  - contexto resolvido dinamicamente conforme a máquina de destino

Importante:
As regras do produto instalável futuro não substituem automaticamente os caminhos atuais do agente que já está funcional no terminal desta máquina.

## Escopo do Mark Alfa
O Mark Alfa é a fundação executável do futuro ecossistema Mark/Jarvis.
Seu foco atual é:
- backend daemon Linux
- frontend desktop Linux
- comunicação JSON/WebSocket
- segurança operacional
- empacotamento `.rpm` e `.deb`
- continuidade de contexto e retomada

## Regras Arquiteturais Obrigatórias
1. O Open Interpreter deve ser usado como biblioteca Python embutida.
2. O Open Interpreter não deve rodar solto no terminal como forma oficial do produto.
3. O backend deve ser um daemon iniciado via systemd.
4. O backend não deve depender de tray icon.
5. O frontend deve ser um aplicativo separado do backend.
6. O instalador do backend deve ser separado do instalador do frontend.
7. O sistema deve suportar Fedora e Ubuntu.
8. O produto final deve prever empacotamento em `.rpm` e `.deb`.

## Runtime Base
1. Python 3.12 é a baseline operacional atual.
2. Dependências e requisitos devem ser documentados no `README.md` do repositório.
3. O instalador deve preparar tudo o que for necessário para executar backend e frontend fora da máquina de desenvolvimento, inclusive dependências do motor de agente, se exigidas.

## Regras do Produto Instalável Futuro
As regras abaixo se aplicam ao backend e frontend instaláveis em construção:

1. A instalação oficial do produto deve residir em:
   `/opt/jarvis`
2. O backend instalável deve residir em:
   `/opt/jarvis/backend`
3. O frontend instalável deve residir em:
   `/opt/jarvis/frontend`
4. O produto não pode depender de hardcode de usuário, como `francisco`, `ubuntu` ou similares.
5. O contexto operacional do produto instalável deve ser resolvido dinamicamente de acordo com a máquina de destino.
6. O produto instalável deve funcionar em Fedora e Ubuntu sem depender da estrutura pessoal da máquina de desenvolvimento.

## Backend
O backend deve:
- expor WebSocket como canal principal
- suportar ações estruturadas via JSON
- manter contexto persistente controlado
- ter healthcheck e status
- suportar kill switch real
- suportar troca de modelo
- suportar modo plan e modo agent
- persistir configurações do agente
- persistir nome do agente
- permitir conexão local e remota via rede autorizada

## Frontend
O frontend deve:
- conectar-se ao backend
- possuir chat com o agente
- permitir troca entre Plan e Agent
- possuir kill switch
- permitir hotswap de modelo
- permitir configurar IP do backend alvo
- permitir configurar IP do master Jarvis
- permitir configurar nome do agente
- exibir mensagem, código, console e estado do backend

## Modelos
Modelo padrão de inicialização do backend:
`gemini/gemini-3-flash-preview`

Modelos inicialmente disponíveis:
- gemini/gemini-3-flash-preview
- gemini/gemini-3.1-pro-preview
- gemini/gemini-3.1-pro-preview-customtools
- gemini/gemini-3.1-flash-lite-preview
- gemini/gemini-2.5-flash
- gemini/gemini-2.5-pro

## Persistência de Trabalho
Durante a execução do projeto, o agente deve:
- atualizar `/home/francisco/Documentos/JarvisMinion/MemoriaDoJarvis.log`
- atualizar `/home/francisco/Documentos/repos/mark/TODOList.md`
- registrar pivotagens em `/home/francisco/Documentos/repos/mark/pivotagem`
- garantir continuidade caso seja interrompido

Importante:
Esses caminhos acima se referem ao ambiente atual de desenvolvimento e operação do agente nesta máquina.

## Regra de Fluxo
1. Ler primeiro itens em `## A fazer`
2. Mover item iniciado para `## Fazendo`
3. Mover item concluído para `## Feito`
4. Ao concluir marco relevante, registrar memória e preparar commit/push

## Critério de Qualidade
Nenhuma funcionalidade deve existir apenas “porque funcionou uma vez”.
Tudo deve ser:
- reproduzível
- rastreável
- testável
- reversível
- documentado

## Resultado Esperado
Ao final do Mark Alfa, deve existir uma base segura e versionável capaz de sustentar a construção posterior do Mark oficial e do futuro Jarvis Master.

## Regra Final
Sempre distinguir claramente:
- o ambiente atual do agente já funcional nesta máquina
- o ambiente-alvo do produto instalável em construção

Misturar os dois ambientes gera erro de arquitetura, documentação e implementação.
