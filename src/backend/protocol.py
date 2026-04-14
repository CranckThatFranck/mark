import json
import logging
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class ProtocolParser:
    """
    Centraliza o parsing e a geracao de mensagens JSON do contrato do Mark Alfa.
    """

    @staticmethod
    def parse_message(message_str: str) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(message_str)
            if not isinstance(data, dict):
                logger.error("A mensagem nao e um dicionario JSON valido")
                return None

            if "action" not in data:
                logger.error("A mensagem nao contem a chave obrigatoria 'action'")
                return None

            return data
        except json.JSONDecodeError as exc:
            logger.error(f"Erro ao decodificar JSON: {exc}")
            return None

    @staticmethod
    def build_sync_state(state: Dict[str, Any], models=None, history=None) -> str:
        payload = {
            "type": "sync_state",
            "state": state,
        }
        if models is not None:
            payload["models"] = models
        if history is not None:
            payload["history"] = history
        return json.dumps(payload)

    @staticmethod
    def build_action_response(action: str, success: bool, data: Any = None, error: str = None) -> str:
        response = {
            "type": "action_response",
            "action": action,
            "success": success,
        }
        if data is not None:
            response["data"] = data
        if error is not None:
            response["error"] = error

        return json.dumps(response)

    @staticmethod
    def build_stream_message(msg_type: str, content: str) -> str:
        return json.dumps(
            {
                "type": "stream",
                "message_type": msg_type,
                "content": content,
            }
        )
