import os
import sys
import tempfile
import json
import asyncio
from pathlib import Path


backend_path = Path(__file__).parent.parent / "src" / "backend"
sys.path.append(str(backend_path))


with tempfile.TemporaryDirectory() as temp_dir:
    os.environ["MARK_BASE_DIR"] = temp_dir
    os.environ["MARK_LOG_DIR"] = str(Path(temp_dir) / "logs")

    from config import BACKEND_LOG, ERRORS_LOG, OPERATIONS_LOG, DEFAULT_MODEL, MODEL_FALLBACK_CHAIN
    from config_manager import (
        build_public_credentials_catalog,
        load_credentials_state,
        load_config,
        load_initial_rules,
        load_session_state,
        save_credentials_state,
        save_config,
        save_session_state,
    )
    from credentials import GeminiCredentialStore
    from logger import build_websocket_server_logger, setup_logger
    from observability import log_error, log_operation
    from protocol import ProtocolParser
    from state import BackendState
    from tool_sanitizer import sanitize_completion_payload, sanitize_tool_arguments

    try:
        import agent_runner as agent_runner_module
        from agent_runner import AgentRunner
    except Exception:
        agent_runner_module = None
        AgentRunner = None

    def test_protocol_parser():
        data = ProtocolParser.parse_message('{"action": "healthcheck"}')
        assert data is not None
        assert data["action"] == "healthcheck"
        print("Test Protocol Parser: OK")

    def test_config_sanitization():
        save_config(
            {
                "mode": "plan",
                "model": "vertex_ai/gemini-2.5-flash",
                "custom_models": [
                    "gpt-4o",
                    "gemini/gemini-2.5-flash-exp",
                    "gemini/gemini-2.5-flash-exp",
                ],
            }
        )
        config = load_config()
        assert config["mode"] == "plan"
        assert config["model"] == DEFAULT_MODEL
        assert config["custom_models"] == ["gemini/gemini-2.5-flash-exp"]
        assert MODEL_FALLBACK_CHAIN[0] == DEFAULT_MODEL
        print("Test Config Sanitization: OK")

    def test_credentials_persistence_and_masking():
        save_credentials_state(
            {
                "active_key_id": "main",
                "keys": [
                    {"id": "main", "label": "Principal", "secret": "AIza-PRIMARY-KEY", "created_at": "2026-01-01"},
                    {"id": "backup", "label": "Backup", "secret": "AIza-BACKUP-KEY", "created_at": "2026-01-02"},
                    {"id": "invalid", "label": "Invalida", "secret": ""},
                ],
            }
        )

        credentials = load_credentials_state()
        assert credentials["active_key_id"] == "main"
        assert len(credentials["keys"]) == 2

        public_catalog = build_public_credentials_catalog(credentials)
        assert public_catalog["total_keys"] == 2
        assert all("secret" not in item for item in public_catalog["keys"])
        assert public_catalog["active_key_masked"].startswith("AIza")
        print("Test Credentials Persistence And Masking: OK")

    def test_credentials_manual_rotation():
        store = GeminiCredentialStore()
        store.add_key(key="AIza-MANUAL-1", label="Manual 1", set_active=True)
        store.add_key(key="AIza-MANUAL-2", label="Manual 2", set_active=False)

        initial = store.get_public_catalog()
        rotated = store.rotate_key()
        assert initial["active_key_id"] != rotated["active_key_id"]
        print("Test Credentials Manual Rotation: OK")

    def test_credentials_update_and_select():
        save_credentials_state({"active_key_id": None, "keys": []})
        store = GeminiCredentialStore()
        first_catalog = store.add_key(key="AIza-UPDATE-1", label="Original", set_active=True)
        first_id = first_catalog["active_key_id"]
        second_catalog = store.add_key(key="AIza-UPDATE-2", label="Second", set_active=False)
        second_id = next(item["id"] for item in second_catalog["keys"] if item["id"] != first_id)

        updated_catalog = store.update_key(first_id, label="Atualizada", key="AIza-UPDATE-1B", set_active=False)
        assert any(item["label"] == "Atualizada" for item in updated_catalog["keys"] if item["id"] == first_id)

        selected_catalog = store.select_key(second_id)
        assert selected_catalog["active_key_id"] == second_id
        print("Test Credentials Update And Select: OK")

    def test_tool_call_sanitization_layer():
        execute_payload = sanitize_tool_arguments("print('oi')", "execute")
        assert execute_payload["changed"] is True
        assert json.loads(execute_payload["arguments"]) == {"code": "print('oi')"}

        completion = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "execute",
                                    "arguments": "{'code': 'print(1)'}",
                                }
                            }
                        ]
                    }
                }
            ]
        }
        updates = sanitize_completion_payload(completion)
        assert len(updates) == 1
        sanitized_arguments = completion["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
        assert json.loads(sanitized_arguments) == {"code": "print(1)"}
        print("Test Tool Call Sanitization Layer: OK")

    def test_observability_files_receive_events():
        setup_logger()
        log_operation("smoke_operation_event", detail="ok")
        log_error("smoke_error_event", error="boom key=AIza-SECRET-1234567890")

        assert BACKEND_LOG.exists()
        assert OPERATIONS_LOG.exists()
        assert ERRORS_LOG.exists()

        operations_content = OPERATIONS_LOG.read_text(encoding="utf-8")
        errors_content = ERRORS_LOG.read_text(encoding="utf-8")

        assert "smoke_operation_event" in operations_content
        assert "smoke_error_event" in errors_content
        assert "AIza-SECRET-1234567890" not in errors_content
        print("Test Observability Files Receive Events: OK")

    class FakeLLM:
        def __init__(self):
            self.model = ""

    class ScriptedInterpreter:
        def __init__(self, scripts):
            self.auto_run = False
            self.custom_instructions = ""
            self.llm = FakeLLM()
            self._scripts = {name: list(steps) for name, steps in scripts.items()}

        def chat(self, _prompt, stream=True, display=False):
            del stream, display
            model = self.llm.model
            model_steps = self._scripts.setdefault(model, [])
            if model_steps:
                step_type, payload = model_steps.pop(0)
            else:
                step_type, payload = "yield", [{"type": "message", "content": "ok"}]

            if step_type == "error":
                raise RuntimeError(payload)

            for chunk in payload:
                yield chunk

    def test_runner_recovers_invalid_tool_payload_without_fallback():
        if AgentRunner is None or agent_runner_module is None:
            print("Test Runner Recover Invalid Tool Payload: SKIPPED (agent_runner indisponivel)")
            return

        save_credentials_state({"active_key_id": None, "keys": []})
        store = GeminiCredentialStore()
        store.add_key(key="AIza-RECOVERY-KEY", label="Recovery", set_active=True)

        first_model = MODEL_FALLBACK_CHAIN[0]
        fake_interpreter = ScriptedInterpreter(
            {
                first_model: [
                    ("error", "JSONDecodeError: function.arguments invalid"),
                    ("yield", [{"type": "message", "content": "retomado apos saneamento"}]),
                ]
            }
        )

        emitted = []
        statuses = []

        async def send_stream(msg_type, content):
            emitted.append((msg_type, str(content)))

        def set_status(status, task):
            statuses.append((status, task))

        original_interpreter = agent_runner_module.interpreter
        agent_runner_module.interpreter = fake_interpreter
        try:
            runner = AgentRunner(send_stream, set_status, credential_store=store)
            asyncio.run(runner.run_task("Teste de saneamento", "agent"))
        finally:
            agent_runner_module.interpreter = original_interpreter

        assert any("Tool call invalida detectada" in text for kind, text in emitted if kind == "status")
        assert statuses and statuses[-1][0] == "idle"
        print("Test Runner Recovers Invalid Tool Payload Without Fallback: OK")

    def test_runner_classifies_auth_errors_without_confusing_tool_payload():
        if AgentRunner is None:
            print("Test Runner Auth Classification: SKIPPED (agent_runner indisponivel)")
            return

        category = AgentRunner.classify_error(RuntimeError("AuthenticationError: API key not valid"))
        assert category == "auth"
        print("Test Runner Classifies Auth Errors Without Confusing Tool Payload: OK")

    def test_runner_fallback_chain_on_quota_error():
        if AgentRunner is None or agent_runner_module is None:
            print("Test Runner Fallback Chain: SKIPPED (agent_runner indisponivel)")
            return

        save_credentials_state({"active_key_id": None, "keys": []})
        store = GeminiCredentialStore()
        store.add_key(key="AIza-FALLBACK-KEY", label="Fallback", set_active=True)

        first_model = MODEL_FALLBACK_CHAIN[0]
        second_model = MODEL_FALLBACK_CHAIN[1]
        fake_interpreter = ScriptedInterpreter(
            {
                first_model: [
                    ("error", "insufficient_quota: daily limit reached"),
                ],
                second_model: [
                    ("yield", [{"type": "message", "content": "executado no modelo de fallback"}]),
                ],
            }
        )

        emitted = []

        async def send_stream(msg_type, content):
            emitted.append((msg_type, str(content)))

        async def on_model_change(model, reason, details):
            emitted.append(("model_change", f"{model}|{reason}|{details}"))

        def set_status(_status, _task):
            return None

        original_interpreter = agent_runner_module.interpreter
        agent_runner_module.interpreter = fake_interpreter
        try:
            runner = AgentRunner(send_stream, set_status, model_change_cb=on_model_change, credential_store=store)
            asyncio.run(runner.run_task("Teste de fallback", "agent"))
            assert runner.active_model == second_model
        finally:
            agent_runner_module.interpreter = original_interpreter

        assert any("Fallback automatico de modelo ativado" in text for kind, text in emitted if kind == "system")
        assert any(kind == "model_change" for kind, _ in emitted)
        print("Test Runner Fallback Chain On Quota Error: OK")

    def test_runner_rotates_key_before_model_fallback_on_quota():
        if AgentRunner is None or agent_runner_module is None:
            print("Test Runner Rotate Key Before Fallback: SKIPPED (agent_runner indisponivel)")
            return

        save_credentials_state({"active_key_id": None, "keys": []})
        store = GeminiCredentialStore()
        first_catalog = store.add_key(key="AIza-ROTATE-1", label="Rotate 1", set_active=True)
        first_key_id = first_catalog["active_key_id"]
        store.add_key(key="AIza-ROTATE-2", label="Rotate 2", set_active=False)

        first_model = MODEL_FALLBACK_CHAIN[0]
        fake_interpreter = ScriptedInterpreter(
            {
                first_model: [
                    ("error", "insufficient_quota: daily limit reached"),
                    ("yield", [{"type": "message", "content": "executado apos rotacao de chave"}]),
                ],
            }
        )

        emitted = []

        async def send_stream(msg_type, content):
            emitted.append((msg_type, str(content)))

        async def on_runtime_state_change(model, reason, details):
            emitted.append(("runtime_state", f"{model}|{reason}|{details}"))

        def set_status(_status, _task):
            return None

        original_interpreter = agent_runner_module.interpreter
        agent_runner_module.interpreter = fake_interpreter
        try:
            runner = AgentRunner(
                send_stream,
                set_status,
                runtime_state_cb=on_runtime_state_change,
                credential_store=store,
            )
            asyncio.run(runner.run_task("Teste de rotacao automatica", "agent"))
        finally:
            agent_runner_module.interpreter = original_interpreter

        rotated_catalog = store.get_public_catalog()
        assert rotated_catalog["active_key_id"] != first_key_id
        assert any("Rotacao automatica de API key Gemini aplicada" in text for kind, text in emitted if kind == "system")
        assert any("api_key_rotation:quota" in text for kind, text in emitted if kind == "runtime_state")
        assert not any("Fallback automatico de modelo ativado" in text for kind, text in emitted if kind == "system")
        print("Test Runner Rotates Key Before Model Fallback On Quota: OK")

    def test_runner_redacts_secret_in_fatal_status_stream():
        if AgentRunner is None or agent_runner_module is None:
            print("Test Runner Redacts Secret In Fatal Status Stream: SKIPPED (agent_runner indisponivel)")
            return

        save_credentials_state({"active_key_id": None, "keys": []})
        store = GeminiCredentialStore()
        store.add_key(key="AIza-STREAM-1", label="Fatal", set_active=True)

        first_model = MODEL_FALLBACK_CHAIN[0]
        secret = "AIza-LEAK-1234567890"
        fake_interpreter = ScriptedInterpreter(
            {
                first_model: [
                    ("error", f"AuthenticationError: request failed key={secret}"),
                ],
            }
        )

        emitted = []

        async def send_stream(msg_type, content):
            emitted.append((msg_type, str(content)))

        def set_status(_status, _task):
            return None

        original_interpreter = agent_runner_module.interpreter
        agent_runner_module.interpreter = fake_interpreter
        try:
            runner = AgentRunner(send_stream, set_status, credential_store=store)
            asyncio.run(runner.run_task("Teste fatal com segredo", "agent"))
        finally:
            agent_runner_module.interpreter = original_interpreter

        status_messages = [text for kind, text in emitted if kind == "status" and text.startswith("Erro:")]
        assert status_messages
        assert all(secret not in text for text in status_messages)
        print("Test Runner Redacts Secret In Fatal Status Stream: OK")

    def test_session_history_merge():
        state = BackendState()
        state.append_history("message", "Ola")
        state.append_history("message", " mundo")
        state.append_history("code", "print('ok')")
        session_state = load_session_state()

        assert len(session_state["history"]) == 2
        assert session_state["history"][0]["content"] == "Ola mundo"
        assert session_state["history"][1]["message_type"] == "code"
        assert "timestamp" in session_state["history"][0]
        print("Test Session History Merge: OK")

    def test_session_persistence():
        save_session_state(
            {
                "history": [
                    {"message_type": "user", "content": "Oi"},
                    {"message_type": "message", "content": "Tudo bem"},
                ]
            }
        )
        session_state = load_session_state()
        assert len(session_state["history"]) == 2
        assert all(item.get("timestamp") for item in session_state["history"])
        print("Test Session Persistence: OK")

    def test_state_paths_and_rules_file():
        state = BackendState()
        payload = state.to_dict()
        assert payload["paths"]["rules_file"].endswith("product_config/initial_rules.txt")
        assert load_initial_rules()
        print("Test State Paths And Rules File: OK")

    def test_websocket_logger_demotes_benign_errors():
        recorded = []

        class FakeLogger:
            def getChild(self, _name):
                return self

            def info(self, message, *args, **kwargs):
                recorded.append(("info", message))

            def error(self, message, *args, **kwargs):
                recorded.append(("error", message))

        websocket_logger = build_websocket_server_logger(FakeLogger())
        websocket_logger.error("opening handshake failed", exc_info=(BrokenPipeError, BrokenPipeError("bye"), None))
        websocket_logger.error("connection handler failed", exc_info=(RuntimeError, RuntimeError("boom"), None))

        assert recorded[0][0] == "info"
        assert recorded[1][0] == "error"
        print("Test WebSocket Logger Demotes Benign Errors: OK")

    if __name__ == "__main__":
        test_protocol_parser()
        test_config_sanitization()
        test_credentials_persistence_and_masking()
        test_credentials_manual_rotation()
        test_credentials_update_and_select()
        test_tool_call_sanitization_layer()
        test_observability_files_receive_events()
        test_runner_recovers_invalid_tool_payload_without_fallback()
        test_runner_classifies_auth_errors_without_confusing_tool_payload()
        test_runner_fallback_chain_on_quota_error()
        test_runner_rotates_key_before_model_fallback_on_quota()
        test_runner_redacts_secret_in_fatal_status_stream()
        test_session_history_merge()
        test_session_persistence()
        test_state_paths_and_rules_file()
        test_websocket_logger_demotes_benign_errors()
