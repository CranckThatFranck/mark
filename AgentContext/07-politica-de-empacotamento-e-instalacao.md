# Política de Empacotamento e Instalação do Mark

## Objetivo
Este documento define como o backend e o frontend do Mark devem ser instalados, distribuídos e preparados para execução em máquinas Fedora e Ubuntu, sem depender do ambiente específico do autor do projeto.

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
- Deve seguir as regras desta política de empacotamento e instalação
- Deve prever:
  - instalação principal em `/opt/jarvis`
  - backend em `/opt/jarvis/backend`
  - frontend em `/opt/jarvis/frontend`
  - contexto operacional dinâmico por usuário na máquina de destino

Importante:
As regras desta política se aplicam ao produto instalável futuro.
Elas não substituem automaticamente o ambiente atual do agente já funcional nesta máquina.

## Regra-Mãe
O produto deve ser instalável fora da máquina de desenvolvimento sem depender:
- do usuário `francisco`
- de caminhos fixos em `/home/francisco`
- de nomes de pasta específicos sem detecção
- de configuração manual obscura
- de terminal aberto permanentemente para o backend existir

## Raízes Oficiais de Instalação

### 1. Instalação da aplicação
A raiz oficial da instalação do produto é:
`/opt/jarvis`

Regra:
1. Todo conteúdo principal instalado do produto deve residir abaixo de `/opt/jarvis`.
2. Backend e frontend devem ser organizados de forma clara dentro dessa raiz.
3. O instalador não deve espalhar arbitrariamente arquivos executáveis por múltiplos diretórios sem necessidade.

Estrutura sugerida:
- `/opt/jarvis/backend`
- `/opt/jarvis/frontend`
- `/opt/jarvis/shared` opcional
- `/opt/jarvis/runtime` opcional
- `/opt/jarvis/version` opcional

### 2. Contexto operacional por usuário
O contexto operacional do Mark não deve ser instalado com caminhos fixos contendo nome de usuário hardcoded.

Regra:
O caminho deve ser resolvido dinamicamente a partir do ambiente do usuário da máquina onde o produto estiver rodando.

Padrão funcional:
1. Obter `HOME` do usuário real
2. Detectar preferencialmente:
   - `~/Documents`
   - `~/Documentos`
3. Criar e usar:
   - `~/Documents/JarvisMark`
   - ou `~/Documentos/JarvisMark`
4. Se nenhuma das duas pastas-base existir, o instalador deve criar a estrutura padrão escolhida pela política oficial do projeto

Estrutura sugerida da raiz de contexto:
- `~/Documents/JarvisMark`
ou
- `~/Documentos/JarvisMark`

Subpastas sugeridas:
- `contextos`
- `logs`
- `memoria`
- `estado`
- `tmp`
- `lixo`

Exemplos:
- `~/Documents/JarvisMark/contextos`
- `~/Documents/JarvisMark/logs`
- `~/Documents/JarvisMark/memoria`
- `~/Documents/JarvisMark/estado`

## Regra de Portabilidade
O produto deve funcionar em:
- Fedora
- Ubuntu

Sem depender de:
- idioma específico do sistema
- estrutura de diretório pessoal idêntica entre máquinas
- nome de usuário específico
- ambiente virtual manual já existente

## Empacotamento Separado

### Backend
O backend deve ter pacote próprio.

Responsabilidades do pacote de backend:
- instalar arquivos do backend em `/opt/jarvis/backend`
- instalar arquivos auxiliares necessários
- instalar unit file do systemd
- preparar diretórios necessários
- preparar arquivo de configuração ou exemplo
- registrar dependências necessárias
- documentar pós-instalação

### Frontend
O frontend deve ter pacote próprio.

Responsabilidades do pacote de frontend:
- instalar arquivos do frontend em `/opt/jarvis/frontend`
- instalar launcher gráfico quando aplicável
- instalar ícones e atalhos quando aplicável
- registrar dependências gráficas necessárias
- não instalar backend por obrigação acoplada, salvo dependência explicitamente documentada

## Formatos de Pacote
O projeto deve prever:
- `.rpm` para Fedora e derivados
- `.deb` para Ubuntu e derivados

Regra:
Backend e frontend devem possuir processos de empacotamento independentes.

## Dependências
Os pacotes devem considerar tudo o que for necessário para rodar fora da máquina do autor, inclusive:
- versão correta do Python suportado
- bibliotecas Python exigidas
- Open Interpreter, quando exigido pela arquitetura final
- dependências de UI, quando exigidas pelo frontend
- arquivos de serviço
- dependências de rede e runtime essenciais

## Python
Baseline operacional inicial:
- Python 3.12

Regra:
1. O projeto deve documentar claramente a versão mínima suportada.
2. O instalador ou a documentação devem deixar explícito quando o sistema precisar preparar Python compatível.
3. Não assumir que toda máquina já possui a versão correta.

## Arquitetura de Instalação do Backend
O backend deve:
- residir em `/opt/jarvis/backend`
- ser iniciado por systemd
- não depender de tray icon
- não depender de terminal aberto
- conseguir subir sozinho após instalação e configuração mínima
- ler seus caminhos de contexto dinamicamente

Estrutura sugerida:
- `/opt/jarvis/backend/app`
- `/opt/jarvis/backend/venv` opcional
- `/opt/jarvis/backend/config`
- `/opt/jarvis/backend/bin`
- `/opt/jarvis/backend/systemd`

## Arquitetura de Instalação do Frontend
O frontend deve:
- residir em `/opt/jarvis/frontend`
- ser instalável apenas em máquinas com interface gráfica
- se conectar ao backend local ou remoto
- usar o contrato oficial JSON/WebSocket
- não conter lógica de sistema que pertença ao backend

Estrutura sugerida:
- `/opt/jarvis/frontend/app`
- `/opt/jarvis/frontend/bin`
- `/opt/jarvis/frontend/assets`
- `/opt/jarvis/frontend/desktop`

## Contexto Persistente do Usuário
O instalador ou o primeiro boot do backend deve preparar a raiz de contexto do usuário.

Objetivo:
Criar um lugar previsível para:
- memória do agente
- logs de mudança
- estados persistidos
- contextos adicionais
- trilha de retomada

Arquivos esperados nessa raiz:
- `memoria/MemoriaDoJarvis.log`
- `logs/change.log`
- `estado/backend_state.json` ou equivalente
- `contextos/README.md`
- `contextos/jarvis_rules.txt`

## Regra de Descoberta de Caminho
O código do backend e do instalador deve implementar resolução dinâmica de caminho.

Ordem sugerida:
1. Ler `HOME`
2. Verificar existência de `~/Documents`
3. Verificar existência de `~/Documentos`
4. Criar `JarvisMark` no primeiro diretório válido encontrado
5. Se nenhum existir, criar uma política de fallback documentada

Fallback sugerido:
- criar `~/JarvisMark`

## Regra de Fallback
Se o ambiente não possuir `Documents` nem `Documentos`, o sistema deve:
1. não falhar silenciosamente
2. não inventar caminho obscuro
3. registrar a decisão
4. usar fallback documentado, por exemplo:
   - `~/JarvisMark`

## Configuração
O instalador deve separar:
- configuração da aplicação
- contexto do usuário
- código do produto

Regra:
1. Código do produto vive em `/opt/jarvis`
2. Estado e contexto do usuário vivem na pasta dinâmica do usuário
3. Configuração do serviço pode viver onde fizer mais sentido para o empacotamento, mas deve ser documentada

## systemd
O backend deve ser operado por systemd.

O pacote do backend deve prever:
- arquivo `.service`
- diretório de trabalho correto
- comando de execução correto
- política de reinício
- dependência de rede quando necessária
- logs observáveis de forma padrão

## Pós-instalação
O instalador do backend deve realizar ou orientar claramente:
- criação dos diretórios necessários
- validação do caminho de contexto do usuário
- preparação de arquivos mínimos
- habilitação opcional do serviço
- instruções de start, stop, restart e status

## README Final
Ao final do Mark Alfa, o `README.md` do projeto deve listar claramente:
- requisitos
- versões suportadas
- dependências
- instalação backend
- instalação frontend
- estrutura de diretórios
- caminho oficial `/opt/jarvis`
- política de contexto por usuário
- troubleshooting básico
- distinção entre:
  - ambiente atual do agente nesta máquina
  - produto instalável futuro

## O que é proibido
1. Hardcode de `/home/francisco/...`
2. Assumir que a máquina terá pasta `Documentos`
3. Assumir que a máquina terá pasta `Documents`
4. Assumir que o usuário será `ubuntu`, `francisco` ou qualquer outro
5. Misturar código do produto com memória do usuário no mesmo diretório sem motivo
6. Fazer o backend existir apenas em terminal manual

## Critério de Sucesso
A política de empacotamento e instalação está correta quando:
- backend e frontend instalam separadamente
- a instalação principal fica em `/opt/jarvis`
- o contexto do usuário é resolvido dinamicamente
- o produto roda em outra máquina sem depender do ambiente do autor
- tudo isso está documentado de forma clara e reproduzível

## Regra Final
Esta política descreve a instalação e distribuição do produto futuro.
Ela não substitui o ambiente atual do agente já funcional nesta máquina.
