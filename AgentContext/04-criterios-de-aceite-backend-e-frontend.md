# Critérios de Aceite do Backend e Frontend do Mark Alfa

## Objetivo
Este documento define, de maneira objetiva, quando uma entrega do backend ou do frontend do Mark Alfa pode ser considerada aceita.

## Regra de Distinção de Ambientes
Existem dois ambientes diferentes que não devem ser confundidos:

1. Ambiente atual do agente já funcional nesta máquina
- É o contexto real do Mark/Jarvis rodando hoje no terminal
- Usa os caminhos atuais locais do Francisco
- Serve como base de desenvolvimento, memória e contexto do trabalho atual

2. Ambiente-alvo do produto em construção
- É o backend e frontend instaláveis do Mark Alfa
- Deve seguir as regras de instalação, portabilidade e empacotamento do `AgentContext`
- Deve prever:
  - `/opt/jarvis`
  - `/opt/jarvis/backend`
  - `/opt/jarvis/frontend`
  - contexto operacional dinâmico na máquina de destino

Importante:
Os critérios de aceite abaixo se aplicam principalmente ao produto em construção.
Eles não substituem o ambiente atual do agente já funcional nesta máquina.

## Regra Geral de Aceite
Uma funcionalidade só é considerada pronta quando:
- foi implementada
- foi testada
- respeita a constituição do agente
- respeita o contrato operacional
- respeita o contrato JSON
- possui comportamento previsível
- possui rollback ou recuperação clara quando aplicável
- foi registrada no TODO e na memória persistente

## 1. Critérios de Aceite do Backend

### 1.1 Inicialização
Aceito quando:
- o backend sobe sem depender de terminal manual permanente
- o backend carrega a configuração inicial corretamente
- o backend informa estado inicial coerente
- o backend não entra em loop de falha na inicialização

Não aceito quando:
- exige intervenção manual obscura para subir
- depende do usuário deixar uma sessão terminal aberta
- inicia sem estado consistente

### 1.2 Configuração
Aceito quando:
- o backend consegue carregar variáveis de ambiente com segurança
- o modelo padrão é aplicado corretamente
- a lista de modelos disponíveis é carregada corretamente
- nome do agente e configurações essenciais podem ser lidos e persistidos
- o backend distingue corretamente:
  - ambiente atual de desenvolvimento
  - ambiente-alvo instalável futuro, quando isso for relevante

Não aceito quando:
- usa valores críticos hardcoded de maneira insegura
- perde configuração ao reiniciar sem motivo
- não consegue distinguir configuração válida de inválida

### 1.3 Comunicação WebSocket
Aceito quando:
- o backend aceita conexão WebSocket
- responde com `sync_state` ao conectar
- processa mensagens JSON válidas
- responde com erro estruturado para payload inválido
- permanece responsivo durante uso normal

Não aceito quando:
- trava ao receber mensagem inesperada
- responde em formato inconsistente
- exige polling manual como solução principal

### 1.4 Ações estruturadas
Aceito quando:
- `healthcheck` funciona
- `get_status` funciona
- `get_models` funciona
- `get_config` funciona
- `update_config` funciona
- `change_model` funciona
- `execute_task` funciona
- `interrupt` funciona
- `shutdown_backend` funciona, se já fizer parte do escopo implementado

Não aceito quando:
- uma ação existe no contrato mas falha sem tratamento
- ação retorna sucesso falso
- ação altera estado sem refletir isso nas respostas

### 1.5 Open Interpreter embutido
Aceito quando:
- o motor do agente roda como biblioteca Python
- a arquitetura oficial não depende da CLI solta
- o backend consegue despachar tarefa ao motor com controle do ciclo de vida

Não aceito quando:
- a solução real depende de abrir manualmente o interpretador no shell
- a execução ignora a camada controladora do backend

### 1.6 Isolamento de processos
Aceito quando:
- tarefas longas não bloqueiam a thread de comunicação
- cada tarefa ativa possui rastreamento mínimo de processo
- o backend segue responsivo durante execução pesada
- não há acúmulo evidente de processos zumbis após testes de estresse

Não aceito quando:
- uma tarefa longa congela o daemon
- o backend perde capacidade de ouvir novas ordens
- subprocessos ficam órfãos com frequência

### 1.7 Kill switch
Aceito quando:
- uma tarefa em andamento pode ser interrompida sob comando do usuário
- o backend confirma a interrupção
- o backend volta a estado seguro após parar
- o backend pode aceitar nova ordem depois da interrupção
- a memória curta da tarefa abortada é tratada adequadamente

Não aceito quando:
- o botão de parar apenas “pede com educação”
- a interrupção deixa o backend preso
- a interrupção mata o daemon inteiro sem necessidade
- a tarefa continua rodando em background depois do stop

### 1.8 Modo Plan e modo Agent
Aceito quando:
- o backend inicia em `agent`
- ao receber `mode = plan`, entra em comportamento de arquiteto
- em plan, não executa alteração destrutiva de sistema
- após concluir a tarefa, retorna automaticamente para `agent`
- o estado atual é refletido corretamente na comunicação

Não aceito quando:
- plan e agent são apenas rótulos visuais sem efeito real
- o backend esquece de retornar para `agent`
- o modo atual fica incoerente entre backend e frontend

### 1.9 Persistência
Aceito quando:
- o backend preserva identidade e configuração importante entre reinícios
- o agente registra marcos relevantes em memória persistente
- o backend pode ser retomado sem perda total de contexto operacional
- o backend prepara corretamente o comportamento esperado para o produto instalável futuro sem depender do home do autor

Não aceito quando:
- reiniciar apaga identidade do agente
- reiniciar apaga configuração principal
- não há rastro mínimo de continuidade

### 1.10 Serviço systemd
Aceito quando:
- o backend pode ser iniciado por `systemctl start`
- o backend pode ser parado por `systemctl stop`
- o backend pode ser reiniciado por `systemctl restart`
- o status é consultável por `systemctl status`
- os logs são acessíveis de forma padrão
- o serviço reinicia de forma coerente após falha recuperável

Não aceito quando:
- o serviço sobe apenas em cenário manual
- a unit está incompleta
- o daemon não sobrevive a reinício do sistema como esperado

### 1.11 Empacotamento do backend
Aceito quando:
- existe pacote `.rpm` funcional
- existe pacote `.deb` funcional
- o pacote instala dependências documentadas ou exige claramente o que falta
- o serviço systemd entra junto no pacote quando aplicável
- a instalação em outra máquina é reproduzível
- o backend preparado para distribuição respeita:
  - `/opt/jarvis/backend`
  - contexto dinâmico por usuário
  - ausência de hardcode de `francisco`

Não aceito quando:
- o pacote instala mas não roda
- o pacote depende de etapas escondidas não documentadas
- a instalação fora da máquina do autor falha por premissas não declaradas

## 2. Critérios de Aceite do Frontend

### 2.1 Inicialização
Aceito quando:
- o frontend instala e abre em ambiente gráfico suportado
- o frontend não precisa manipular diretamente o sistema operacional para existir
- o frontend inicia mesmo quando o backend ainda não está conectado, exibindo estado coerente

Não aceito quando:
- o frontend fecha abruptamente por falta de conexão
- o frontend depende de hacks temporários para abrir

### 2.2 Conexão com backend
Aceito quando:
- o frontend consegue conectar em `localhost`
- o frontend consegue conectar em IP remoto autorizado
- o frontend informa claramente conectado, desconectado e reconectando
- o frontend se recupera de perda temporária de conexão

Não aceito quando:
- a conexão falha silenciosamente
- o usuário não entende em que estado a conexão está

### 2.3 Tela principal
Aceito quando:
- existe chat funcional
- existe seletor de modo Plan/Agent
- existe kill switch acessível
- existe seletor de modelo
- existe exibição de mensagens do agente
- existe exibição de trechos de código e console quando enviados pelo backend

Não aceito quando:
- a tela principal não permite operar o agente
- o stream do backend é perdido ou escondido sem justificativa

### 2.4 Tela de configurações
Aceito quando:
- existe campo para IP do master
- existe campo para IP do backend alvo
- existe configuração persistente do nome do agente
- existe listagem ou gestão básica de modelos disponíveis, conforme escopo implementado
- existe ação de desligamento gracioso do backend, se essa funcionalidade já estiver ativa no contrato

Não aceito quando:
- configurações somem ao reiniciar sem motivo
- o frontend salva estado local incoerente com o backend

### 2.5 Fluxo Plan/Agent
Aceito quando:
- o frontend envia corretamente o modo escolhido
- o frontend reflete o estado real devolvido pelo backend
- após tarefa em plan, a UI volta coerentemente para agent quando essa for a regra oficial do backend

Não aceito quando:
- a UI mostra um estado e o backend opera em outro
- o seletor é puramente cosmético

### 2.6 Kill switch no frontend
Aceito quando:
- o botão de parar é fácil de localizar
- ao clicar, o payload correto é disparado
- a UI reflete a interrupção confirmada
- o usuário percebe que o sistema voltou a ficar livre

Não aceito quando:
- o botão é ambíguo
- o comando de parar não gera resposta clara
- a interface continua parecendo travada após interrupção bem-sucedida

### 2.7 Hotswap de modelo
Aceito quando:
- o usuário consegue solicitar mudança de modelo sem reiniciar a aplicação
- a UI exibe o modelo atual após troca
- a troca respeita a lista oficial de modelos disponíveis

Não aceito quando:
- a troca exige reiniciar tudo
- a UI mostra modelo diferente do backend

### 2.8 Robustez visual e operacional
Aceito quando:
- a interface continua usável em caso de erro recuperável
- mensagens de erro são compreensíveis
- não há travamento total por retorno inesperado do backend
- a interface mantém foco em operação, não em efeitos visuais supérfluos

Não aceito quando:
- qualquer erro simples quebra a aplicação inteira
- a interface esconde o problema em vez de comunicar

### 2.9 Empacotamento do frontend
Aceito quando:
- existe pacote `.rpm` funcional
- existe pacote `.deb` funcional
- a instalação é reproduzível
- dependências gráficas e de runtime estão documentadas
- a aplicação abre corretamente após instalação
- o frontend preparado para distribuição respeita:
  - `/opt/jarvis/frontend`
  - separação clara do backend
  - ausência de dependência do home do autor

Não aceito quando:
- a instalação conclui mas o app não abre
- a aplicação só roda na máquina de desenvolvimento

## 3. Critérios de Aceite de Integração

Aceito quando:
- frontend e backend se conectam com sucesso
- `sync_state` aparece corretamente ao conectar
- envio de tarefa funciona
- retorno de mensagem funciona
- retorno de código funciona
- retorno de console funciona
- troca de modelo funciona
- plan mode funciona
- agent mode funciona
- interrupt funciona
- reconexão funciona
- configuração persistida continua correta após reinício

Não aceito quando:
- integração depende de ações manuais não documentadas
- um lado usa contrato diferente do outro
- o fluxo principal só funciona em demonstração controlada

## 4. Critérios de Aceite de Documentação

Aceito quando:
- `README.md` lista requisitos e dependências
- existe instrução de instalação do backend
- existe instrução de instalação do frontend
- existe instrução de start/stop/status do backend
- existe instrução de troubleshooting básico
- existe instrução de recuperação após interrupção ou falha simples
- a documentação deixa clara a diferença entre:
  - ambiente atual do agente nesta máquina
  - ambiente-alvo do produto instalável futuro

Não aceito quando:
- o projeto depende de conhecimento tácito do autor
- a documentação só explica “o que deveria ser” e não “como rodar”
- os documentos misturam o agente atual com o produto instalável sem distinção

## 5. Critério Final de Pronto
O Mark Alfa só pode ser considerado pronto quando:
- backend e frontend estiverem separados e funcionais
- ambos forem instaláveis
- ambos respeitarem o contrato operacional
- o fluxo ponta a ponta estiver validado
- o kill switch estiver funcional
- a documentação mínima estiver pronta
- o estado do trabalho estiver registrado em memória, TODO e versionamento

## Regra Final
Os critérios de aceite do Mark Alfa devem validar corretamente o produto em construção sem apagar a noção do ambiente atual do agente já funcional nesta máquina.
