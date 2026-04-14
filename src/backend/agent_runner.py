import asyncio
import sys
import logging
import os
import pty
from interpreter import interpreter

logger = logging.getLogger(__name__)

class AgentRunner:
    """
    Invólucro controlado para executar o Open Interpreter.
    Garante que o motor use a versão instalada no ambiente atual e não rode
    descontroladamente como CLI de terminal.
    """
    
    def __init__(self, send_stream_cb, set_status_cb):
        # Callbacks para comunicação com o websocket
        self.send_stream = send_stream_cb
        self.set_status = set_status_cb
        self.interpreter = interpreter
        self._configure_interpreter()

    def _configure_interpreter(self):
        """Configurações básicas seguras do interpreter"""
        self.interpreter.auto_run = True
        self.interpreter.llm.model = "gemini-2.5-flash" # default start
        # Podemos adicionar limits aqui

    def update_model(self, new_model: str, region: str = None):
        """
        Atualiza o modelo de LLM usado pelo interpreter e as variaveis
        necessárias para chamadas Vertex AI baseando-se no que está já no OS ou env.
        """
        self.interpreter.llm.model = new_model
        
        # O litellm/open-interpreter precisa de dicas no environment local
        # se for usar o vertex_ai. A responsabilidade de prover os dados nas vars é do operador,
        # nós só amarramos os pontos pro provider.
        if "vertex_ai" in new_model:
            # Puxa o location do argumento que veio do frontend (override) ou env default e injeta VERTEX_LOCATION e VERTEXAI_LOCATION pro litellm ler
            final_region = region if region else os.environ.get("VERTEXAI_LOCATION", "us-east5")
            os.environ["VERTEX_LOCATION"] = final_region
            os.environ["VERTEXAI_LOCATION"] = final_region
            # Não injetamos chaves aqui. O Operator que precisa ter GOOGLE_APPLICATION_CREDENTIALS ou VERTEXAI_PROJECT no ambiente/systemd

        logger.info(f"Modelo atualizado para {new_model}, Região para VertexAI: {os.environ.get('VERTEXAI_LOCATION', 'us-east5')}")


    async def run_task(self, prompt: str, mode: str):
        """
        Executa a tarefa no interpreter considerando o modo Plan vs Agent.
        """
        try:
            self.set_status("running", prompt)
            
            await self.send_stream("user", prompt)
            
            # Formata prompt baseado no modo
            final_prompt = prompt
            if mode == "plan":
                final_prompt = (
                    "Você está no modo PLAN (Planejamento de escopo). "
                    "Seu objetivo não é executar código ainda, mas sim descrever o plano de ação, "
                    "etapas, checagens de segurança e arquivos envolvidos. "
                    "Mostre o plano formatado em Markdown e pergunte se pode executar. "
                    "Ignorar essa regra é uma violação do contrato operacional. "
                    f"A tarefa é: {prompt}"
                )
                await self.send_stream("status", "Analisando contexto no modo Plan...")
            else:
                await self.send_stream("status", "Executando em modo Agent...")

            for chunk in self.interpreter.chat(final_prompt, stream=True, display=False):
                if isinstance(chunk, dict) and "content" in chunk:
                    ctype = chunk.get("type", "message")
                    # O OI usa "message" (fala da IA), "code" (código executado), "console" (saída)
                    if ctype in ["message", "code", "console"]:
                        await self.send_stream(ctype, chunk["content"])
                        
            # Quando a execução finaliza
            
            # Retorno automático para Agent se estiver em Plan (conforme contrato de que plano finalizado volta pra execução)
            if mode == "plan":
                # Sinaliza ao servidor que deve mudar o estado globalmente
                # Para evitar dependência circular aqui, enviaremos um stream system
                await self.send_stream("system", "MODO_PLAN_CONCLUIDO")
                
            self.set_status("idle", None)
            await self.send_stream("status", "Tarefa concluída.")
            
        except Exception as e:
            logger.error(f"Erro na execução da tarefa: {e}")
            self.set_status("idle", None)
            await self.send_stream("status", f"Erro: {str(e)}")


