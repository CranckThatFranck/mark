import asyncio
from contextlib import suppress
import errno
import json
import logging
import os

import websockets
from websockets.exceptions import ConnectionClosed, InvalidHandshake, WebSocketException


logger = logging.getLogger(__name__)


class JarvisWSClient:
    """Cliente WebSocket com reconexao e sinalizacao mais precisa para a UI."""

    def __init__(self, host="127.0.0.1", port=8765, ui_callback=None, reconnect_delay=2.0):
        self.host = os.environ.get("MARK_WS_HOST", host)
        self.port = int(os.environ.get("MARK_WS_PORT", str(port)))
        self.uri = self._build_uri()
        self.ui_callback = ui_callback
        self.reconnect_delay = reconnect_delay
        self.websocket = None
        self.connected = False
        self._task = None
        self._closing = False
        self._had_successful_connection = False

    def _build_uri(self):
        return f"ws://{self.host}:{self.port}"

    def _emit_ui_event(self, payload):
        if self.ui_callback:
            self.ui_callback(payload)

    def _describe_failure(self, exc: Exception) -> str:
        message = str(exc).strip()
        if isinstance(exc, InvalidHandshake):
            return message or "handshake interrompido antes da sessao ficar pronta"
        if isinstance(exc, ConnectionClosed):
            return message or "transporte WebSocket encerrado sem confirmacao completa"
        if isinstance(exc, ConnectionRefusedError):
            return "servico nao aceitou a conexao na porta configurada"
        if isinstance(exc, OSError):
            if getattr(exc, "errno", None) in {errno.ECONNREFUSED, 111, 61, 10061}:
                return "servico indisponivel ou ainda nao pronto para aceitar conexoes"
            return message or "falha de transporte ao falar com o backend"
        return message or exc.__class__.__name__

    def _failure_status(self, exc: Exception) -> str:
        if isinstance(exc, (InvalidHandshake, ConnectionClosed, WebSocketException)):
            return "reconnecting"
        if isinstance(exc, ConnectionRefusedError):
            return "unavailable"
        if isinstance(exc, OSError) and getattr(exc, "errno", None) in {errno.ECONNREFUSED, 111, 61, 10061}:
            return "unavailable"
        if self._had_successful_connection:
            return "reconnecting"
        return "unavailable"

    async def connect(self):
        attempt = 0
        while not self._closing:
            try:
                self.uri = self._build_uri()
                if attempt == 0 and not self._had_successful_connection:
                    self._emit_ui_event(
                        {
                            "type": "connection_status",
                            "status": "connecting",
                            "host": self.host,
                            "port": self.port,
                        }
                    )
                logger.info(f"Tentando conectar a {self.uri}...")
                async with websockets.connect(
                    self.uri,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=3,
                ) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    recovered = self._had_successful_connection
                    self._had_successful_connection = True
                    attempt = 0
                    self._emit_ui_event(
                        {
                            "type": "connection_status",
                            "status": "connected",
                            "recovered": recovered,
                            "host": self.host,
                            "port": self.port,
                        }
                    )

                    async for message in websocket:
                        try:
                            payload = json.loads(message)
                        except json.JSONDecodeError:
                            logger.error("Mensagem JSON invalida recebida")
                            continue
                        self._emit_ui_event(payload)

                if self._closing:
                    break

                self.connected = False
                self.websocket = None
                attempt += 1
                detail = "sessao WebSocket encerrada; iniciando nova tentativa de conexao"
                self._emit_ui_event(
                    {
                        "type": "connection_status",
                        "status": "reconnecting",
                        "detail": detail,
                        "attempt": attempt,
                        "host": self.host,
                        "port": self.port,
                    }
                )
                logger.warning(f"Falha de conexao com o backend (reconnecting): {detail}")
                await asyncio.sleep(self.reconnect_delay)
                continue

            except asyncio.CancelledError:
                raise
            except (ConnectionClosed, InvalidHandshake, WebSocketException, ConnectionRefusedError, OSError) as exc:
                if self._closing:
                    break

                self.connected = False
                self.websocket = None
                attempt += 1
                status = self._failure_status(exc)
                detail = self._describe_failure(exc)
                self._emit_ui_event(
                    {
                        "type": "connection_status",
                        "status": status,
                        "detail": detail,
                        "attempt": attempt,
                        "host": self.host,
                        "port": self.port,
                    }
                )
                logger.warning(f"Falha de conexao com o backend ({status}): {detail}")
                await asyncio.sleep(self.reconnect_delay)
            finally:
                self.connected = False
                self.websocket = None

    def start(self, loop):
        self._task = loop.create_task(self.connect())

    async def close(self):
        self._closing = True
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
        except (ConnectionClosed, OSError) as exc:
            self.connected = False
            self.websocket = None
            self._emit_ui_event(
                {
                    "type": "connection_status",
                    "status": "reconnecting",
                    "detail": self._describe_failure(exc),
                    "host": self.host,
                    "port": self.port,
                }
            )
            logger.warning(f"Erro ao enviar {action}: {exc}")
            return False
