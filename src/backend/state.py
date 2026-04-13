from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from config import DEFAULT_MODEL

@dataclass
class BackendState:
    mode: str = "agent"  # "agent" ou "plan"
    model: str = DEFAULT_MODEL
    status: str = "idle" # "idle", "running", "interrupted"
    active_task: Optional[str] = None
    interpreter_pid: Optional[int] = None
    interpreter_pgid: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "model": self.model,
            "status": self.status,
            "active_task": self.active_task
        }
        
    def reset_execution(self):
        """Reseta o estado de execução para o modo ocioso"""
        self.status = "idle"
        self.active_task = None
        self.interpreter_pid = None
        self.interpreter_pgid = None

# Instância global do estado para ser compartilhada
global_state = BackendState()
