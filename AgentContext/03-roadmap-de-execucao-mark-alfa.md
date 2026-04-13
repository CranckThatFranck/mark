# Roadmap de Execução do Mark Alfa

## Objetivo
Este documento define a ordem oficial de construção do Mark Alfa para evitar desenvolvimento em modo cowboy e garantir uma execução sequencial, testável, segura, rastreável e versionável.

## Regra-Mãe
O Mark Alfa não deve improvisar arquitetura durante a implementação.
Toda tarefa estrutural deve nascer em modo PLAN, ser aprovada, e só então ser executada em modo AGENT.

## Regra de Distinção de Ambientes
Existem dois ambientes diferentes que não devem ser confundidos:

1. Ambiente atual do agente já funcional nesta máquina
- É o Mark/Jarvis que já roda hoje no terminal
- Usa os caminhos reais atuais do ambiente do Francisco
- Opera com base em:
  - `/home/francisco/Documentos/JarvisMinion`
  - `/home/francisco/Documentos/repos/mark`

2. Ambiente-alvo do produto em construção
- É o backend e frontend instaláveis do Mark Alfa
- Deve seguir as regras de portabilidade, empacotamento e instalação do `AgentContext`
- Deve prever:
  - instalação principal em `/opt/jarvis`
  - backend em `/opt/jarvis/backend`
  - frontend em `/opt/jarvis/frontend`
  - contexto operacional dinâmico conforme a máquina de destino

Importante:
As regras do produto instalável futuro não substituem automaticamente os caminhos atuais do agente já funcional nesta máquina.

## Resultado Esperado do Mark Alfa
Ao final desta etapa, o projeto deve entregar:
- um backend Linux executado como daemon via systemd
- um frontend Linux separado do backend
- comunicação padronizada via JSON/WebSocket
- suporte a modo Plan e modo Agent
- kill switch real e funcional
- persistência mínima de configuração e estado
- empacotamento separado para backend e frontend em `.rpm` e `.deb`
- documentação de requisitos, dependências, instalação, operação e recuperação

## Premissas Obrigatórias
1. O Open Interpreter deve ser usado como biblioteca Python embutida.
2. O backend não pode depender de terminal manual para existir.
3. O backend deve iniciar por systemd.
4. O backend não deve depender de tray icon.
5. O frontend é cliente do backend.
6. Backend e frontend devem ter instaladores separados.
7. O projeto deve atender Fedora e Ubuntu.
8. O trabalho precisa ser protegido por memória persistente, TODOList e registro de pivotagem.

## Ordem Oficial de Execução

### Fase 0 - Preparação documental
Objetivo:
Garantir que o agente tenha contrato suficiente para construir sem improviso.

Entregáveis:
- constituição consolidada do agente
- README de contextos consolidado
- contrato operacional do Mark Alfa
- contrato JSON do Mark Alfa
- este roadmap
- critérios de aceite

Critério para avançar:
Todos os documentos-base do ambiente atual do agente e do `AgentContext` precisam estar coerentes entre si.

### Fase 1 - Estrutura-base do repositório
Objetivo:
Preparar o terreno técnico mínimo do projeto.

Ações:
- revisar estrutura atual do repositório `/home/francisco/Documentos/repos/mark`
- definir árvore inicial de diretórios
- garantir existência e uso de:
  - `src/backend`
  - `src/frontend`
  - `packaging/backend`
  - `packaging/frontend`
  - `scripts`
  - `docs`
  - `tests`
  - `pivotagem`

Entregáveis:
- estrutura inicial validada
- TODOList atualizado
- registro em memória persistente

Critério para avançar:
A árvore mínima do projeto deve existir e estar documentada.

### Fase 2 - Constituição programática do backend
Objetivo:
Transformar regras operacionais em artefato de código.

Ações:
- criar `src/backend/config.py`
- centralizar `SYSTEM_MESSAGE`
- carregar `.env` com segurança
- definir configurações padrão do backend
- declarar modelo padrão
- declarar lista inicial de modelos disponíveis
- preparar base para distinguir:
  - ambiente atual do agente nesta máquina
  - ambiente-alvo do backend instalável

Entregáveis:
- `config.py`
- padrão de carregamento de variáveis
- constantes principais do backend

Critério para avançar:
O backend deve conseguir importar configuração sem erro e sem depender de valores hardcoded inseguros.

### Fase 3 - Chassi do backend
Objetivo:
Criar o servidor de comunicação persistente.

Ações:
- criar `src/backend/server.py`
- subir WebSocket na porta padrão do projeto
- implementar handshake inicial
- implementar `sync_state`
- preparar o despachante de ações JSON
- implementar ações mínimas:
  - `healthcheck`
  - `get_status`
  - `get_models`
  - `get_config`

Entregáveis:
- servidor WebSocket funcional
- protocolo inicial funcional
- backend iniciando localmente

Critério para avançar:
O backend deve subir, aceitar conexão e responder ações básicas sem travar.

### Fase 4 - Invólucro do motor de agente
Objetivo:
Enjaular o Open Interpreter dentro do backend.

Ações:
- criar `src/backend/agent_runner.py` ou equivalente
- encapsular o motor do agente
- proibir CLI solta como caminho oficial
- fazer o backend chamar o runner de forma controlada
- preparar fluxo de execução para `execute_task`

Entregáveis:
- runner funcional
- integração inicial com backend
- base de execução controlada

Critério para avançar:
Uma tarefa simples deve poder ser enviada ao backend e processada sem quebrar o servidor de comunicação.

### Fase 5 - Isolamento de subprocessos
Objetivo:
Garantir que tarefas longas não sequestram o backend.

Ações:
- isolar tarefas em novo PGID
- rastrear PID e PGID por tarefa ativa
- manter thread de comunicação livre
- impedir processos zumbis

Entregáveis:
- rastreamento de tarefas ativas
- isolamento por grupo de processos
- telemetria mínima do estado da tarefa

Critério para avançar:
Uma tarefa longa não pode bloquear o WebSocket nem matar a responsividade do daemon.

### Fase 6 - Kill switch
Objetivo:
Dar poder absoluto de interrupção ao usuário.

Ações:
- implementar `action = interrupt`
- localizar PGID ativo
- disparar interrupção de grupo
- limpar estado curto da tarefa
- enviar confirmação ao frontend
- registrar interrupção em log e memória

Entregáveis:
- kill switch funcional
- fluxo de recuperação pós-interrupção
- backend pronto para nova ordem sem reinício

Critério para avançar:
Uma tarefa bloqueante deve poder ser interrompida com sucesso, sem deixar o backend preso.

### Fase 7 - Modo Plan e Modo Agent
Objetivo:
Implantar o ciclo cognitivo formal do Mark.

Ações:
- implementar suporte a `mode = plan`
- bloquear execução destrutiva no plan
- implementar retorno automático para `agent` após conclusão
- refletir estado no `sync_state` e nas respostas

Entregáveis:
- fluxo plan/agent funcional
- transições de estado consistentes
- suporte total ao contrato definido

Critério para avançar:
O backend deve respeitar o modo solicitado e retornar ao estado esperado sem inconsistências.

### Fase 8 - Persistência de configuração
Objetivo:
Fazer o backend lembrar quem ele é e como deve operar.

Ações:
- persistir nome do agente
- persistir host master
- persistir host alvo padrão
- persistir lista de modelos habilitados
- persistir preferências essenciais do backend
- preparar a persistência para o produto instalável futuro sem quebrar o ambiente atual de desenvolvimento

Entregáveis:
- arquivo ou mecanismo de configuração persistente
- ações `get_config` e `update_config`
- leitura correta no boot

Critério para avançar:
Reiniciar o backend não pode apagar identidade nem configuração principal.

### Fase 9 - Serviço systemd
Objetivo:
Formalizar o backend como processo do sistema.

Ações:
- criar unit file do systemd
- definir diretório de trabalho
- definir usuário de execução
- definir restart policy
- definir ordem de dependências de rede
- documentar comandos de start/stop/status/logs

Entregáveis:
- serviço systemd funcional
- boot controlado
- operação documentada

Critério para avançar:
O backend deve subir, parar e reiniciar por systemd de forma previsível.

### Fase 10 - Frontend desktop
Objetivo:
Criar a central local de controle do agente.

Ações:
- criar `src/frontend/app.py`
- implementar conexão WebSocket com backend
- implementar tela principal com:
  - chat
  - seletor Plan/Agent
  - kill switch
  - seletor de modelo
- implementar tela de configuração com:
  - IP do master
  - IP do backend alvo
  - nome do agente
  - desligamento gracioso do backend

Entregáveis:
- frontend funcional
- comunicação real com backend
- visualização mínima do stream do agente

Critério para avançar:
O frontend deve conseguir operar um backend real sem manipulação manual de terminal.

### Fase 11 - Integração ponta a ponta
Objetivo:
Validar o produto em fluxo real.

Ações:
- testar backend local com frontend local
- testar troca de modelo
- testar modo plan
- testar modo agent
- testar interrupção
- testar persistência de configuração
- testar reconexão do frontend
- testar backend remoto via IP autorizado

Entregáveis:
- checklist de integração aprovado
- falhas corrigidas
- memória e TODO atualizados

Critério para avançar:
Todos os fluxos principais devem funcionar de ponta a ponta.

### Fase 12 - Empacotamento backend
Objetivo:
Preparar distribuição instalável do backend.

Ações:
- criar estrutura de pacote `.rpm`
- criar estrutura de pacote `.deb`
- incluir dependências necessárias
- incluir unit file do systemd
- incluir scripts de pós-instalação se necessários
- preparar a instalação do produto em `/opt/jarvis/backend`
- preparar a política de contexto dinâmico para a máquina de destino

Entregáveis:
- pacote instalável do backend para Fedora
- pacote instalável do backend para Ubuntu

Critério para avançar:
O backend deve instalar e iniciar fora da máquina de desenvolvimento.

### Fase 13 - Empacotamento frontend
Objetivo:
Preparar distribuição instalável do frontend.

Ações:
- criar pacote `.rpm`
- criar pacote `.deb`
- incluir dependências do frontend
- validar instalação em máquina com interface gráfica
- preparar a instalação do produto em `/opt/jarvis/frontend`

Entregáveis:
- pacote instalável do frontend para Fedora
- pacote instalável do frontend para Ubuntu

Critério para avançar:
O frontend deve instalar, abrir e conectar no backend sem ajustes manuais obscuros.

### Fase 14 - Documentação final
Objetivo:
Fechar a fundação do Mark Alfa de forma operável por humanos e agentes.

Ações:
- atualizar `README.md`
- listar requisitos
- listar dependências
- listar instalação backend
- listar instalação frontend
- listar operação
- listar recuperação
- listar troubleshooting
- listar limitações atuais
- explicar claramente a diferença entre:
  - ambiente atual do agente nesta máquina
  - ambiente-alvo do produto instalável futuro

Entregáveis:
- README final consistente
- documentação de operação mínima
- documentação de recuperação mínima

Critério para avançar:
Uma nova instalação deve ser possível com base apenas na documentação.

### Fase 15 - Fechamento de marco
Objetivo:
Finalizar o ciclo com rastreabilidade total.

Ações:
- revisar TODOList
- mover itens concluídos
- registrar marco em memória
- gerar eventual pivotagem pendente
- realizar commit e push do marco aprovado

Entregáveis:
- repositório versionado
- memória persistente atualizada
- marco concluído de forma recuperável

Critério de conclusão do Mark Alfa:
O projeto deve possuir backend e frontend separados, operáveis, instaláveis, documentados, interrompíveis, versionados e prontos para sustentar a próxima evolução do ecossistema Mark.

## Regra Final
O roadmap do Mark Alfa deve sempre preservar a distinção entre:
- o agente atual já funcional nesta máquina
- o produto instalável futuro em construção

Essa distinção evita que o projeto confunda ambiente de desenvolvimento atual com ambiente-alvo de distribuição.
