import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

class JarvisWSClient:
    """
    Cliente WebSocket para se comunicar com o backend do Jarvis.
    """
    def __init__(self, host="127.0.0.1", port=8765, ui_callback=None):
        self.uri = f"ws://{host}:{port}"
        self.ui_callback = ui_callback
        self.websocket = None
        self.connected = False
        self._task = None

    async def connect(self):
        """Loop infinito de conexão com auto-reconnect."""
        while True:
            try:
                logger.info(f"Tentando conectar a {self.uri}...")
                async with websockets.connect(self.uri) as ws:
                    self.websocket = ws
                    self.connected = True
                    if self.ui_callback:
                        self.ui_callback({"type": "connection_status", "status": "connected"})
                    
                    logger.info("Conectado ao backend!")
                    
                    # Loop de escuta
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            if self.ui_callback:
                                self.ui_callback(data)
                        except json.JSONDecodeError:
                            logger.error("Mensagem inválida recebida")
                            
            except (ConnectionClosed, ConnectionRefusedError, OSError) as e:
                self.connected = False
                self.websocket = None
                if self.ui_callback:
                    self.ui_callback({"type": "connection_status", "status": "disconnected"})
                logger.warning(f"Conexão perdida. Tentando novamente em 3s... {e}")
                await asyncio.sleep(3)

    def start(self, loop):
        """Inicia a task no loop asyncio passado"""
        self._task = loop.create_task(self.connect())

    async def send_action(self, action: str, payload: dict = None):
        """Envia uma ação formatada no contrato JSON para o backend."""
        if not self.connected or not self.websocket:
            logger.error("Tentativa de envio falhou: não conectado")
            return False
            
        data = {
            "action": action,
            "payload": payload or {}
        }
        try:
            await self.websocket.send(json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar {action}: {e}")
            return False
