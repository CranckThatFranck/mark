### Instruções de leitura e movimentação do documento:
**Inicie a leitura dos iténs em A fazer**: Está será sua lista de to-do divido em itens de ações. Cada workiten será contido em uma linha iniciado em - e finalizado em . 
** No ## Fazendo**: Deverá ser para onde você moverá o itém que você começou a trabalhar, para que possamos saber o que falta fazer e o que está sendo feito.
** Feito**: Quando finalizar o itém que estava trabalhando, mova o item para cá quando finalizado! Aqui deverá ser feito o push e commit para o repositório github nessa pasta.

## Feito
- Validar backend com testes reais subindo no novo modelo e trocando de região dinamicamente.
- Atualizar o README.md detalhando as novas configurações de Vertex AI, chaves, regiões e exemplos de caminhos de credenciais.
- Atualizar o README.md detalhando as novas configurações de Vertex AI, chaves, regiões e exemplos de caminhos de credenciais.
- Atualizar o frontend para permitir escolha ou edição de Região para Hotswap de modelos.
- Atualizar o frontend para permitir a inclusão de Custom Model ID.
- Atualizar o frontend para listar os novos modelos Vertex AI.
- Atualizar contrato/configuração (config_manager.py e protocol.py) para suportar modelo dinâmico e região.
- Implementar suporte à configuração de região padrão (us-east5) e override por modelo no backend.
- Implementar seleção de provedor baseada nas chaves de API/Vertex.
- Corrigir e padronizar o tratamento de variáveis VERTEXAI_PROJECT, VERTEXAI_LOCATION e GOOGLE_APPLICATION_CREDENTIALS.
- Configurar suporte completo aos modelos Vertex AI, mantendo suporte ao Gemini.
- Atualizar o modelo padrão de inicialização para vertex_ai/gemini-3.1-pro-preview-customtools.
- Atualizar o README.md do projeto com instruções de instalação do frontend.
- Atualizar o README.md do projeto com instruções de instalação do backend.
- Atualizar o README.md do projeto com requisitos, dependências e visão geral da aplicação.
- Concluir o marco final da versão simples e final do Mark Alfa.
- Revisar o README final, TODOList, memória persistente e pivotagens após a validação completa.
- Atualizar o README.md do projeto com instruções de operação, status, interrupção e troubleshooting.
- Atualizar o README.md do projeto com requisitos, dependências e visão geral da aplicação.
- Atualizar o README.md do projeto com instruções de instalação do backend.
- Atualizar o README.md do projeto com instruções de instalação do frontend.
- Criar estrutura de packaging do frontend para .rpm.
- Criar estrutura de packaging do frontend para .deb.
- Criar estrutura de packaging do backend para .rpm.
- Criar estrutura de packaging do backend para .deb.
- Validar start, stop, restart e status do backend via systemd.
- Validar instalação do backend em /opt/jarvis/backend.
- Corrigir eventuais falhas encontradas durante os testes finais.
- Executar nova rodada de validação final após correções.
- Executar checklist de aceite do backend.
- Executar checklist de aceite do frontend.
- Executar testes de fumaça do frontend.
- Criar scripts e arquivos necessários de pós-instalação do frontend, se aplicável.
- Criar launcher e arquivo .desktop do frontend quando aplicável.
- Criar assets mínimos do frontend, incluindo ícone e recursos necessários para empacotamento.
- Implementar persistência visual mínima do frontend.
- Implementar reconexão e tolerância a falhas no frontend.
- Implementar envio de execute_task, change_model, interrupt, get_status, get_config e update_config no frontend.
- Implementar a tela de configurações do frontend.
- Implementar área de exibição de message, code, console, status e system no frontend.
- Implementar a janela principal do frontend.
- Criar o cliente WebSocket do frontend.
- Criar a estrutura inicial do frontend em src/frontend.
- Definir oficialmente a stack do frontend e registrar a decisão no repositório.
- Criar o unit file do systemd para o backend.
- Implementar logs e observabilidade mínima do backend.
- Implementar o kill switch real com interrupção do grupo de processos.
- Implementar a action interrupt.
- Implementar rastreamento de tarefa ativa com PID e PGID.
- Implementar o isolamento de subprocessos por PGID.
- Implementar o modo Agent.
- Implementar o modo Plan.
- Implementar o fluxo de mensagens user, status, message, code, console e action_response.
- Integrar o backend ao agent_runner sem depender da CLI solta do Open Interpreter.

## Fazendo
- Regenerar pacotes .deb e .rpm de backend e frontend após atualizações da stack Vertex.
- Validar backend com testes reais subindo no novo modelo e trocando de região dinamicamente.
- Atualizar o frontend para permitir a inclusão de Custom Model ID.
- Atualizar o frontend para listar os novos modelos Vertex AI.

## A fazer
- Atualizar contrato/configuração (config_manager.py e protocol.py) para suportar modelo dinâmico e região.
- Atualizar o README.md detalhando as novas configurações de Vertex AI, chaves, regiões e exemplos de caminhos de credenciais.
- Validar backend com testes reais subindo no novo modelo e trocando de região dinamicamente.
- Regenerar pacotes .deb e .rpm de backend e frontend após atualizações da stack Vertex.
- Validar artefatos finais de empacotamento com as novas mudanças embutidas.
