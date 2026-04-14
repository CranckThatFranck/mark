import asyncio
import logging
import os
import threading
from typing import Callable

from interpreter import interpreter

from config import DEFAULT_MODEL, INITIAL_RULES_FILE, LEGACY_ENV_KEYS, MODEL_FALLBACK_CHAIN, is_supported_model
from config_manager import load_initial_rules
from credentials import GeminiCredentialStore
from observability import log_error, log_operation, redact_text
from tool_sanitizer import install_litellm_tool_sanitizer


logger = logging.getLogger(__name__)


INVALID_TOOL_PAYLOAD_MARKERS = (
    "jsondecodeerror",
    "json.loads",
    "expecting value",
    "function.arguments",
    "invalid function.arguments",
    "arguments is not valid json",
    "invalid tool arguments",
    "failed to parse tool arguments",
    "invalid arguments json",
)
AUTH_MARKERS = (
    "authenticationerror",
    "api key not valid",
    "api_key_invalid",
    "invalid api key",
    "unauthorized",
    "invalid authentication",
)
QUOTA_MARKERS = (
    "insufficient_quota",
    "quota",
    "resource exhausted",
    "daily limit",
    "exceeded your current quota",
)
RATE_LIMIT_MARKERS = (
    "rate limit",
    "too many requests",
    "429",
)
TOKEN_LIMIT_MARKERS = (
    "token limit",
    "context length",
    "too many tokens",
    "maximum context length",
)
PROVIDER_UNAVAILABLE_MARKERS = (
    "temporarily unavailable",
    "service unavailable",
    "provider unavailable",
    "upstream",
    "timeout",
    "connection error",
    "internal error",
    "503",
)


class AgentRunner:
    """
    Invólucro controlado para executar o Open Interpreter.
    """

    def __init__(
        self,
        send_stream_cb,
        set_status_cb,
        runtime_state_cb: Callable | None = None,
        credential_store=None,
        model_change_cb: Callable | None = None,
    ):
        self.send_stream = send_stream_cb
        self.set_status = set_status_cb
        self.runtime_state_cb = runtime_state_cb or model_change_cb
        self.credential_store = credential_store or GeminiCredentialStore()
        self.interpreter = interpreter
        self.active_model = DEFAULT_MODEL
        self.max_payload_retries = 2
        self.max_recoverable_retries = len(MODEL_FALLBACK_CHAIN) + 4
        self._configure_interpreter()

    def _configure_interpreter(self):
        self.interpreter.auto_run = True
        self.interpreter.custom_instructions = load_initial_rules()
        install_litellm_tool_sanitizer(self._on_tool_call_sanitized)
        logger.info(f"Regras iniciais do produto carregadas de {INITIAL_RULES_FILE}")
        log_operation("backend_rules_loaded", rules_file=str(INITIAL_RULES_FILE))
        self.update_model(DEFAULT_MODEL, reason="startup")

    def _on_tool_call_sanitized(self, payload: dict):
        log_operation(
            "tool_call_payload_sanitized",
            model=self.active_model,
            tool_name=payload.get("tool_name"),
            strategy=payload.get("strategy"),
            choice_index=payload.get("choice_index"),
            message_index=payload.get("message_index"),
            phase=payload.get("phase", "unknown"),
        )
        logger.warning(
            "Saneamento de tool call aplicado (model=%s tool=%s strategy=%s phase=%s)",
            self.active_model,
            payload.get("tool_name"),
            payload.get("strategy"),
            payload.get("phase", "unknown"),
        )

    def _clear_legacy_provider_environment(self):
        for env_key in LEGACY_ENV_KEYS:
            os.environ.pop(env_key, None)

    def refresh_runtime_api_key(self, reason: str = "runtime_refresh"):
        active = self.credential_store.apply_to_environment()
        self.interpreter.llm.api_key = active.get("secret") or None
        if active.get("source") == "missing":
            logger.warning(
                "Nenhuma chave Gemini disponivel (persistida ou variavel de ambiente Gemini). "
                "As proximas chamadas ao modelo podem falhar."
            )
            log_error("gemini_api_key_missing", reason=reason)
        else:
            log_operation(
                "gemini_api_key_applied",
                reason=reason,
                source=active.get("source"),
                active_key_id=active.get("id"),
                active_key_masked=active.get("masked"),
            )
        return active

    def update_model(self, new_model: str, reason: str = "manual"):
        if not is_supported_model(new_model):
            raise ValueError("Apenas modelos Gemini com prefixo gemini/ sao suportados")

        self._clear_legacy_provider_environment()
        active_key = self.refresh_runtime_api_key(reason=f"model_update:{reason}")

        previous_model = self.active_model
        self.interpreter.llm.model = new_model
        self.active_model = new_model

        log_operation(
            "model_switched",
            reason=reason,
            previous_model=previous_model,
            current_model=new_model,
            key_source=active_key.get("source"),
            active_key_id=active_key.get("id"),
        )

        if active_key.get("source") != "missing":
            logger.info(f"Modelo do Open Interpreter atualizado para: {new_model}")
        else:
            logger.warning(
                "Nenhuma chave Gemini valida encontrada no ambiente persistido/variavel. O backend inicia, "
                "mas a execucao do agente vai falhar ate a chave ser configurada."
            )

    async def _notify_runtime_state_change(self, new_model: str, reason: str, details: str):
        if not self.runtime_state_cb:
            return
        maybe_result = self.runtime_state_cb(new_model, reason, redact_text(details))
        if asyncio.iscoroutine(maybe_result):
            await maybe_result

    @staticmethod
    def classify_error(exc: Exception) -> str:
        text = str(exc).lower()
        if any(marker in text for marker in INVALID_TOOL_PAYLOAD_MARKERS):
            return "invalid_tool_payload"
        if any(marker in text for marker in AUTH_MARKERS):
            return "auth"
        if any(marker in text for marker in QUOTA_MARKERS):
            return "quota"
        if any(marker in text for marker in RATE_LIMIT_MARKERS):
            return "rate_limit"
        if any(marker in text for marker in TOKEN_LIMIT_MARKERS):
            return "token_limit"
        if any(marker in text for marker in PROVIDER_UNAVAILABLE_MARKERS):
            return "provider_unavailable"
        return "unknown"

    @staticmethod
    def _build_payload_recovery_prompt(original_prompt: str):
        return (
            "Continue a tarefa sem recomecar do zero e sem repetir etapas concluidas. "
            "Toda tool call deve ter function.arguments em JSON valido e canonico. "
            "Para chamadas execute, envie um objeto JSON explicito com campos claros. "
            f"Tarefa original: {original_prompt}"
        )

    @staticmethod
    def _build_provider_recovery_prompt(original_prompt: str):
        return (
            "Houve uma recuperacao automatica de execucao. "
            "Continue a tarefa exatamente do ponto em que parou, sem perder contexto. "
            f"Tarefa original: {original_prompt}"
        )

    def _fallback_candidates(self):
        if self.active_model in MODEL_FALLBACK_CHAIN:
            current_index = MODEL_FALLBACK_CHAIN.index(self.active_model)
            return MODEL_FALLBACK_CHAIN[current_index + 1 :]
        return MODEL_FALLBACK_CHAIN[:]

    async def _try_key_rotation_before_fallback(self, category: str, failure: Exception) -> bool:
        if category != "quota":
            return False

        rotated = self.credential_store.rotate_key_after_quota()
        if not rotated:
            return False

        active = self.refresh_runtime_api_key(reason=f"auto_rotate:{category}")
        log_operation(
            "gemini_api_key_rotated_auto",
            reason=category,
            model=self.active_model,
            from_key_id=rotated.get("from_id"),
            to_key_id=rotated.get("to_id"),
            to_key_masked=rotated.get("to_masked"),
        )
        await self.send_stream(
            "system",
            (
                "Quota/rate limit detectado. Rotacao automatica de API key Gemini aplicada "
                f"(chave ativa: {active.get('masked') or 'indisponivel'}). Tentando continuar no mesmo modelo."
            ),
        )
        logger.warning(
            "Rotacao automatica de chave Gemini antes de fallback (categoria=%s model=%s erro=%s)",
            category,
            self.active_model,
            failure,
        )
        await self._notify_runtime_state_change(
            self.active_model,
            "api_key_rotation:quota",
            str(failure),
        )
        return True

    async def _try_model_fallback(self, category: str, failure: Exception) -> bool:
        previous_model = self.active_model
        for candidate in self._fallback_candidates():
            try:
                self.update_model(candidate, reason=f"auto_fallback:{category}")
            except Exception as switch_error:
                log_error(
                    "model_fallback_switch_failed",
                    switch_error,
                    from_model=previous_model,
                    candidate_model=candidate,
                    reason=category,
                )
                continue

            log_operation(
                "model_fallback_success",
                reason=category,
                from_model=previous_model,
                to_model=candidate,
                trigger_error=str(failure),
            )
            await self.send_stream(
                "system",
                (
                    "Fallback automatico de modelo ativado: "
                    f"{previous_model} -> {candidate} (motivo: {category})."
                ),
            )
            await self._notify_runtime_state_change(
                candidate,
                f"auto_fallback:{category}",
                redact_text(str(failure)),
            )
            return True

        log_error(
            "model_fallback_exhausted",
            failure,
            model=previous_model,
            reason=category,
        )
        return False

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
            log_operation(
                "task_started",
                mode=mode,
                model=self.active_model,
                prompt_preview=prompt[:140],
            )

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

            payload_retries = 0
            recoverable_retries = 0
            attempt = 0
            prompt_to_run = final_prompt

            while True:
                attempt += 1
                log_operation(
                    "task_attempt_started",
                    mode=mode,
                    model=self.active_model,
                    attempt=attempt,
                )

                try:
                    async for chunk in self._stream_chat_chunks(prompt_to_run):
                        if isinstance(chunk, dict) and "content" in chunk:
                            content_type = chunk.get("type", "message")
                            if content_type in {"message", "code", "console"}:
                                await self.send_stream(content_type, chunk["content"])
                    break
                except Exception as exc:
                    category = self.classify_error(exc)
                    log_error(
                        "task_attempt_failed",
                        exc,
                        mode=mode,
                        model=self.active_model,
                        attempt=attempt,
                        category=category,
                    )

                    if category == "invalid_tool_payload":
                        log_operation(
                            "invalid_tool_payload_detected",
                            model=self.active_model,
                            attempt=attempt,
                            error=str(exc),
                        )
                    elif category == "quota":
                        log_operation(
                            "quota_limit_detected",
                            model=self.active_model,
                            attempt=attempt,
                            error=str(exc),
                        )
                    elif category == "rate_limit":
                        log_operation(
                            "rate_limit_detected",
                            model=self.active_model,
                            attempt=attempt,
                            error=str(exc),
                        )
                    elif category == "token_limit":
                        log_operation(
                            "token_limit_detected",
                            model=self.active_model,
                            attempt=attempt,
                            error=str(exc),
                        )
                    elif category == "provider_unavailable":
                        log_operation(
                            "provider_unavailable_detected",
                            model=self.active_model,
                            attempt=attempt,
                            error=str(exc),
                        )
                    elif category == "auth":
                        log_operation(
                            "provider_auth_detected",
                            model=self.active_model,
                            attempt=attempt,
                            error=str(exc),
                        )

                    if category == "invalid_tool_payload" and payload_retries < self.max_payload_retries:
                        payload_retries += 1
                        log_operation(
                            "tool_call_payload_retry",
                            model=self.active_model,
                            attempt=attempt,
                            retry=payload_retries,
                        )
                        await self.send_stream(
                            "status",
                            "Tool call invalida detectada; aplicando saneamento e retomando sem reiniciar a tarefa.",
                        )
                        prompt_to_run = self._build_payload_recovery_prompt(prompt)
                        continue

                    if category in {"quota", "rate_limit", "provider_unavailable", "token_limit"}:
                        if recoverable_retries >= self.max_recoverable_retries:
                            raise

                        recoverable_retries += 1

                        rotated = await self._try_key_rotation_before_fallback(category, exc)
                        if rotated:
                            prompt_to_run = self._build_provider_recovery_prompt(prompt)
                            continue

                        switched = await self._try_model_fallback(category, exc)
                        if switched:
                            prompt_to_run = self._build_provider_recovery_prompt(prompt)
                            continue

                    raise

            if mode == "plan":
                await self.send_stream("system", "MODO_PLAN_CONCLUIDO")

            self.set_status("idle", None)
            await self.send_stream("status", "Tarefa concluida.")
            log_operation(
                "task_finished",
                mode=mode,
                model=self.active_model,
                attempts=attempt,
            )

        except Exception as exc:
            logger.error(f"Erro na execucao da tarefa: {exc}")
            log_error("task_fatal", exc, model=self.active_model, mode=mode)
            self.set_status("idle", None)
            await self.send_stream("status", f"Erro: {redact_text(str(exc))}")
