import asyncio
import logging

import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK

from agent_runner import AgentRunner
from config import MODEL_FALLBACK_CHAIN, WS_HOST, WS_PORT, is_supported_model, normalize_model, now_timestamp
from config_manager import save_config
from context_setup import prepare_context_structure
from credentials import CredentialValidationError, GeminiCredentialStore
from logger import build_websocket_server_logger, setup_logger
from observability import log_error, log_operation
from process_manager import ProcessManager
from protocol import ProtocolParser
from state import global_state


setup_logger()
logger = logging.getLogger("MarkServer")


agent_runner = None
credential_store = None
active_connections = set()


def is_benign_disconnect(exc: Exception) -> bool:
    return isinstance(
        exc,
        (
            ConnectionClosed,
            ConnectionClosedOK,
            ConnectionClosedError,
            BrokenPipeError,
            ConnectionResetError,
            OSError,
        ),
    )


async def safe_send(websocket, payload: str, context: str, log_unexpected: bool = True) -> bool:
    try:
        await websocket.send(payload)
        return True
    except Exception as exc:
        active_connections.discard(websocket)
        if is_benign_disconnect(exc):
            logger.info(f"Conexao removida durante {context}: transporte encerrado pelo cliente")
        elif log_unexpected:
            logger.error(f"Falha ao enviar {context}: {exc}")
        return False


def persist_runtime_config():
    save_config(
        {
            "mode": global_state.mode,
            "model": global_state.model,
            "custom_models": global_state.custom_models,
        }
    )


def build_state_payload():
    state_payload = global_state.to_dict()
    state_payload["fallback_chain"] = MODEL_FALLBACK_CHAIN[:]

    if credential_store:
        catalog = credential_store.get_public_catalog()
        active = credential_store.resolve_active_key()
        state_payload["credentials"] = {
            "active_key_id": catalog.get("active_key_id"),
            "active_key_masked": catalog.get("active_key_masked"),
            "total_keys": catalog.get("total_keys", 0),
            "source": active.get("source"),
            "keys": catalog.get("keys", []),
        }
    else:
        state_payload["credentials"] = {
            "active_key_id": None,
            "active_key_masked": "",
            "total_keys": 0,
            "source": "missing",
        }

    return state_payload


def build_config_payload():
    catalog = credential_store.get_public_catalog() if credential_store else {"active_key_id": None, "keys": []}
    active = credential_store.resolve_active_key() if credential_store else {"source": "missing"}
    return {
        "mode": global_state.mode,
        "model": global_state.model,
        "custom_models": global_state.custom_models,
        "models": global_state.get_model_catalog(),
        "fallback_chain": MODEL_FALLBACK_CHAIN[:],
        "credentials": {
            **catalog,
            "source": active.get("source"),
        },
    }


async def on_runtime_state_change(new_model: str, reason: str, details: str):
    global_state.model = new_model
    global_state.remember_custom_model(new_model)
    persist_runtime_config()
    log_operation(
        "frontend_notified_runtime_state_change",
        model=new_model,
        reason=reason,
        details=details,
    )
    await broadcast_state()


def apply_model_selection(raw_model_name: str):
    model_name = normalize_model(raw_model_name)
    if not model_name:
        raise ValueError("Modelo nao enviado")
    if not is_supported_model(model_name):
        raise ValueError("Apenas modelos Gemini com prefixo gemini/ sao suportados")

    global_state.model = model_name
    global_state.remember_custom_model(model_name)


async def send_sync_state(websocket, include_history: bool = False):
    sync_message = ProtocolParser.build_sync_state(
        build_state_payload(),
        models=global_state.get_model_catalog(),
        history=global_state.get_history_snapshot() if include_history else None,
    )
    return await safe_send(websocket, sync_message, "sync_state")


async def broadcast_state():
    if not active_connections:
        return

    stale_connections = []
    for websocket in tuple(active_connections):
        sent = await send_sync_state(websocket)
        if not sent:
            stale_connections.append(websocket)

    for websocket in stale_connections:
        active_connections.discard(websocket)


async def send_stream_cb(msg_type: str, content: str):
    if content is None:
        return
    content = str(content)

    if msg_type == "system" and content == "MODO_PLAN_CONCLUIDO":
        if global_state.mode == "plan":
            global_state.mode = "agent"
            persist_runtime_config()
            asyncio.create_task(broadcast_state())
        return

    timestamp = now_timestamp()
    global_state.append_history(msg_type, content, timestamp=timestamp)

    if not active_connections:
        return

    message = ProtocolParser.build_stream_message(msg_type, content, timestamp=timestamp)
    stale_connections = []
    for websocket in tuple(active_connections):
        sent = await safe_send(websocket, message, f"stream:{msg_type}", log_unexpected=False)
        if not sent:
            stale_connections.append(websocket)

    for websocket in stale_connections:
        active_connections.discard(websocket)


def set_status_cb(status: str, task: str | None):
    global_state.status = status
    global_state.active_task = task
    asyncio.create_task(broadcast_state())


async def handle_action(websocket, data: dict):
    global agent_runner

    action = data.get("action")
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}

    logger.info(f"Acao recebida: {action}")
    log_operation("action_received", action=action)

    if action == "healthcheck":
        response = ProtocolParser.build_action_response(
            "healthcheck",
            True,
            data={"status": "ok", "model": global_state.model},
        )
        await safe_send(websocket, response, action or "action_response")
        return

    if action == "get_status":
        response = ProtocolParser.build_action_response("get_status", True, data=build_state_payload())
        await safe_send(websocket, response, action or "action_response")
        return

    if action == "get_models":
        response = ProtocolParser.build_action_response(
            "get_models",
            True,
            data=global_state.get_model_catalog(),
        )
        await safe_send(websocket, response, action or "action_response")
        return

    if action == "get_config":
        response = ProtocolParser.build_action_response(
            "get_config",
            True,
            data=build_config_payload(),
        )
        await safe_send(websocket, response, action or "action_response")
        return

    if action == "get_api_keys":
        response = ProtocolParser.build_action_response(
            "get_api_keys",
            True,
            data=credential_store.get_public_catalog() if credential_store else {"active_key_id": None, "keys": []},
        )
        await safe_send(websocket, response, action or "action_response")
        return

    if action == "add_api_key":
        try:
            catalog = credential_store.add_key(
                key=payload.get("key"),
                label=payload.get("label"),
                set_active=bool(payload.get("set_active", True)),
            )
            agent_runner.refresh_runtime_api_key(reason="manual_add_api_key")
            await broadcast_state()
            log_operation(
                "api_key_added",
                active_key_id=catalog.get("active_key_id"),
                total_keys=catalog.get("total_keys", 0),
            )
            response = ProtocolParser.build_action_response("add_api_key", True, data=catalog)
        except CredentialValidationError as exc:
            response = ProtocolParser.build_action_response("add_api_key", False, error=str(exc))
        except Exception as exc:
            log_error("api_key_add_failed", exc)
            response = ProtocolParser.build_action_response("add_api_key", False, error="Falha inesperada ao cadastrar chave")

        await safe_send(websocket, response, action or "action_response")
        return

    if action == "update_api_key":
        try:
            key_id = payload.get("id")
            if not key_id:
                raise CredentialValidationError("ID da chave nao enviado")
            catalog = credential_store.update_key(
                key_id=key_id,
                label=payload.get("label"),
                key=payload.get("key"),
                set_active=bool(payload.get("set_active", False)),
            )
            agent_runner.refresh_runtime_api_key(reason="manual_update_api_key")
            await broadcast_state()
            log_operation("api_key_updated", key_id=key_id)
            response = ProtocolParser.build_action_response("update_api_key", True, data=catalog)
        except CredentialValidationError as exc:
            response = ProtocolParser.build_action_response("update_api_key", False, error=str(exc))
        except Exception as exc:
            log_error("api_key_update_failed", exc)
            response = ProtocolParser.build_action_response("update_api_key", False, error="Falha inesperada ao editar chave")

        await safe_send(websocket, response, action or "action_response")
        return

    if action == "delete_api_key":
        try:
            key_id = payload.get("id")
            if not key_id:
                raise CredentialValidationError("ID da chave nao enviado")
            _, catalog = credential_store.delete_key(key_id)
            agent_runner.refresh_runtime_api_key(reason="manual_delete_api_key")
            await broadcast_state()
            log_operation("api_key_deleted", key_id=key_id)
            response = ProtocolParser.build_action_response("delete_api_key", True, data=catalog)
        except CredentialValidationError as exc:
            response = ProtocolParser.build_action_response("delete_api_key", False, error=str(exc))
        except Exception as exc:
            log_error("api_key_delete_failed", exc)
            response = ProtocolParser.build_action_response("delete_api_key", False, error="Falha inesperada ao remover chave")

        await safe_send(websocket, response, action or "action_response")
        return

    if action == "select_api_key":
        try:
            key_id = payload.get("id")
            if not key_id:
                raise CredentialValidationError("ID da chave nao enviado")
            catalog = credential_store.select_key(key_id)
            agent_runner.refresh_runtime_api_key(reason="manual_select_api_key")
            await broadcast_state()
            log_operation("api_key_selected", key_id=key_id)
            response = ProtocolParser.build_action_response("select_api_key", True, data=catalog)
        except CredentialValidationError as exc:
            response = ProtocolParser.build_action_response("select_api_key", False, error=str(exc))
        except Exception as exc:
            log_error("api_key_select_failed", exc)
            response = ProtocolParser.build_action_response("select_api_key", False, error="Falha inesperada ao selecionar chave")

        await safe_send(websocket, response, action or "action_response")
        return

    if action == "rotate_api_key":
        try:
            catalog = credential_store.rotate_key()
            agent_runner.refresh_runtime_api_key(reason="manual_rotate_api_key")
            await broadcast_state()
            log_operation("api_key_rotated_manual", active_key_id=catalog.get("active_key_id"))
            response = ProtocolParser.build_action_response("rotate_api_key", True, data=catalog)
        except CredentialValidationError as exc:
            response = ProtocolParser.build_action_response("rotate_api_key", False, error=str(exc))
        except Exception as exc:
            log_error("api_key_rotate_failed", exc)
            response = ProtocolParser.build_action_response("rotate_api_key", False, error="Falha inesperada na rotacao")

        await safe_send(websocket, response, action or "action_response")
        return

    if action == "update_config":
        new_config = payload.get("config", {})
        try:
            if "mode" in new_config:
                new_mode = new_config.get("mode")
                if new_mode not in {"agent", "plan"}:
                    raise ValueError("Modo invalido")
                global_state.mode = new_mode

            if "model" in new_config:
                apply_model_selection(new_config.get("model"))
                agent_runner.update_model(global_state.model, reason="update_config")

            persist_runtime_config()
            await broadcast_state()
            response = ProtocolParser.build_action_response(
                "update_config",
                True,
                data=build_config_payload(),
            )
            log_operation("config_updated", mode=global_state.mode, model=global_state.model)
        except ValueError as exc:
            response = ProtocolParser.build_action_response("update_config", False, error=str(exc))
        except Exception as exc:
            log_error("config_update_failed", exc)
            response = ProtocolParser.build_action_response("update_config", False, error="Falha inesperada ao atualizar configuracao")
        await safe_send(websocket, response, action or "action_response")
        return

    if action == "change_model":
        try:
            apply_model_selection(payload.get("model"))
            persist_runtime_config()
            agent_runner.update_model(global_state.model, reason="manual")
            await broadcast_state()
            response = ProtocolParser.build_action_response(
                "change_model",
                True,
                data={
                    "model": global_state.model,
                    "models": global_state.get_model_catalog(),
                },
            )
            log_operation("manual_model_switch_success", model=global_state.model)
        except ValueError as exc:
            response = ProtocolParser.build_action_response("change_model", False, error=str(exc))
            log_operation("manual_model_switch_failed", requested_model=payload.get("model"), reason=str(exc))
        except Exception as exc:
            log_error("manual_model_switch_failed_unexpected", exc, requested_model=payload.get("model"))
            response = ProtocolParser.build_action_response("change_model", False, error="Falha inesperada na troca de modelo")
        await safe_send(websocket, response, action or "action_response")
        return

    if action == "change_mode":
        mode = payload.get("mode")
        if mode in {"agent", "plan"}:
            global_state.mode = mode
            persist_runtime_config()
            await broadcast_state()
            response = ProtocolParser.build_action_response("change_mode", True, data={"mode": global_state.mode})
            log_operation("manual_mode_switch", mode=global_state.mode)
        else:
            response = ProtocolParser.build_action_response("change_mode", False, error="Modo invalido")
        await safe_send(websocket, response, action or "action_response")
        return

    if action == "execute_task":
        prompt = payload.get("prompt")
        if not prompt:
            response = ProtocolParser.build_action_response("execute_task", False, error="Prompt vazio")
            await safe_send(websocket, response, action or "action_response")
            return

        if global_state.status == "running":
            response = ProtocolParser.build_action_response(
                "execute_task",
                False,
                error="Uma tarefa ja esta em execucao",
            )
            await safe_send(websocket, response, action or "action_response")
            return

        response = ProtocolParser.build_action_response("execute_task", True)
        await safe_send(websocket, response, action or "action_response")
        log_operation("execute_task_accepted", mode=global_state.mode, model=global_state.model)
        asyncio.create_task(agent_runner.run_task(prompt, global_state.mode))
        return

    if action == "interrupt":
        if global_state.status == "idle":
            response = ProtocolParser.build_action_response(
                "interrupt",
                False,
                error="Nenhuma tarefa em execucao",
            )
            await safe_send(websocket, response, action or "action_response")
            return

        logger.warning("Kill switch acionado")

        if global_state.interpreter_pid:
            ProcessManager.kill_process_tree(global_state.interpreter_pid)
        if global_state.interpreter_pgid:
            ProcessManager.kill_pgid(global_state.interpreter_pgid)

        global_state.reset_execution()
        agent_runner = AgentRunner(
            send_stream_cb,
            set_status_cb,
            runtime_state_cb=on_runtime_state_change,
            credential_store=credential_store,
        )
        agent_runner.update_model(global_state.model, reason="interrupt_rebuild")

        await broadcast_state()
        await send_stream_cb("system", "Tarefa interrompida pelo usuario")
        log_operation("task_interrupted", model=global_state.model)

        response = ProtocolParser.build_action_response("interrupt", True)
        await safe_send(websocket, response, action or "action_response")
        return

    logger.warning(f"Acao desconhecida ou nao implementada: {action}")
    response = ProtocolParser.build_action_response(action, False, error="Acao desconhecida")
    await safe_send(websocket, response, action or "action_response")


async def connection_handler(websocket):
    logger.info(f"Nova conexao WebSocket de {websocket.remote_address}")
    log_operation("frontend_connection_open", remote=str(websocket.remote_address))
    active_connections.add(websocket)

    try:
        sent = await send_sync_state(websocket, include_history=True)
        if not sent:
            return
        async for message in websocket:
            data = ProtocolParser.parse_message(message)
            if data:
                await handle_action(websocket, data)
    except ConnectionClosedOK:
        logger.info(f"Conexao encerrada normalmente: {websocket.remote_address}")
        log_operation("frontend_connection_closed", remote=str(websocket.remote_address), reason="closed_ok")
    except ConnectionClosedError as exc:
        logger.info(f"Conexao interrompida sem queda do backend: {websocket.remote_address} ({exc})")
        log_operation(
            "frontend_connection_reconnect",
            remote=str(websocket.remote_address),
            reason="connection_closed_error",
            details=str(exc),
        )
    except ConnectionClosed:
        logger.info(f"Conexao fechada: {websocket.remote_address}")
        log_operation("frontend_connection_closed", remote=str(websocket.remote_address), reason="connection_closed")
    except Exception as exc:
        logger.error(f"Erro inesperado na conexao: {exc}")
        log_error("frontend_connection_unexpected_error", exc, remote=str(websocket.remote_address))
    finally:
        active_connections.discard(websocket)


async def start_server():
    global agent_runner, credential_store

    prepare_context_structure()
    credential_store = GeminiCredentialStore()
    agent_runner = AgentRunner(
        send_stream_cb,
        set_status_cb,
        runtime_state_cb=on_runtime_state_change,
        credential_store=credential_store,
    )
    agent_runner.update_model(global_state.model, reason="startup_restore")
    log_operation(
        "backend_started",
        host=WS_HOST,
        port=WS_PORT,
        active_model=global_state.model,
        fallback_chain=MODEL_FALLBACK_CHAIN,
    )

    logger.info(f"Iniciando Mark Backend em ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(
        connection_handler,
        WS_HOST,
        WS_PORT,
        logger=build_websocket_server_logger(logger),
    ):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuario")
