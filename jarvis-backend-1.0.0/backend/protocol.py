import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProtocolParser:
    """
    Centraliza o parsing e a geração de mensagens JSON de acordo com o contrato
    definido em AgentContext/02-contrato-json-mark-alfa.md
    """
    
    @staticmethod
    def parse_message(message_str: str) -> Optional[Dict[str, Any]]:
        """Converte a string JSON para dict verificando o contrato básico"""
        try:
            data = json.loads(message_str)
            if not isinstance(data, dict):
                logger.error("A mensagem não é um dicionário JSON válido")
                return None
                
            if "action" not in data:
                logger.error("A mensagem não contém a chave obrigatória 'action'")
                return None
                
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            return None

    @staticmethod
    def build_sync_state(state: Dict[str, Any]) -> str:
        return json.dumps({
            "type": "sync_state",
            "state": state
        })

    @staticmethod
    def build_action_response(action: str, success: bool, data: Any = None, error: str = None) -> str:
        response = {
            "type": "action_response",
            "action": action,
            "success": success
        }
        if data is not None:
            response["data"] = data
        if error is not None:
            response["error"] = error
            
        return json.dumps(response)

    @staticmethod
    def build_stream_message(msg_type: str, content: str) -> str:
        """msg_type pode ser: user, status, message, code, console"""
        return json.dumps({
            "type": "stream",
            "message_type": msg_type,
            "content": content
        })
