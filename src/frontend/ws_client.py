import asyncio
from contextlib import suppress
import json
import logging
import os

import websockets
from websockets.exceptions import ConnectionClosed


logger = logging.getLogger(__name__)


class JarvisWSClient:
    """Cliente WebSocket com auto-reconnect para o frontend do Mark."""

    def __init__(self, host="127.0.0.1", port=8765, ui_callback=None):
        resolved_host = os.environ.get("MARK_WS_HOST", host)
        resolved_port = int(os.environ.get("MARK_WS_PORT", str(port)))

        self.uri = f"ws://{resolved_host}:{resolved_port}"
        self.ui_callback = ui_callback
        self.websocket = None
        self.connected = False
        self._task = None

    async def connect(self):
        while True:
            try:
                logger.info(f"Tentando conectar a {self.uri}...")
                async with websockets.connect(self.uri) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    if self.ui_callback:
                        self.ui_callback({"type": "connection_status", "status": "connected"})

                    async for message in websocket:
                        try:
                            payload = json.loads(message)
                            if self.ui_callback:
                                self.ui_callback(payload)
                        except json.JSONDecodeError:
                            logger.error("Mensagem JSON invalida recebida")

            except asyncio.CancelledError:
                raise
            except (ConnectionClosed, ConnectionRefusedError, OSError) as exc:
                self.connected = False
                self.websocket = None
                if self.ui_callback:
                    self.ui_callback({"type": "connection_status", "status": "disconnected"})
                logger.warning(f"Conexao perdida. Tentando novamente em 3s... {exc}")
                await asyncio.sleep(3)

    def start(self, loop):
        self._task = loop.create_task(self.connect())

    async def close(self):
        if self.websocket:
            await self.websocket.close()
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def send_action(self, action: str, payload: dict = None):
        if not self.connected or not self.websocket:
            logger.error("Tentativa de envio falhou: nao conectado")
            return False

        envelope = {
            "action": action,
            "payload": payload or {},
        }
        try:
            await self.websocket.send(json.dumps(envelope))
            return True
        except Exception as exc:
            logger.error(f"Erro ao enviar {action}: {exc}")
            return False
