# Guia de Implementação Sequencial do Backend do Mark

## Objetivo
Este documento transforma a arquitetura do backend do Mark em uma sequência de implementação braçal, linear e validável, para que o agente execute a construção com o mínimo de improviso possível.

## Regra de Distinção de Ambientes
Existem dois ambientes diferentes que não devem ser confundidos:

1. Ambiente atual do agente já funcional nesta máquina
- É o Mark/Jarvis que já roda hoje no terminal
- Usa os caminhos reais atuais do ambiente do Francisco
- Serve como base de desenvolvimento, memória e contexto do trabalho atual

2. Ambiente-alvo do produto em construção
- É o backend instalável do Mark Alfa
- Deve seguir as regras de portabilidade, empacotamento e instalação do `AgentContext`
- Deve prever:
  - instalação em `/opt/jarvis/backend`
  - contexto operacional dinâmico por usuário
  - separação entre código do produto e contexto da máquina de destino

Importante:
As etapas deste documento se aplicam ao backend do produto em construção.
Elas não substituem automaticamente o ambiente atual do agente já funcional nesta máquina.

## Regra de Execução
O backend deve ser construído em etapas pequenas e validadas.
Nenhuma etapa estrutural deve ser pulada.
Nenhuma etapa posterior deve assumir que a anterior “deve estar funcionando” sem validação.

## Resultado Esperado do Backend
Ao final da implementação, o backend deve:
- rodar como daemon via systemd
- viver instalado em `/opt/jarvis/backend`
- usar Open Interpreter como biblioteca embutida
- expor WebSocket e protocolo JSON
- suportar `execute_task`, `change_model`, `interrupt`, `get_status`, `get_config`, `update_config`, `healthcheck`, `get_models`
- suportar Plan e Agent
- rastrear tarefa ativa
- isolar subprocessos por PGID
- encerrar tarefas com kill switch real
- persistir identidade e configuração
- usar contexto por usuário resolvido dinamicamente

## Pré-condições
Antes de codar o backend:
1. Ler a constituição do agente
2. Ler o contrato operacional
3. Ler o contrato JSON
4. Ler o roadmap
5. Ler critérios de aceite
6. Ler política de diretórios
7. Ler política de persistência
8. Ler política de empacotamento e instalação

## Etapa 1 - Definir constantes e resolução de caminhos
Objetivo:
Criar a base que impede hardcodes de ambiente.

Criar:
- `src/backend/config.py`

Implementar:
- modelo padrão
- lista de modelos disponíveis
- porta padrão do backend
- resolução de `HOME`
- resolução de raiz de contexto do usuário
- detecção de `~/Documents`
- detecção de `~/Documentos`
- fallback documentado
- caminhos derivados para:
  - memória
  - logs
  - estado
  - contextos
- caminhos de instalação do produto em `/opt/jarvis/backend`

Validar:
- o módulo importa sem erro
- os caminhos são calculados corretamente
- nenhum caminho depende de `/home/francisco`
- o código distingue corretamente o backend instalável futuro do ambiente atual de desenvolvimento, quando isso for necessário

Critério de aceite local:
- o backend consegue imprimir ou expor os caminhos resolvidos de forma consistente

## Etapa 2 - Preparar estrutura mínima de contexto
Objetivo:
Garantir que o backend sabe onde guardar seu estado.

Implementar:
- função que cria diretórios mínimos se não existirem
- criação de:
  - pasta de memória
  - pasta de logs
  - pasta de estado
  - pasta de contextos
  - pasta de lixo
- criação opcional de arquivos mínimos vazios ou templates

Validar:
- primeiro boot consegue preparar estrutura mínima
- execução repetida não quebra nem duplica desnecessariamente

Critério de aceite local:
- a raiz `JarvisMark` do usuário fica pronta para uso

## Etapa 3 - Configuração segura do backend
Objetivo:
Centralizar configuração e evitar espalhamento de constantes.

Implementar em `config.py`:
- carregamento de `.env` ou equivalente
- leitura segura de variáveis de ambiente
- definição de `SYSTEM_MESSAGE`
- função de validação de configuração essencial
- valores default seguros

Validar:
- backend inicializa mesmo com ausência de campos não críticos
- falha de forma clara quando faltar campo realmente obrigatório

Critério de aceite local:
- configuração inválida gera erro compreensível
- configuração válida gera estado coerente

## Etapa 4 - Chassi do servidor WebSocket
Objetivo:
Criar o orquestrador de rede do backend.

Criar:
- `src/backend/server.py`

Implementar:
- servidor assíncrono WebSocket
- loop de escuta contínua
- handshake inicial
- envio de `sync_state`
- parser de mensagens JSON
- tratamento de payload inválido
- roteamento por `action`

Validar:
- conexão local funciona
- `sync_state` chega ao cliente
- payload inválido não derruba o daemon

Critério de aceite local:
- o servidor sobe, aceita conexão e responde sem travar

## Etapa 5 - Estado interno do backend
Objetivo:
Dar memória operacional de curto prazo ao daemon.

Implementar:
- modelo de estado interno do backend
- status do daemon: idle, busy, interrupted, error
- modo atual: plan ou agent
- modelo atual
- nome do agente
- host master
- host alvo padrão
- tabela de tarefas ativas

Validar:
- `get_status` reflete o estado real
- transições de estado são consistentes

Critério de aceite local:
- o backend sabe quem ele é, em que modo está e se há tarefa ativa

## Etapa 6 - Persistência de configuração
Objetivo:
Fazer o backend manter identidade entre reinícios.

Implementar:
- arquivo persistente de configuração
- leitura no boot
- escrita segura ao atualizar
- ações:
  - `get_config`
  - `update_config`

Persistir pelo menos:
- nome do agente
- host master
- host alvo padrão
- lista de modelos habilitados
- preferências essenciais

Validar:
- reiniciar backend preserva configuração
- config inválida não corrompe estado

Critério de aceite local:
- a identidade do agente permanece após reinício

## Etapa 7 - Ações básicas do protocolo
Objetivo:
Fechar primeiro o backend “sem IA” antes da execução agentic.

Implementar:
- `healthcheck`
- `get_status`
- `get_models`
- `get_config`
- `update_config`

Validar:
- todas retornam JSON consistente
- erros retornam `action_response` com status de erro
- nenhuma dessas ações trava o daemon

Critério de aceite local:
- cliente consegue usar backend básico sem Open Interpreter ainda

## Etapa 8 - Enjaular o Open Interpreter
Objetivo:
Integrar o motor do agente do jeito arquiteturalmente correto.

Criar:
- `src/backend/agent_runner.py` ou componente equivalente

Implementar:
- import da biblioteca `interpreter`
- injeção de `SYSTEM_MESSAGE`
- configuração programática
- proibição de depender da CLI solta
- interface controlada para execução de tarefa

Validar:
- backend chama runner por camada controladora
- a arquitetura oficial não exige terminal manual do interpretador

Critério de aceite local:
- uma tarefa simples consegue passar pela jaula e voltar com resposta

## Etapa 9 - `execute_task`
Objetivo:
Fazer o backend executar tarefa real.

Implementar:
- action `execute_task`
- leitura de `task`
- leitura de `mode`
- eco `user`
- envio de `status START`
- fluxo de resposta `message`, `code`, `console`, `action_response`
- envio de `status END`

Validar:
- tarefa simples responde corretamente
- ausência de `mode` assume `agent`
- modo informado é respeitado

Critério de aceite local:
- o cliente consegue enviar uma tarefa e receber stream coerente

## Etapa 10 - Modo Plan e modo Agent
Objetivo:
Fazer o backend respeitar de fato o estado cognitivo solicitado.

Implementar:
- entrada em `plan`
- bloqueio de ações destrutivas em `plan`
- entrada em `agent`
- retorno automático para `agent` ao concluir tarefa
- coerência entre estado interno e mensagens externas

Validar:
- plan não executa alteração destrutiva
- backend volta para `agent` ao fim
- `sync_state` e `get_status` refletem o estado correto

Critério de aceite local:
- plan e agent deixam de ser rótulos e passam a ser comportamento real

## Etapa 11 - Isolamento de subprocessos
Objetivo:
Evitar que tarefas longas matem a responsividade do backend.

Implementar:
- criação de processo/tarefa isolada
- PGID próprio por tarefa
- rastreamento de PID/PGID
- tabela de tarefas ativas vinculada à sessão ou cliente

Validar:
- tarefa longa não bloqueia o WebSocket
- backend continua aceitando comando enquanto há tarefa ativa
- não há evidência de zumbis após testes repetidos

Critério de aceite local:
- daemon segue vivo e responsivo sob carga

## Etapa 12 - Kill switch
Objetivo:
Dar interrupção real ao usuário.

Implementar:
- action `interrupt`
- localização da tarefa ativa
- `os.killpg(os.getpgid(pid), signal.SIGINT)` ou equivalente seguro
- limpeza do contexto curto da tarefa
- atualização do estado interno
- resposta ao cliente confirmando sistema livre

Validar:
- interrompe tarefa bloqueante
- não derruba o daemon inteiro
- aceita nova tarefa depois
- não deixa processo rodando escondido

Critério de aceite local:
- o botão de parar funciona de verdade

## Etapa 13 - Recuperação pós-interrupção
Objetivo:
Fazer o backend voltar limpo após trauma.

Implementar:
- reset do estado da tarefa
- marcação de interrupção na memória do backend
- registro em memória persistente
- registro em change.log quando aplicável
- prevenção de retomada automática alucinada

Validar:
- após interrupção o sistema não tenta continuar sozinho
- próxima tarefa começa limpa

Critério de aceite local:
- backend fica pronto para nova ordem sem reinício manual

## Etapa 14 - Health e observabilidade
Objetivo:
Facilitar uso real e troubleshooting.

Implementar:
- `healthcheck`
- `get_status`
- logs mínimos relevantes
- mensagens de erro legíveis
- estado inicial, ocupado, interrompido e erro

Validar:
- o usuário entende o estado do backend
- logs ajudam sem virar ruído inútil

Critério de aceite local:
- há visibilidade mínima operacional

## Etapa 15 - Integração com systemd
Objetivo:
Formalizar o backend como processo do sistema.

Implementar:
- unit file
- diretório de trabalho correto
- ExecStart correto
- restart policy
- dependência de rede quando fizer sentido
- comandos documentados

Validar:
- start funciona
- stop funciona
- restart funciona
- status funciona
- reboot da máquina não quebra o modelo operacional

Critério de aceite local:
- backend existe como serviço de verdade

## Etapa 16 - Preparação para empacotamento
Objetivo:
Deixar o backend pronto para virar pacote.

Implementar:
- organização final dos arquivos
- scripts auxiliares mínimos
- arquivos de packaging
- inclusão do serviço systemd
- inclusão de templates de config
- validação da instalação em `/opt/jarvis/backend`

Validar:
- instalação não depende da árvore do repositório original
- caminhos do backend continuam corretos após instalação
- o backend preparado para distribuição não depende do ambiente pessoal do autor

Critério de aceite local:
- backend consegue rodar fora do ambiente de desenvolvimento

## Etapa 17 - Testes de fumaça
Objetivo:
Garantir o mínimo operável antes de seguir para frontend.

Executar checklist:
- sobe o backend
- responde `sync_state`
- responde `healthcheck`
- responde `get_status`
- atualiza config
- lista modelos
- executa tarefa simples
- respeita plan
- respeita agent
- interrompe tarefa longa
- reinicia mantendo config

Critério de aceite local:
- backend aprovado para integração com frontend

## Etapa 18 - Fechamento da etapa backend
Objetivo:
Encerrar o marco de backend com rastreabilidade.

Executar:
- atualizar TODOList
- registrar memória persistente
- registrar pivotagem se houve desvio estrutural
- revisar arquivos centrais
- preparar commit do marco

## Proibições durante a implementação
1. Não hardcodar `/home/francisco`
2. Não depender da CLI solta do Open Interpreter
3. Não misturar frontend no backend
4. Não acoplar daemon a tray icon
5. Não seguir para etapa posterior sem validar a anterior
6. Não deixar o kill switch para “depois”
7. Não inventar requisitos novos no meio da execução sem registrar

## Regra Final
O backend do Mark deve nascer primeiro como sistema controlado, rastreável e interrompível.
Só depois ele ganha refinamento de UX via frontend.

Também é obrigatório preservar a distinção entre:
- o ambiente atual do agente já funcional nesta máquina
- o backend instalável do produto futuro em construção
