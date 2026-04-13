# Guia de Implementação Sequencial do Frontend do Mark

## Objetivo
Este documento transforma a arquitetura do frontend do Mark em uma sequência de implementação linear, validável e de baixo improviso, para que o agente construa a interface desktop como cliente oficial do backend.

## Regra de Distinção de Ambientes
Existem dois ambientes diferentes que não devem ser confundidos:

1. Ambiente atual do agente já funcional nesta máquina
- É o Mark/Jarvis que já roda hoje no terminal
- Usa os caminhos reais atuais do ambiente do Francisco
- Serve como base de desenvolvimento, memória e contexto do trabalho atual

2. Ambiente-alvo do produto em construção
- É o frontend instalável do Mark Alfa
- Deve seguir as regras de portabilidade, empacotamento e instalação do `AgentContext`
- Deve prever:
  - instalação em `/opt/jarvis/frontend`
  - comunicação com backend local ou remoto
  - separação entre interface do produto e o ambiente atual do agente

Importante:
As etapas deste documento se aplicam ao frontend do produto em construção.
Elas não substituem automaticamente o ambiente atual do agente já funcional nesta máquina.

## Regra de Execução
O frontend deve ser implementado em etapas pequenas e testáveis.
Nenhuma etapa deve assumir funcionamento do backend além do que já foi validado.
O frontend não deve assumir responsabilidade de sistema operacional que pertença ao backend.

## Resultado Esperado do Frontend
Ao final da implementação, o frontend deve:
- rodar como aplicação desktop Linux
- viver instalado em `/opt/jarvis/frontend`
- conectar-se a um backend local ou remoto
- usar o contrato oficial JSON/WebSocket
- exibir chat, mensagens, código e console
- permitir seleção de modo Plan/Agent
- permitir hotswap de modelo
- permitir kill switch
- permitir configuração de IP do backend alvo
- permitir configuração de IP do master
- permitir configuração do nome do agente
- refletir o estado real do backend
- tolerar desconexão, reconexão e erro sem quebrar a aplicação inteira

## Pré-condições
Antes de codar o frontend:
1. Ler a constituição do agente
2. Ler o contrato operacional
3. Ler o contrato JSON
4. Ler o roadmap
5. Ler os critérios de aceite
6. Ler a política de diretórios
7. Ler a política de persistência
8. Ler a política de empacotamento e instalação
9. Confirmar que o backend já passou pelos testes mínimos de fumaça

## Regra de Responsabilidade
O frontend é um cliente de controle e observação.
O frontend não deve:
- executar lógica de sistema operacional local como substituto do backend
- assumir que pode modificar diretamente arquivos do backend
- assumir que o backend local está sempre disponível
- conter regras de negócio duplicadas que já existem no backend

## Etapa 1 - Definir stack oficial do frontend
Objetivo:
Fechar a base técnica da UI para evitar retrabalho estrutural.

Definir:
- toolkit oficial da interface
- modelo de organização do app
- estratégia de build local
- estratégia de empacotamento

Regras:
- a stack precisa rodar bem em Fedora e Ubuntu
- a stack precisa ser leve o suficiente para ambientes modestos
- a stack precisa ser empacotável em `.rpm` e `.deb`
- a stack não deve introduzir dependências desnecessariamente pesadas

Critério de aceite local:
- a stack escolhida abre uma janela mínima funcional
- a decisão fica registrada de forma explícita

## Etapa 2 - Estrutura mínima do frontend
Objetivo:
Criar o chassi inicial da aplicação desktop.

Criar:
- `src/frontend/app.py`
- `src/frontend/client/`
- `src/frontend/views/`
- `src/frontend/widgets/`
- `src/frontend/state/`
- `src/frontend/utils/`

Implementar:
- ponto de entrada da aplicação
- janela principal mínima
- bootstrap de estado inicial
- estrutura para navegação entre telas ou painéis

Critério de aceite local:
- a aplicação abre sem erro
- a estrutura mínima do projeto está organizada

## Etapa 3 - Cliente WebSocket
Objetivo:
Criar a camada de comunicação com o backend.

Implementar:
- cliente WebSocket do frontend
- conexão com backend local
- conexão com backend remoto
- estado de conexão:
  - disconnected
  - connecting
  - connected
  - reconnecting
  - error
- parser das mensagens do protocolo
- tratamento de payload desconhecido

Regras:
- o frontend deve suportar `ws://localhost:porta` e host configurável
- a conexão não pode travar a UI
- o frontend deve ignorar campos desconhecidos do protocolo sem quebrar

Critério de aceite local:
- a aplicação consegue conectar em backend funcional
- a UI mostra claramente o estado da conexão

## Etapa 4 - Estado local do frontend
Objetivo:
Separar estado visual de estado remoto.

Implementar:
- estado local da UI
- armazenamento do estado de conexão
- armazenamento do painel atual
- armazenamento dos dados recebidos do backend
- fila de mensagens exibidas
- estado visual de loading, erro, ocupado e livre

Regras:
- o backend é a fonte de verdade para:
  - modo atual
  - modelo atual
  - status do daemon
  - configuração persistente do agente
- o frontend pode manter estado visual temporário, mas não deve mentir sobre o estado real do backend

Critério de aceite local:
- a interface mantém coerência mesmo com múltiplas mensagens chegando em sequência

## Etapa 5 - Handshake e `sync_state`
Objetivo:
Fazer o frontend entender o estado do backend ao conectar.

Implementar:
- recepção de `sync_state`
- atualização da UI com:
  - nome do agente
  - modelo atual
  - modo padrão
  - status do backend
- sincronização de campos visuais a partir do estado real

Critério de aceite local:
- ao conectar, a interface mostra o estado correto sem depender de suposição local

## Etapa 6 - Tela principal
Objetivo:
Criar a central de operação do Mark.

Implementar:
- área de chat
- histórico de mensagens
- entrada de texto
- botão de envio
- seletor Plan/Agent
- seletor de modelo
- botão de kill switch
- área para stream de:
  - message
  - code
  - console
  - system
  - status

Regras:
- a tela deve priorizar operação e clareza
- o usuário deve distinguir:
  - fala natural do agente
  - código que o agente gerou
  - saída de console
  - alertas do sistema

Critério de aceite local:
- um fluxo simples de conversa com o backend pode ser realizado na tela principal

## Etapa 7 - Envio de ações básicas
Objetivo:
Permitir que a UI opere o protocolo oficial.

Implementar envio de:
- `healthcheck`
- `get_status`
- `get_models`
- `get_config`
- `update_config`
- `execute_task`
- `change_model`
- `interrupt`
- `shutdown_backend`, quando esta ação estiver ativa no backend

Regras:
- toda ação deve refletir loading visual quando necessário
- erro de comunicação deve ser tratado sem travar a UI
- resposta estruturada deve ser exibida de forma legível

Critério de aceite local:
- a UI consegue acionar as ações do backend e reagir ao retorno

## Etapa 8 - Fluxo de tarefa
Objetivo:
Permitir uso real do agente pela UI.

Implementar:
- envio de `execute_task`
- eco da mensagem do usuário na interface
- exibição do `status START`
- exibição das mensagens do agente
- exibição de código e console em tempo real
- exibição do `status END`
- tratamento de conclusão com sucesso ou erro

Regras:
- o frontend não pode congelar durante stream
- o usuário deve perceber quando a tarefa começou e quando terminou

Critério de aceite local:
- uma tarefa simples pode ser enviada e acompanhada em tempo real pela UI

## Etapa 9 - Fluxo Plan e Agent
Objetivo:
Fazer a interface respeitar o comportamento cognitivo do backend.

Implementar:
- seletor de modo
- envio do modo escolhido em `execute_task`
- atualização visual ao receber estado real do backend
- retorno visual coerente para `agent` quando esta for a regra do backend após a conclusão da tarefa

Regras:
- o frontend não pode tratar o seletor como enfeite
- o estado exibido deve refletir o estado real devolvido pelo backend

Critério de aceite local:
- o usuário consegue mandar tarefa em plan ou agent e ver o comportamento refletido corretamente

## Etapa 10 - Kill switch
Objetivo:
Dar ao usuário poder imediato de interromper o backend.

Implementar:
- botão visualmente claro de parada
- envio de `interrupt`
- atualização da UI ao receber confirmação
- retorno a estado livre quando a interrupção for bem-sucedida

Regras:
- o botão de parar precisa ser fácil de localizar
- a UI deve deixar claro que a interrupção foi aceita
- após parar, o usuário deve perceber que o sistema está pronto para nova ordem

Critério de aceite local:
- uma tarefa longa pode ser interrompida via UI com resposta visível e coerente

## Etapa 11 - Tela de configurações
Objetivo:
Permitir ao usuário configurar o ambiente de operação.

Implementar campos para:
- IP ou host do backend alvo
- IP ou host do master
- nome do agente
- leitura da configuração persistida do backend
- salvamento de configuração via `update_config`

Regras:
- o backend é a fonte oficial para configurações persistentes do agente
- o frontend pode guardar apenas preferências puramente visuais locais, se isso for necessário

Critério de aceite local:
- o usuário consegue alterar a configuração do agente pela UI e a alteração persiste no backend

## Etapa 12 - Reconexão e tolerância a falhas
Objetivo:
Evitar que erros normais destruam a experiência de uso.

Implementar:
- detecção de desconexão
- tentativa controlada de reconexão
- mensagens claras de falha
- preservação do estado visual útil
- recuperação ao restabelecer a conexão

Regras:
- perda de conexão não deve fechar a aplicação abruptamente
- o frontend deve informar o problema sem esconder a falha

Critério de aceite local:
- desligar e religar o backend não deve exigir reiniciar a UI em todos os casos

## Etapa 13 - Persistência local mínima da UI
Objetivo:
Guardar apenas o que faz sentido do lado visual.

Persistir localmente apenas se necessário:
- último host alvo usado
- preferências visuais
- dimensões da janela
- painel aberto por último

Regras:
- não duplicar no frontend a configuração que já pertence ao backend
- não transformar persistência visual em fonte de verdade operacional

Critério de aceite local:
- reiniciar a UI mantém conforto de uso sem gerar inconsistência com o backend

## Etapa 14 - Observabilidade e ergonomia
Objetivo:
Melhorar a leitura operacional da interface.

Implementar:
- diferenciação visual entre tipos de mensagem
- indicadores de conexão
- indicador de backend ocupado/livre
- indicador do modo atual
- indicador do modelo atual
- mensagens de erro compreensíveis
- feedback de ações enviadas

Critério de aceite local:
- um usuário olha a tela e entende rapidamente o estado do sistema

## Etapa 15 - Preparação para empacotamento
Objetivo:
Deixar o frontend pronto para distribuição.

Implementar:
- organização final dos arquivos
- launcher do app
- assets
- ícone
- arquivo `.desktop`, se aplicável
- validação de dependências gráficas
- instalação em `/opt/jarvis/frontend`

Critério de aceite local:
- o frontend abre corretamente fora da árvore do repositório
- o frontend preparado para distribuição não depende do ambiente pessoal do autor

## Etapa 16 - Testes de fumaça do frontend
Objetivo:
Garantir o mínimo operável antes de chamar de pronto.

Executar checklist:
- aplicação abre
- conecta no backend local
- conecta no backend remoto
- recebe `sync_state`
- envia `healthcheck`
- envia `get_status`
- envia `get_config`
- atualiza config
- envia tarefa simples
- acompanha stream de `message`
- acompanha stream de `code`
- acompanha stream de `console`
- troca modelo
- usa plan
- usa agent
- interrompe tarefa longa
- tolera desconexão e reconecta

Critério de aceite local:
- a UI está pronta para entrar no checklist final de release

## Etapa 17 - Fechamento da etapa frontend
Objetivo:
Encerrar o marco do frontend com rastreabilidade.

Executar:
- atualizar TODOList
- registrar memória persistente
- registrar pivotagem se houver desvio estrutural
- revisar arquivos centrais
- preparar commit do marco

## Proibições durante a implementação
1. Não hardcodar `/home/francisco`
2. Não assumir que o backend estará sempre em localhost
3. Não colocar lógica de sistema no frontend
4. Não acoplar a UI ao terminal manual do backend
5. Não criar estado visual que contradiz o backend
6. Não seguir para empacotamento sem validar integração real
7. Não esconder erros importantes do usuário

## Regra Final
O frontend do Mark deve nascer como um painel operacional confiável.
Ele não substitui o backend, não improvisa arquitetura e não inventa fonte de verdade própria para o que pertence ao daemon.

Também é obrigatório preservar a distinção entre:
- o ambiente atual do agente já funcional nesta máquina
- o frontend instalável do produto futuro em construção
