# Estrutura de Diretórios e Arquivos do Projeto Mark

## Objetivo
Este documento define a estrutura oficial de diretórios e arquivos do repositório `/home/francisco/Documentos/repos/mark` para que o desenvolvimento do Mark Alfa aconteça de forma previsível, modular, empacotável e fácil de manter.

## Regra de Distinção de Ambientes
Existem dois ambientes diferentes que não devem ser confundidos:

1. Ambiente atual do agente já funcional nesta máquina
- É o Mark/Jarvis que já roda hoje no terminal
- Usa os caminhos reais atuais do ambiente do Francisco
- Opera com base em:
  - `/home/francisco/Documentos/repos/mark`
  - `/home/francisco/Documentos/JarvisMinion`

2. Ambiente-alvo do produto em construção
- É o backend e frontend instaláveis do Mark Alfa
- Deve seguir as regras de portabilidade, instalação e empacotamento definidas no `AgentContext`
- Deve prever:
  - instalação principal em `/opt/jarvis`
  - backend em `/opt/jarvis/backend`
  - frontend em `/opt/jarvis/frontend`
  - contexto operacional dinâmico conforme a máquina de destino

Importante:
As regras do produto instalável futuro não substituem automaticamente os caminhos atuais do agente já funcional nesta máquina.

## Regra Geral
1. O repositório do Mark deve separar claramente:
   - código do backend
   - código do frontend
   - empacotamento
   - documentação
   - testes
   - scripts operacionais
   - arquivos de apoio de execução do projeto
2. Nenhum arquivo novo estrutural deve ser criado “em qualquer lugar”.
3. Toda expansão estrutural relevante deve ser documentada.
4. Se surgir necessidade de nova pasta estrutural fora desta convenção, isso deve gerar item no TODOList e arquivo em `pivotagem`.

## Raízes Externas ao Repositório
O projeto depende de duas raízes distintas:

### 1. Repositório de desenvolvimento
`/home/francisco/Documentos/repos/mark`

Função:
- código
- empacotamento
- documentação do produto
- testes
- pipeline manual de construção
- TODOList e pivotagens do projeto

### 2. Área operacional viva do agente atual nesta máquina
`/home/francisco/Documentos/JarvisMinion`

Função:
- memória persistente
- logs
- contextos globais do agente
- histórico de execução
- continuidade após interrupção

### 3. Raiz oficial do produto instalável futuro
`/opt/jarvis`

Função:
- instalação do backend distribuível
- instalação do frontend distribuível
- base oficial do produto em máquinas de destino

Importante:
A raiz `/opt/jarvis` pertence ao produto instalável futuro.
Ela não substitui a árvore atual do repositório de desenvolvimento nem a área operacional viva do agente já funcional nesta máquina.

## Estrutura Oficial do Repositório

### Raiz
Arquivos esperados na raiz:
- `README.md`
- `TODOList.md`
- `.gitignore`
- `.env.example`
- `LICENSE` se aplicável
- `pyproject.toml` ou equivalente, se adotado como padrão do projeto
- `requirements-backend.txt` ou equivalente
- `requirements-frontend.txt` ou equivalente

Pastas esperadas:
- `src`
- `tests`
- `docs`
- `scripts`
- `packaging`
- `pivotagem`

## Diretório `src`
Função:
Conter exclusivamente o código-fonte do produto.

Estrutura:
- `src/backend`
- `src/frontend`
- `src/shared` opcional

### `src/backend`
Função:
Conter o daemon e tudo que pertence ao backend.

Arquivos/pastas esperados:
- `config.py`
- `server.py`
- `agent_runner.py`
- `models.py` opcional
- `protocol.py` opcional
- `state.py` opcional
- `services/` opcional
- `utils/` opcional

Responsabilidades:
- carregar configuração
- encapsular Open Interpreter
- expor WebSocket
- processar JSON
- gerenciar modo Plan/Agent
- controlar modelo ativo
- controlar tarefas ativas
- implementar kill switch
- persistir configuração essencial

### `src/frontend`
Função:
Conter o aplicativo desktop do frontend.

Arquivos/pastas esperados:
- `app.py`
- `ui/`
- `views/`
- `widgets/`
- `client/`
- `state/`
- `assets/` se necessário
- `utils/`

Responsabilidades:
- abrir a interface
- conectar ao backend
- mostrar chat
- mostrar stream de mensagens
- mostrar código e console
- permitir troca de modelo
- permitir seleção Plan/Agent
- permitir interrupção
- permitir configuração de IPs e nome do agente

### `src/shared`
Função:
Conter contratos ou utilitários compartilhados entre backend e frontend, se isso realmente reduzir duplicação sem misturar responsabilidades.

Pode conter:
- enums de status
- schemas JSON
- validações
- constantes de protocolo

Regra:
Só criar se houver ganho real de clareza. Não criar por antecipação vazia.

## Diretório `tests`
Função:
Conter testes automatizados e, quando necessário, testes assistidos documentados.

Estrutura sugerida:
- `tests/backend`
- `tests/frontend`
- `tests/integration`
- `tests/manual`

### `tests/backend`
Exemplos:
- parsing de payload JSON
- persistência de config
- ciclo de status
- troca de modelo
- interrupção de tarefa
- regras de transição de estado

### `tests/frontend`
Exemplos:
- estados de conexão
- renderização mínima
- tratamento de erro
- mapeamento de mensagens do backend

### `tests/integration`
Exemplos:
- frontend conectando no backend
- `sync_state`
- `execute_task`
- `change_model`
- `interrupt`
- reconexão

### `tests/manual`
Função:
Guardar checklists ou roteiros de testes humanos quando o teste automatizado não for suficiente.

## Diretório `docs`
Função:
Guardar documentação de produto, arquitetura e operação que não pertence ao `AgentContext`.

Arquivos sugeridos:
- `architecture.md`
- `backend.md`
- `frontend.md`
- `protocol.md`
- `packaging.md`
- `operations.md`
- `troubleshooting.md`

Regra:
`AgentContext` orienta o agente a construir.
`docs` explica o produto construído.

## Diretório `scripts`
Função:
Guardar scripts de apoio ao desenvolvimento, build, validação e empacotamento.

Arquivos sugeridos:
- `run-backend-dev.sh`
- `run-frontend-dev.sh`
- `check-env.sh`
- `build-backend-package.sh`
- `build-frontend-package.sh`
- `smoke-test.sh`

Regra:
Scripts em `scripts/` não substituem a arquitetura do produto.
Eles ajudam a construir, testar ou empacotar.

## Diretório `packaging`
Função:
Separar claramente os artefatos de empacotamento do backend e do frontend.

Estrutura:
- `packaging/backend`
- `packaging/frontend`

### `packaging/backend`
Pode conter:
- arquivos `.spec`
- estrutura `.deb`
- unit file do systemd
- scripts de pós-instalação
- arquivos de serviço
- templates de config de instalação

Responsabilidade adicional:
Preparar o backend para instalação futura em:
`/opt/jarvis/backend`

### `packaging/frontend`
Pode conter:
- arquivos `.spec`
- estrutura `.deb`
- atalhos `.desktop`
- ícones
- scripts de pós-instalação se necessários

Responsabilidade adicional:
Preparar o frontend para instalação futura em:
`/opt/jarvis/frontend`

Regra:
Backend e frontend devem ter pipelines de empacotamento independentes.

## Diretório `pivotagem`
Função:
Registrar decisões estruturais novas ou desvios de rota.

Regra obrigatória:
Se o agente criar, alterar ou propor algo relevante fora do plano atual, deve:
1. adicionar ou mover o item correspondente no `TODOList.md`
2. criar um arquivo nesta pasta com o nome do item
3. explicar:
   - o que mudou
   - por que mudou
   - qual problema isso resolveu
   - qual impacto teve no plano

## Arquivo `TODOList.md`
Função:
Ser a trilha visual e operacional do avanço do projeto.

Estrutura oficial:
- `## Feito`
- `## Fazendo`
- `## A fazer`

Regras:
1. Todo trabalho começa lendo `## A fazer`.
2. Ao iniciar um item, mover para `## Fazendo`.
3. Ao concluir, mover para `## Feito`.
4. Ao concluir marco relevante, realizar commit e push.
5. Se surgir novo item necessário, inserir no TODO e documentar em `pivotagem` quando houver mudança estrutural.

## Arquivo `README.md`
Função:
Explicar como o produto funciona para humanos.

Deve conter ao final do Mark Alfa:
- visão geral
- requisitos
- dependências
- como instalar backend
- como instalar frontend
- como operar
- como verificar status
- como interromper
- como recuperar
- troubleshooting básico
- distinção entre:
  - ambiente atual de desenvolvimento
  - produto instalável futuro

## Arquivo `.env.example`
Função:
Mostrar as variáveis esperadas sem expor segredos reais.

Pode conter exemplos como:
- chave de API
- modelo padrão
- porta do backend
- caminho de arquivos de estado
- opções de ambiente

Regra:
Nunca commitar segredos reais.

## Convenções de Nomes
1. Usar nomes claros e previsíveis.
2. Evitar misturar português e inglês no mesmo nível estrutural sem necessidade.
3. Pastas técnicas do produto preferencialmente em inglês.
4. Documentos operacionais para o agente podem permanecer em português.
5. Nomes devem refletir responsabilidade real do arquivo.

## Regra de Modularidade
1. Backend e frontend não devem compartilhar acoplamento desnecessário.
2. Código de protocolo pode ser compartilhado apenas se isso reduzir inconsistência.
3. Lógica de sistema fica no backend.
4. Lógica de apresentação fica no frontend.
5. Configuração persistente do agente deve ser tratada no backend.

## Regra Final
A estrutura do repositório deve fazer o projeto ficar mais fácil de entender, testar, empacotar, versionar e retomar.
Se uma nova pasta ou arquivo não ajuda nisso, provavelmente ele não deve existir.

Também é obrigatório preservar a distinção entre:
- a estrutura atual do projeto e do agente nesta máquina
- a estrutura oficial do produto instalável futuro
