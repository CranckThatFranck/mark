echo "##active_line2##"
# Mark Alfa
echo "##active_line3##"

echo "##active_line4##"
Este é o repositório oficial do Mark Alfa, um sistema composto por:
echo "##active_line5##"
- **Backend (Python)**: Um servidor WebSocket e HTTP local, isolado por systemd, responsável por rodar o Open Interpreter encapsulado e gerenciar o estado da máquina.
echo "##active_line6##"
- **Frontend (Python)**: Uma interface gráfica nativa em PyQt6/CustomTkinter que se conecta ao backend via WebSocket e exibe o chat e status de execução.
echo "##active_line7##"

echo "##active_line8##"
## Divisão de Ambientes
echo "##active_line9##"
Este repositório preserva a separação entre:
echo "##active_line10##"
1. **O ambiente atual do agente Jarvis**: que trabalha e executa suas tarefas em `/home/francisco/Documentos/JarvisMinion` e neste próprio repositório.
echo "##active_line11##"
2. **O ambiente do Produto Instalável Futuro**: onde a aplicação backend e frontend residirão em `/opt/jarvis` (com estrutura dinâmica por usuário para dados, respeitando o `AgentContext`).
echo "##active_line12##"

echo "##active_line13##"
## Documentação Completa
echo "##active_line14##"
A documentação completa de contexto, roadmap, arquitetura, política de diretórios e contratos JSON está na pasta `AgentContext/`.
echo "##active_line15##"

echo "##active_line16##"
## Estrutura Inicial (em andamento)
echo "##active_line17##"
```
echo "##active_line18##"
/src
echo "##active_line19##"
   /backend
echo "##active_line20##"
   /frontend
echo "##active_line21##"
/tests
echo "##active_line22##"
/docs
echo "##active_line23##"
/scripts
echo "##active_line24##"
/packaging
echo "##active_line25##"
/pivotagem
echo "##active_line26##"
```
echo "##active_line27##"

echo "##active_line28##"
## Como usar
echo "##active_line29##"
(Em construção)
echo "##active_line30##"

echo "##active_line31##"
