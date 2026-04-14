import os
import sys
import tempfile
from pathlib import Path


backend_path = Path(__file__).parent.parent / "src" / "backend"
sys.path.append(str(backend_path))


with tempfile.TemporaryDirectory() as temp_dir:
    os.environ["MARK_BASE_DIR"] = temp_dir

    from config import DEFAULT_MODEL
    from config_manager import (
        load_config,
        load_session_state,
        save_config,
        save_session_state,
    )
    from protocol import ProtocolParser
    from state import BackendState

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
        print("Test Config Sanitization: OK")

    def test_session_history_merge():
        state = BackendState()
        state.append_history("message", "Ola")
        state.append_history("message", " mundo")
        state.append_history("code", "print('ok')")
        session_state = load_session_state()

        assert len(session_state["history"]) == 2
        assert session_state["history"][0]["content"] == "Ola mundo"
        assert session_state["history"][1]["message_type"] == "code"
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
        print("Test Session Persistence: OK")

    if __name__ == "__main__":
        test_protocol_parser()
        test_config_sanitization()
        test_session_history_merge()
        test_session_persistence()
