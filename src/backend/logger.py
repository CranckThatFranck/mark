import logging
import sys

from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK

from config import BACKEND_LOG, ERRORS_LOG, OPERATIONS_LOG
from observability import redact_text


def _exc_from_logging_payload(exc_info):
    if exc_info is True:
        return sys.exc_info()[1]
    if isinstance(exc_info, BaseException):
        return exc_info
    if isinstance(exc_info, tuple) and len(exc_info) == 3:
        return exc_info[1]
    return None


def _is_benign_websocket_exception(exc):
    current = exc
    while current is not None:
        if isinstance(
            current,
            (
                ConnectionClosed,
                ConnectionClosedOK,
                ConnectionClosedError,
                BrokenPipeError,
                ConnectionResetError,
                EOFError,
            ),
        ):
            return True
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)
    return False


class WebSocketServerLogger:
    def __init__(self, base_logger: logging.Logger):
        self._logger = base_logger

    def error(self, msg, *args, **kwargs):
        exc = _exc_from_logging_payload(kwargs.get("exc_info"))
        if msg == "opening handshake failed":
            self._logger.info("opening handshake failed: conexao abortada antes da sessao WebSocket ficar pronta")
            return
        if msg == "connection handler failed" and _is_benign_websocket_exception(exc):
            self._logger.info(f"{msg}: conexao encerrada pelo cliente durante transporte/handshake")
            return
        self._logger.error(msg, *args, **kwargs)

    def getChild(self, suffix):
        return WebSocketServerLogger(self._logger.getChild(suffix))

    def __getattr__(self, item):
        return getattr(self._logger, item)


class BenignWebSocketRecordFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if message == "opening handshake failed":
            return False
        if message == "connection handler failed" and _is_benign_websocket_exception(
            _exc_from_logging_payload(record.exc_info)
        ):
            return False
        return True


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        return redact_text(rendered)


def setup_logger():
    """Configura o logger com persistencia em arquivo e stdout."""
    BACKEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    OPERATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    ERRORS_LOG.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    formatter = RedactingFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    websocket_filter = BenignWebSocketRecordFilter()

    file_handler = logging.FileHandler(BACKEND_LOG)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(websocket_filter)

    error_handler = logging.FileHandler(ERRORS_LOG)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(websocket_filter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(websocket_filter)

    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    operations_logger = logging.getLogger("MarkOperations")
    operations_logger.setLevel(logging.INFO)
    operations_logger.propagate = False
    if operations_logger.handlers:
        operations_logger.handlers.clear()
    operations_handler = logging.FileHandler(OPERATIONS_LOG)
    operations_handler.setLevel(logging.INFO)
    operations_handler.setFormatter(RedactingFormatter("%(message)s"))
    operations_logger.addHandler(operations_handler)

    structured_errors_logger = logging.getLogger("MarkErrors")
    structured_errors_logger.setLevel(logging.ERROR)
    structured_errors_logger.propagate = False
    if structured_errors_logger.handlers:
        structured_errors_logger.handlers.clear()
    structured_errors_handler = logging.FileHandler(ERRORS_LOG)
    structured_errors_handler.setLevel(logging.ERROR)
    structured_errors_handler.setFormatter(RedactingFormatter("%(message)s"))
    structured_errors_logger.addHandler(structured_errors_handler)

    return logger


def build_websocket_server_logger(base_logger: logging.Logger) -> WebSocketServerLogger:
    return WebSocketServerLogger(base_logger.getChild("websocket"))


backend_logger = setup_logger()
