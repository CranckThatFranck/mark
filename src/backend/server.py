import asyncio
import logging

import websockets

from agent_runner import AgentRunner
from config import WS_HOST, WS_PORT, is_supported_model, normalize_model
from config_manager import save_config
from context_setup import prepare_context_structure
from logger import setup_logger
from process_manager import ProcessManager
from protocol import ProtocolParser
from state import global_state


setup_logger()
logger = logging.getLogger("MarkServer")


agent_runner = None
active_connections = set()


def persist_runtime_config():
    save_config(
        {
            "mode": global_state.mode,
            "model": global_state.model,
            "custom_models": global_state.custom_models,
        }
    )


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
        global_state.to_dict(),
        models=global_state.get_model_catalog(),
        history=global_state.get_history_snapshot() if include_history else None,
    )
    await websocket.send(sync_message)


async def broadcast_state():
    if not active_connections:
        return

    stale_connections = []
    for websocket in active_connections:
        try:
            await send_sync_state(websocket)
        except Exception as exc:
            logger.error(f"Erro ao enviar sync_state: {exc}")
            stale_connections.append(websocket)

    for websocket in stale_connections:
        active_connections.discard(websocket)


async def send_stream_cb(msg_type: str, content: str):
    if msg_type == "system" and content == "MODO_PLAN_CONCLUIDO":
        if global_state.mode == "plan":
            global_state.mode = "agent"
            persist_runtime_config()
            asyncio.create_task(broadcast_state())
        return

    global_state.append_history(msg_type, content)

    if not active_connections:
        return

    message = ProtocolParser.build_stream_message(msg_type, content)
    stale_connections = []
    for websocket in active_connections:
        try:
            await websocket.send(message)
        except Exception:
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

    logger.info(f"Acao recebida: {action}")

    if action == "healthcheck":
        response = ProtocolParser.build_action_response(
            "healthcheck",
            True,
            data={"status": "ok", "model": global_state.model},
        )
        await websocket.send(response)
        return

    if action == "get_status":
        response = ProtocolParser.build_action_response("get_status", True, data=global_state.to_dict())
        await websocket.send(response)
        return

    if action == "get_models":
        response = ProtocolParser.build_action_response(
            "get_models",
            True,
            data=global_state.get_model_catalog(),
        )
        await websocket.send(response)
        return

    if action == "get_config":
        response = ProtocolParser.build_action_response(
            "get_config",
            True,
            data={
                "mode": global_state.mode,
                "model": global_state.model,
                "custom_models": global_state.custom_models,
            },
        )
        await websocket.send(response)
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
                agent_runner.update_model(global_state.model)

            persist_runtime_config()
            await broadcast_state()
            response = ProtocolParser.build_action_response(
                "update_config",
                True,
                data={
                    "model": global_state.model,
                    "mode": global_state.mode,
                    "models": global_state.get_model_catalog(),
                },
            )
        except ValueError as exc:
            response = ProtocolParser.build_action_response("update_config", False, error=str(exc))
        await websocket.send(response)
        return

    if action == "change_model":
        try:
            apply_model_selection(payload.get("model"))
            persist_runtime_config()
            agent_runner.update_model(global_state.model)
            await broadcast_state()
            response = ProtocolParser.build_action_response(
                "change_model",
                True,
                data={
                    "model": global_state.model,
                    "models": global_state.get_model_catalog(),
                },
            )
        except ValueError as exc:
            response = ProtocolParser.build_action_response("change_model", False, error=str(exc))
        await websocket.send(response)
        return

    if action == "change_mode":
        mode = payload.get("mode")
        if mode in {"agent", "plan"}:
            global_state.mode = mode
            persist_runtime_config()
            await broadcast_state()
            response = ProtocolParser.build_action_response("change_mode", True, data={"mode": global_state.mode})
        else:
            response = ProtocolParser.build_action_response("change_mode", False, error="Modo invalido")
        await websocket.send(response)
        return

    if action == "execute_task":
        prompt = payload.get("prompt")
        if not prompt:
            response = ProtocolParser.build_action_response("execute_task", False, error="Prompt vazio")
            await websocket.send(response)
            return

        if global_state.status == "running":
            response = ProtocolParser.build_action_response(
                "execute_task",
                False,
                error="Uma tarefa ja esta em execucao",
            )
            await websocket.send(response)
            return

        response = ProtocolParser.build_action_response("execute_task", True)
        await websocket.send(response)
        asyncio.create_task(agent_runner.run_task(prompt, global_state.mode))
        return

    if action == "interrupt":
        if global_state.status == "idle":
            response = ProtocolParser.build_action_response(
                "interrupt",
                False,
                error="Nenhuma tarefa em execucao",
            )
            await websocket.send(response)
            return

        logger.warning("Kill switch acionado")

        if global_state.interpreter_pid:
            ProcessManager.kill_process_tree(global_state.interpreter_pid)
        if global_state.interpreter_pgid:
            ProcessManager.kill_pgid(global_state.interpreter_pgid)

        global_state.reset_execution()
        agent_runner = AgentRunner(send_stream_cb, set_status_cb)
        agent_runner.update_model(global_state.model)

        await broadcast_state()
        await send_stream_cb("system", "Tarefa interrompida pelo usuario")

        response = ProtocolParser.build_action_response("interrupt", True)
        await websocket.send(response)
        return

    logger.warning(f"Acao desconhecida ou nao implementada: {action}")
    response = ProtocolParser.build_action_response(action, False, error="Acao desconhecida")
    await websocket.send(response)


async def connection_handler(websocket):
    logger.info(f"Nova conexao WebSocket de {websocket.remote_address}")
    active_connections.add(websocket)

    try:
        await send_sync_state(websocket, include_history=True)
        async for message in websocket:
            data = ProtocolParser.parse_message(message)
            if data:
                await handle_action(websocket, data)
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Conexao fechada: {websocket.remote_address}")
    except Exception as exc:
        logger.error(f"Erro inesperado na conexao: {exc}")
    finally:
        active_connections.discard(websocket)


async def start_server():
    global agent_runner

    prepare_context_structure()
    agent_runner = AgentRunner(send_stream_cb, set_status_cb)
    agent_runner.update_model(global_state.model)

    logger.info(f"Iniciando Mark Backend em ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(connection_handler, WS_HOST, WS_PORT):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuario")
