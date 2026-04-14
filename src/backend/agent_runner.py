import asyncio
import logging
import os
import threading

from interpreter import interpreter

from config import DEFAULT_MODEL, INITIAL_RULES_FILE, LEGACY_ENV_KEYS, is_supported_model
from config_manager import load_initial_rules


logger = logging.getLogger(__name__)


class AgentRunner:
    """
    Invólucro controlado para executar o Open Interpreter.
    """

    def __init__(self, send_stream_cb, set_status_cb):
        self.send_stream = send_stream_cb
        self.set_status = set_status_cb
        self.interpreter = interpreter
        self._configure_interpreter()

    def _configure_interpreter(self):
        self.interpreter.auto_run = True
        self.interpreter.custom_instructions = load_initial_rules()
        logger.info(f"Regras iniciais do produto carregadas de {INITIAL_RULES_FILE}")
        self.update_model(DEFAULT_MODEL)

    def _clear_legacy_provider_environment(self):
        for env_key in LEGACY_ENV_KEYS:
            os.environ.pop(env_key, None)

    def update_model(self, new_model: str):
        if not is_supported_model(new_model):
            raise ValueError("Apenas modelos Gemini com prefixo gemini/ sao suportados")

        self._clear_legacy_provider_environment()
        self.interpreter.llm.model = new_model

        if os.environ.get("GOOGLE_API_KEY"):
            logger.info(f"Modelo do Open Interpreter atualizado para: {new_model}")
        else:
            logger.warning(
                "GOOGLE_API_KEY nao encontrado no ambiente. O backend inicia, "
                "mas a execucao do agente vai falhar ate a chave ser configurada."
            )

    async def _stream_chat_chunks(self, prompt: str):
        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()

        def worker():
            try:
                for chunk in self.interpreter.chat(prompt, stream=True, display=False):
                    loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

        threading.Thread(target=worker, daemon=True).start()

        while True:
            item_type, payload = await queue.get()
            if item_type == "chunk":
                yield payload
                continue
            if item_type == "error":
                raise payload
            break

    async def run_task(self, prompt: str, mode: str):
        try:
            self.set_status("running", prompt)
            await self.send_stream("user", prompt)

            final_prompt = prompt
            if mode == "plan":
                final_prompt = (
                    "Voce esta no modo PLAN. Seu objetivo nao e executar codigo ainda, "
                    "mas descrever o plano de acao, checagens de seguranca e arquivos envolvidos. "
                    "Mostre o plano em Markdown e pergunte se pode executar. "
                    f"A tarefa e: {prompt}"
                )
                await self.send_stream("status", "Analisando contexto no modo plan...")
            else:
                await self.send_stream("status", "Executando em modo agent...")

            async for chunk in self._stream_chat_chunks(final_prompt):
                if isinstance(chunk, dict) and "content" in chunk:
                    content_type = chunk.get("type", "message")
                    if content_type in {"message", "code", "console"}:
                        await self.send_stream(content_type, chunk["content"])

            if mode == "plan":
                await self.send_stream("system", "MODO_PLAN_CONCLUIDO")

            self.set_status("idle", None)
            await self.send_stream("status", "Tarefa concluida.")

        except Exception as exc:
            logger.error(f"Erro na execucao da tarefa: {exc}")
            self.set_status("idle", None)
            await self.send_stream("status", f"Erro: {str(exc)}")
