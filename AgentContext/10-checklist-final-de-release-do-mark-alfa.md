# Checklist Final de Release do Mark Alfa

## Objetivo
Este documento define a régua final de liberação do Mark Alfa.
O release só pode ser considerado aprovado quando os itens críticos abaixo forem verificados e marcados como concluídos.

## Regra de Distinção de Ambientes
Existem dois ambientes diferentes que não devem ser confundidos:

1. Ambiente atual do agente já funcional nesta máquina
- É o Mark/Jarvis que já roda hoje no terminal
- Usa os caminhos reais atuais do ambiente do Francisco
- Serve como base do trabalho de desenvolvimento atual

2. Ambiente-alvo do produto em construção
- É o backend e frontend instaláveis do Mark Alfa
- Deve seguir as regras de portabilidade, empacotamento e instalação do `AgentContext`
- Deve prever:
  - `/opt/jarvis`
  - `/opt/jarvis/backend`
  - `/opt/jarvis/frontend`
  - contexto operacional dinâmico por usuário

Importante:
Este checklist avalia principalmente o produto em construção.
Ele não apaga a existência do ambiente atual do agente já funcional nesta máquina.

## Regra-Mãe
“Funcionar na máquina do autor” não é critério suficiente de release.
O Mark Alfa só está pronto quando:
- roda com caminhos corretos
- instala de forma reproduzível
- respeita a arquitetura definida
- possui backend e frontend separados
- mantém continuidade de contexto
- pode ser interrompido com segurança
- está documentado

## Bloco 1 - Coerência documental
Confirmar:
- [ ] Constituição do agente revisada
- [ ] README de contextos revisado
- [ ] Contrato operacional revisado
- [ ] Contrato JSON revisado
- [ ] Roadmap revisado
- [ ] Critérios de aceite revisados
- [ ] Política de diretórios revisada
- [ ] Política de persistência revisada
- [ ] Política de empacotamento revisada
- [ ] Guia de backend revisado
- [ ] Guia de frontend revisado
- [ ] Nenhum documento oficial depende de `/home/francisco/...` como caminho de produto
- [ ] Caminhos históricos do agente atual foram mantidos apenas onde representam o ambiente atual real
- [ ] A documentação distingue claramente:
  - ambiente atual do agente nesta máquina
  - produto instalável futuro

## Bloco 2 - Regras de caminho e portabilidade
Confirmar:
- [ ] Instalação principal do produto usa `/opt/jarvis`
- [ ] Backend instala em `/opt/jarvis/backend`
- [ ] Frontend instala em `/opt/jarvis/frontend`
- [ ] O sistema não assume usuário fixo
- [ ] O sistema não assume `Documents` sem detecção
- [ ] O sistema não assume `Documentos` sem detecção
- [ ] O backend resolve o caminho de contexto dinamicamente
- [ ] O fallback de caminho está documentado
- [ ] O projeto não contém hardcode indevido de ambiente do autor

## Bloco 3 - Contexto do usuário
Confirmar:
- [ ] O sistema cria ou usa `~/Documents/JarvisMark` quando apropriado
- [ ] O sistema cria ou usa `~/Documentos/JarvisMark` quando apropriado
- [ ] O sistema usa fallback documentado quando nenhuma das duas existir
- [ ] O contexto do usuário contém estrutura mínima funcional
- [ ] Os arquivos de memória, logs e estado ficam fora de `/opt/jarvis`
- [ ] O backend encontra o contexto correto no boot

## Bloco 4 - Backend
Confirmar:
- [ ] O backend sobe sem terminal manual permanente
- [ ] O backend responde `sync_state`
- [ ] O backend responde `healthcheck`
- [ ] O backend responde `get_status`
- [ ] O backend responde `get_models`
- [ ] O backend responde `get_config`
- [ ] O backend responde `update_config`
- [ ] O backend responde `change_model`
- [ ] O backend responde `execute_task`
- [ ] O backend responde `interrupt`
- [ ] O backend opera com Open Interpreter embutido
- [ ] O backend não depende oficialmente da CLI solta do Open Interpreter
- [ ] O backend respeita Plan
- [ ] O backend respeita Agent
- [ ] O backend retorna ao estado esperado após tarefa concluída
- [ ] O backend mantém configuração entre reinícios
- [ ] O backend registra memória e mudanças relevantes

## Bloco 5 - Kill switch e contenção
Confirmar:
- [ ] Tarefa longa pode ser interrompida
- [ ] A interrupção não deixa o daemon preso
- [ ] A interrupção não derruba o daemon desnecessariamente
- [ ] O backend aceita nova tarefa após interrupção
- [ ] Não há processo zumbi evidente após interrupção
- [ ] O estado interno volta para condição segura
- [ ] A interrupção é refletida corretamente no frontend

## Bloco 6 - systemd
Confirmar:
- [ ] Existe unit file funcional
- [ ] `systemctl start` funciona
- [ ] `systemctl stop` funciona
- [ ] `systemctl restart` funciona
- [ ] `systemctl status` funciona
- [ ] Os logs são observáveis por meios padrão
- [ ] O serviço sobe corretamente após reboot, quando essa política estiver habilitada
- [ ] O backend não depende de tray icon

## Bloco 7 - Frontend
Confirmar:
- [ ] O frontend abre em ambiente gráfico suportado
- [ ] O frontend conecta em backend local
- [ ] O frontend conecta em backend remoto
- [ ] O frontend recebe `sync_state`
- [ ] O frontend exibe mensagens do agente
- [ ] O frontend exibe código
- [ ] O frontend exibe console
- [ ] O frontend permite selecionar Plan/Agent
- [ ] O frontend permite trocar modelo
- [ ] O frontend possui kill switch funcional
- [ ] O frontend possui tela de configurações
- [ ] O frontend permite configurar host alvo
- [ ] O frontend permite configurar host master
- [ ] O frontend permite configurar nome do agente
- [ ] O frontend tolera desconexão e reconexão sem quebrar

## Bloco 8 - Integração ponta a ponta
Confirmar:
- [ ] Frontend e backend usam o mesmo contrato JSON
- [ ] O fluxo de tarefa funciona de ponta a ponta
- [ ] O fluxo de mudança de modelo funciona de ponta a ponta
- [ ] O fluxo Plan funciona de ponta a ponta
- [ ] O fluxo Agent funciona de ponta a ponta
- [ ] O fluxo de interrupção funciona de ponta a ponta
- [ ] O estado mostrado no frontend condiz com o backend
- [ ] O backend remoto pode ser operado pelo frontend usando host configurado

## Bloco 9 - Empacotamento
Confirmar:
- [ ] Existe pacote `.rpm` do backend
- [ ] Existe pacote `.deb` do backend
- [ ] Existe pacote `.rpm` do frontend
- [ ] Existe pacote `.deb` do frontend
- [ ] Os pacotes instalam fora da máquina de desenvolvimento
- [ ] Os pacotes colocam os arquivos em `/opt/jarvis`
- [ ] Os pacotes respeitam a separação backend/frontend
- [ ] Dependências relevantes estão tratadas ou documentadas
- [ ] O backend instalado por pacote sobe corretamente
- [ ] O frontend instalado por pacote abre corretamente

## Bloco 10 - Teste em ambiente diferente do autor
Confirmar:
- [ ] O backend foi testado em máquina com usuário diferente de `francisco`
- [ ] O frontend foi testado em máquina com usuário diferente de `francisco`
- [ ] Foi testado em ambiente com `Documents`
- [ ] Foi testado em ambiente com `Documentos`
- [ ] Foi testado o fallback sem ambas as pastas
- [ ] O sistema se comportou corretamente sem hardcodes ocultos

## Bloco 11 - Segurança operacional
Confirmar:
- [ ] Não há uso arquiteturalmente aceito de `rm` destrutivo
- [ ] Há política de backup antes de alteração crítica
- [ ] O backend respeita a constituição do agente
- [ ] O frontend não executa papel que pertence ao backend
- [ ] A separação de responsabilidades está preservada
- [ ] Os caminhos de contexto e instalação estão claros
- [ ] Não há dependência de ações manuais obscuras

## Bloco 12 - Persistência e retomada
Confirmar:
- [ ] `MemoriaDoJarvis.log` ou equivalente de contexto está sendo usado corretamente
- [ ] `change.log` ou equivalente de contexto está sendo usado corretamente
- [ ] O `TODOList.md` reflete o estado real do trabalho
- [ ] Pivotagens relevantes foram registradas
- [ ] O projeto consegue ser retomado após interrupção com rastreabilidade suficiente

## Bloco 13 - Documentação do produto
Confirmar:
- [ ] `README.md` contém visão geral
- [ ] `README.md` contém requisitos
- [ ] `README.md` contém dependências
- [ ] `README.md` contém instalação do backend
- [ ] `README.md` contém instalação do frontend
- [ ] `README.md` contém operação do backend
- [ ] `README.md` contém operação do frontend
- [ ] `README.md` contém troubleshooting básico
- [ ] `README.md` contém política de caminhos
- [ ] `README.md` explica `/opt/jarvis`
- [ ] `README.md` explica a pasta dinâmica de contexto do usuário
- [ ] `README.md` distingue claramente o ambiente atual do agente e o produto futuro instalável

## Bloco 14 - Estado do repositório
Confirmar:
- [ ] `TODOList.md` atualizado
- [ ] Itens concluídos movidos para `## Feito`
- [ ] Itens em andamento coerentes em `## Fazendo`
- [ ] Novos itens necessários registrados
- [ ] Arquivos estruturais versionados
- [ ] Memória persistente atualizada
- [ ] Commit do marco preparado ou realizado
- [ ] Push realizado quando aprovado

## Bloco 15 - Go / No-Go
O release do Mark Alfa está liberado apenas se:
- [ ] nenhum item crítico acima estiver pendente
- [ ] não houver hardcode inválido de caminhos
- [ ] backend e frontend estiverem funcionais e separados
- [ ] empacotamento estiver validado
- [ ] documentação mínima estiver pronta
- [ ] o sistema puder ser instalado em máquina diferente da original
- [ ] o Mark puder ser interrompido com segurança
- [ ] a continuidade do trabalho estiver protegida

## Regra Final
Se um item crítico deste checklist falhar, o Mark Alfa não está pronto para release.
Corrigir primeiro. Liberar depois.

Também é obrigatório preservar a distinção entre:
- o ambiente atual do agente já funcional nesta máquina
- o produto instalável futuro que este checklist está avaliando
