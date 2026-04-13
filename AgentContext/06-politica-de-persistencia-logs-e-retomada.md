# Política de Persistência, Logs e Retomada do Mark

## Objetivo
Este documento define como o Mark deve preservar contexto, registrar ações, sobreviver a interrupções e retomar o trabalho sem apagar o que já foi aprendido ou executado.

## Regra de Distinção de Ambientes
Existem dois ambientes diferentes que não devem ser confundidos:

1. Ambiente atual do agente já funcional nesta máquina
- É o contexto real do Mark/Jarvis rodando hoje no terminal
- Usa os caminhos atuais locais do Francisco
- Serve como base de memória, logs e continuidade do trabalho atual

2. Ambiente-alvo do produto em construção
- É o backend e frontend instaláveis do Mark Alfa
- Deve seguir as regras de empacotamento e instalação do `AgentContext`
- Deve prever:
  - instalação em `/opt/jarvis`
  - contexto dinâmico por usuário na máquina de destino
  - separação entre código do produto e contexto operacional do usuário

Importante:
As regras abaixo tratam principalmente da persistência do trabalho atual nesta máquina, sem apagar a noção de que o produto instalável futuro terá política própria de instalação e contexto em outras máquinas.

## Problema que este documento resolve
Os Marks sofrem de amnésia de sessão e podem ser interrompidos por falha, reinício, travamento, kill switch, troca de contexto ou perda de conectividade.
Sem disciplina de persistência, o agente volta a improvisar, repetir trabalho, perder decisões e quebrar continuidade.

## Princípio Geral
Todo trabalho relevante precisa deixar rastro suficiente para que:
- um humano entenda o estado atual
- o próprio Mark saiba onde parou
- uma retomada possa ocorrer sem recomeçar do zero
- mudanças estruturais não sejam esquecidas

## Duas Camadas de Persistência

### 1. Persistência operacional viva do agente atual nesta máquina
Caminho:
`/home/francisco/Documentos/JarvisMinion`

Função:
- memória persistente do agente
- logs de mudança
- contexto global do ambiente
- retomada após interrupção

### 2. Persistência de projeto
Caminho:
`/home/francisco/Documentos/repos/mark`

Função:
- trilha do trabalho no repositório
- itens a fazer, fazendo e feito
- documentação de pivotagens
- versionamento por Git

### 3. Persistência esperada do produto instalável futuro
O backend/frontend instaláveis do Mark Alfa deverão prever política própria de contexto operacional conforme os documentos de instalação e empacotamento do `AgentContext`.

Importante:
Essa persistência futura não substitui automaticamente a persistência atual do agente já funcional nesta máquina.

## Arquivos Obrigatórios

### `MemoriaDoJarvis.log`
Caminho:
`/home/francisco/Documentos/JarvisMinion/MemoriaDoJarvis.log`

Função:
Registrar memória estratégica e continuidade.

Deve registrar:
- decisão arquitetural relevante
- bugs encontrados
- hipóteses validadas ou descartadas
- testes executados
- correções aplicadas
- desvios de rota
- riscos identificados
- pendências
- ponto exato de parada
- próximo passo recomendado

Não deve virar:
- dump bruto e infinito de terminal
- cópia cega de logs extensos
- arquivo barulhento sem utilidade de retomada

Formato sugerido por entrada:
- data/hora
- contexto
- ação ou decisão
- resultado
- impacto
- próximo passo

### `change.log`
Caminho:
`/home/francisco/Documentos/JarvisMinion/change.log`

Função:
Registrar alterações objetivas e sensíveis.

Deve registrar:
- data/hora
- alvo alterado
- motivo
- comando ou operação
- resultado resumido

Exemplos de alvo:
- arquivo de sistema
- arquivo de configuração
- arquivo de código
- unit file
- script de empacotamento
- arquivo de documentação crítica

### `TODOList.md`
Caminho:
`/home/francisco/Documentos/repos/mark/TODOList.md`

Função:
Ser a trilha operacional do progresso do projeto.

Regras:
1. Ler primeiro `## A fazer`
2. Mover item iniciado para `## Fazendo`
3. Mover item concluído para `## Feito`
4. Não trabalhar silenciosamente fora do TODO em tarefas estruturais
5. Ao encerrar marco importante, preparar commit/push correspondente

### `pivotagem/`
Caminho:
`/home/francisco/Documentos/repos/mark/pivotagem`

Função:
Registrar mudanças de rota e decisões novas não previstas no plano inicial.

Obrigatório quando:
- surgir nova necessidade estrutural
- uma regra do plano precisar ser adaptada
- uma nova pasta/arquivo importante surgir
- uma limitação técnica obrigar revisão do desenho
- o agente adotar abordagem diferente da prevista

Conteúdo mínimo do arquivo de pivotagem:
- título do item
- contexto
- problema encontrado
- decisão tomada
- motivo da decisão
- impacto técnico
- impacto no roadmap
- próximos passos

## Regra de Escrita em Memória
O Mark deve escrever em memória sempre que ocorrer pelo menos um dos seguintes eventos:
1. início de etapa relevante
2. conclusão de etapa relevante
3. descoberta de bug importante
4. alteração de arquitetura
5. falha de teste relevante
6. correção confirmada
7. interrupção manual
8. travamento ou exceção crítica
9. mudança de escopo
10. preparação para encerrar sessão

## Regra de Escrita em change.log
O Mark deve registrar no `change.log` quando:
- alterar arquivo de sistema
- alterar configuração sensível
- criar ou alterar arquivo-chave do projeto
- instalar ou remover dependência relevante
- criar ou alterar unit file
- alterar scripts de build, empacotamento ou execução
- modificar arquivos centrais do backend ou frontend

## Regra de Leitura no Boot
Antes de iniciar nova sessão de trabalho, o Mark deve:
1. ler as últimas linhas de `MemoriaDoJarvis.log`
2. ler as últimas linhas de `change.log`
3. ler `README.md` dos contextos
4. reler documentos mandatórios
5. se estiver trabalhando no projeto Mark, reler `AgentContext`
6. ler o `TODOList.md`
7. identificar em que item parou ou qual é o próximo item lógico

## Regra de Retomada
Ao retomar uma sessão interrompida, o Mark deve responder internamente a estas perguntas antes de agir:
1. O que já foi feito?
2. O que estava sendo feito?
3. O que falhou?
4. O que foi apenas planejado?
5. Existe item em `## Fazendo` que precisa ser continuado?
6. Existe pivotagem aberta sem consolidação?
7. Existe mudança aplicada mas ainda não documentada?
8. O próximo passo ainda faz sentido?

## Retomada após Kill Switch
Se uma tarefa foi interrompida:
1. registrar o fato em `MemoriaDoJarvis.log`
2. registrar no `change.log` se houve alteração parcial relevante
3. marcar que a tarefa anterior foi abortada
4. não assumir que pode continuar exatamente do mesmo ponto
5. primeiro validar o estado do sistema
6. só então decidir entre:
   - retomar
   - refazer
   - voltar para modo PLAN

## Retomada após falha de hardware, reboot ou apagão
Ao voltar:
1. verificar memória persistente
2. verificar último item em `TODOList.md`
3. verificar se há arquivos parcialmente criados
4. verificar se há serviços em estado inconsistente
5. verificar se houve instalação incompleta
6. verificar se o backend ou frontend ficaram em estado quebrado
7. registrar a análise antes de seguir alterando

## Retomada após mudança de escopo
Quando o escopo mudar:
1. não continuar como se nada tivesse acontecido
2. registrar a mudança em memória
3. criar item no TODO se necessário
4. criar pivotagem se a mudança for estrutural
5. atualizar o plano antes da execução

## Regra de Granularidade
A persistência deve ser suficiente para retomada, mas não deve virar ruído.
Evitar:
- registrar cada comando trivial sem importância
- registrar texto demais sem síntese
- registrar apenas frases vagas como “continue depois”

Preferir:
- síntese objetiva
- evidência do que foi decidido
- evidência do que foi alterado
- indicação clara do próximo passo

## Regra de Estado do Projeto
Sempre que possível, cada sessão deve terminar com estes quatro estados coerentes:
1. memória atualizada
2. change.log atualizado
3. TODOList coerente
4. arquivos do projeto em estado compreensível

## Regra de Commit e Versionamento
Memória e TODO não substituem versionamento.
Ao concluir marco relevante:
1. revisar o estado dos arquivos
2. confirmar documentação mínima
3. garantir TODO coerente
4. realizar commit
5. realizar push quando aprovado

## Critério de Boa Persistência
A persistência é boa quando, após uma interrupção, o Mark ou o Francisco conseguem entender:
- onde estávamos
- o que foi feito
- o que faltou
- o que quebrou
- o que fazer em seguida

## Regra Final
Se uma decisão, alteração ou falha é importante o bastante para impactar a continuação do trabalho, ela é importante o bastante para ser persistida.

Também é obrigatório preservar a distinção entre:
- a persistência atual do agente já funcional nesta máquina
- a persistência esperada do produto instalável futuro
