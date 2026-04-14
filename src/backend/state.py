from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import BUILTIN_MODELS, DEFAULT_MODEL, dedupe_models, is_allowed_custom_model
from config_manager import load_config, load_session_state, save_session_state


MERGEABLE_HISTORY_TYPES = {"message", "code", "console"}


@dataclass
class BackendState:
    mode: str = "agent"
    model: str = DEFAULT_MODEL
    status: str = "idle"
    active_task: Optional[str] = None
    interpreter_pid: Optional[int] = None
    interpreter_pgid: Optional[int] = None
    custom_models: List[str] = field(default_factory=list)
    session_history: List[Dict[str, str]] = field(default_factory=list)
    history_revision: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "model": self.model,
            "status": self.status,
            "active_task": self.active_task,
            "history_revision": self.history_revision,
        }

    def get_model_catalog(self) -> Dict[str, List[str]]:
        all_models = dedupe_models([*BUILTIN_MODELS, *self.custom_models])
        return {
            "builtin": BUILTIN_MODELS[:],
            "custom": self.custom_models[:],
            "all": all_models,
        }

    def get_history_snapshot(self) -> List[Dict[str, str]]:
        return [dict(item) for item in self.session_history]

    def remember_custom_model(self, model_name: str) -> bool:
        if not is_allowed_custom_model(model_name):
            return False
        if model_name in self.custom_models:
            return False
        self.custom_models.append(model_name)
        self.custom_models = dedupe_models(self.custom_models)
        return True

    def append_history(self, message_type: str, content: str):
        if not content:
            return

        if (
            message_type in MERGEABLE_HISTORY_TYPES
            and self.session_history
            and self.session_history[-1]["message_type"] == message_type
        ):
            self.session_history[-1]["content"] += content
        else:
            self.session_history.append(
                {
                    "message_type": message_type,
                    "content": content,
                }
            )

        self.history_revision += 1
        save_session_state({"history": self.session_history})

    def reset_execution(self):
        self.status = "idle"
        self.active_task = None
        self.interpreter_pid = None
        self.interpreter_pgid = None


initial_cfg = load_config()
session_state = load_session_state()

global_state = BackendState(
    mode=initial_cfg.get("mode", "agent"),
    model=initial_cfg.get("model", DEFAULT_MODEL),
    custom_models=initial_cfg.get("custom_models", []),
    session_history=session_state.get("history", []),
    history_revision=len(session_state.get("history", [])),
)
