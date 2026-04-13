import sys
import asyncio
from pathlib import Path

# Injeta src/backend no path para teste
backend_path = Path(__file__).parent.parent / "src" / "backend"
sys.path.append(str(backend_path))

from protocol import ProtocolParser
from state import BackendState

def test_protocol_parser():
    data = ProtocolParser.parse_message('{"action": "healthcheck"}')
    assert data is not None
    assert data["action"] == "healthcheck"
    print("Test Protocol Parser: OK")

def test_backend_state():
    state = BackendState()
    assert state.mode == "agent"
    assert state.status == "idle"
    state.reset_execution()
    assert state.status == "idle"
    print("Test Backend State: OK")

if __name__ == "__main__":
    test_protocol_parser()
    test_backend_state()
