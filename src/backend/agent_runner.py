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

    def update_model(self, new_model: str):
        """Atualiza o modelo de LLM usado pelo interpreter"""
        self.interpreter.llm.model = new_model

    async def run_task(self, prompt: str, mode: str):
        """
        Executa a tarefa no interpreter.
        Aqui interceptaremos a saída assíncrona se necessário.
        """
        try:
            self.set_status("running", prompt)
            
            # TODO: a implementação real exigirá interceptar stdout/stderr usando subprocess
            # ou usando o motor interno do Open Interpreter generator-based
            # Por enquanto, chassi básico:
            
            await self.send_stream("status", "Pensando...")
            
            # Vamos testar o modo generator do Open Interpreter:
            for chunk in self.interpreter.chat(prompt, stream=True, display=False):
                # O chunk tem a forma de dict com 'role', 'type', 'content', etc.
                if isinstance(chunk, dict) and "content" in chunk:
                    # Roteia os tipos (message, code, console)
                    ctype = chunk.get("type", "message")
                    if ctype == "message":
                        await self.send_stream("message", chunk["content"])
                    elif ctype == "code":
                        await self.send_stream("code", chunk["content"])
                    elif ctype == "console":
                        await self.send_stream("console", chunk["content"])
                        
            # Quando acaba a tarefa...
            self.set_status("idle", None)
            await self.send_stream("status", "Tarefa concluída")
            
        except Exception as e:
            logger.error(f"Erro na execução da tarefa: {e}")
            self.set_status("idle", None)
            await self.send_stream("status", f"Erro: {str(e)}")

