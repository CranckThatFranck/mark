import asyncio
import websockets
import logging
import json
from config import WS_HOST, WS_PORT, SUPPORTED_MODELS
from state import global_state
from protocol import ProtocolParser
from agent_runner import AgentRunner
from process_manager import ProcessManager
import asyncio
from context_setup import prepare_context_structure

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("JarvisServer")


# Runner global instanciado
agent_runner = None


async def send_stream_cb(msg_type: str, content: str):
    if msg_type == "system" and content == "MODO_PLAN_CONCLUIDO":
        # Retorno automático
        if global_state.mode == "plan":
            global_state.mode = "agent"
            from config_manager import save_config
            save_config({"mode": global_state.mode, "model": global_state.model})
            asyncio.create_task(broadcast_state())
        return

    if not active_connections: return
    msg = ProtocolParser.build_stream_message(msg_type, content)

    for ws in active_connections:
        try:
            await ws.send(msg)
        except:
            pass

def set_status_cb(status: str, task: str):
    global_state.status = status
    global_state.active_task = task
    asyncio.create_task(broadcast_state())

# Conjunto global de conexões WebSocket ativas (frontend e master)
active_connections = set()

async def broadcast_state():
    """Envia o estado atualizado para todos os clientes conectados."""
    if not active_connections:
        return
        
    state_msg = ProtocolParser.build_sync_state(global_state.to_dict())
    for ws in active_connections:
        try:
            await ws.send(state_msg)
        except Exception as e:
            logger.error(f"Erro ao enviar sync_state: {e}")

async def handle_action(ws, data: dict):
    """Roteador principal de ações."""
    global agent_runner
    action = data.get("action")
    payload = data.get("payload", {})
    
    logger.info(f"Ação recebida: {action}")
    
    if action == "healthcheck":
        resp = ProtocolParser.build_action_response("healthcheck", True, data={"status": "ok"})
        await ws.send(resp)
        
    elif action == "get_status":
        resp = ProtocolParser.build_action_response("get_status", True, data=global_state.to_dict())
        await ws.send(resp)
        
    elif action == "get_models":
        resp = ProtocolParser.build_action_response("get_models", True, data={"models": SUPPORTED_MODELS})
        await ws.send(resp)
        
    elif action == "get_config":
        # Retorna config atual (no futuro, pode ler de um json de config persistido)
        resp = ProtocolParser.build_action_response("get_config", True, data={
            "mode": global_state.mode,
            "model": global_state.model
        })
        await ws.send(resp)
        

    elif action == "update_config":
        new_config = payload.get("config", {})
        if "model" in new_config and new_config["model"] in SUPPORTED_MODELS:
            global_state.model = new_config["model"]
        if "mode" in new_config and new_config["mode"] in ["agent", "plan"]:
            global_state.mode = new_config["mode"]
            
        from config_manager import save_config
        save_config({"mode": global_state.mode, "model": global_state.model})
        
        await broadcast_state()
        resp = ProtocolParser.build_action_response("update_config", True)
        await ws.send(resp)
        
    elif action == "change_model":
        model = payload.get("model")
        if model in SUPPORTED_MODELS:
            global_state.model = model
            from config_manager import save_config
            save_config({"mode": global_state.mode, "model": global_state.model})
            await broadcast_state()
            resp = ProtocolParser.build_action_response("change_model", True)
        else:
            resp = ProtocolParser.build_action_response("change_model", False, error="Modelo não suportado")
        await ws.send(resp)
        
    elif action == "change_mode":
        mode = payload.get("mode")
        if mode in ["agent", "plan"]:
            global_state.mode = mode
            from config_manager import save_config
            save_config({"mode": global_state.mode, "model": global_state.model})
            await broadcast_state()
            resp = ProtocolParser.build_action_response("change_mode", True)
        else:
            resp = ProtocolParser.build_action_response("change_mode", False, error="Modo inválido")
        await ws.send(resp)


    elif action == "execute_task":
        prompt = payload.get("prompt")
        if not prompt:
            resp = ProtocolParser.build_action_response("execute_task", False, error="Prompt vazio")
            await ws.send(resp)
            return
            
        if global_state.status == "running":
            resp = ProtocolParser.build_action_response("execute_task", False, error="Uma tarefa já está em execução")
            await ws.send(resp)
            return
            
        # Responde confirmando que começou
        resp = ProtocolParser.build_action_response("execute_task", True)
        await ws.send(resp)
        
        # Dispara execução assíncrona
        asyncio.create_task(agent_runner.run_task(prompt, global_state.mode))


    elif action == "interrupt":
        if global_state.status == "idle":
            resp = ProtocolParser.build_action_response("interrupt", False, error="Nenhuma tarefa em execução")
            await ws.send(resp)
            return
            
        logger.warning("KILL SWITCH ACIONADO!")
        
        # O Open Interpreter assíncrono interno roda na mesma thread python em um wrapper generator
        # Se tivéssemos um subprocesso, usaríamos ProcessManager aqui.
        # Como o OI não expõe o PID interno facilmente via python API simples (sem subprocess real)
        # Vamos parar o fluxo de controle e sinalizar a recuperação:
        
        # Simula o kill (na integração avançada isso matará o subprocesso)
        if global_state.interpreter_pid:
            ProcessManager.kill_process_tree(global_state.interpreter_pid)
            
        if global_state.interpreter_pgid:
            ProcessManager.kill_pgid(global_state.interpreter_pgid)
            
        # Força o reset de estado
        global_state.reset_execution()
        
        # Reinicia o Runner para garantir estado limpo (Recuperação Segura Pós-Interrupção)
        agent_runner = AgentRunner(send_stream_cb, set_status_cb)
        agent_runner.update_model(global_state.model)
        
        # Envia broadcast a todos e responde confirmando a interrupção
        await broadcast_state()
        await send_stream_cb("system", "TAREFA INTERROMPIDA PELO USUÁRIO")
        
        resp = ProtocolParser.build_action_response("interrupt", True)
        await ws.send(resp)

    # Mais acoes serao implementadas conforme a TODOList...
    else:
        logger.warning(f"Ação desconhecida ou não implementada: {action}")
        resp = ProtocolParser.build_action_response(action, False, error="Ação desconhecida")
        await ws.send(resp)

async def connection_handler(websocket): # removed 'path' as it's deprecated in websockets
    """Gerencia o ciclo de vida de uma conexão WebSocket."""
    logger.info(f"Nova conexão WebSocket de {websocket.remote_address}")
    active_connections.add(websocket)
    
    try:
        # 1. Envia sync_state imediato
        state_msg = ProtocolParser.build_sync_state(global_state.to_dict())
        await websocket.send(state_msg)
        
        # 2. Loop de escuta
        async for message in websocket:
            data = ProtocolParser.parse_message(message)
            if data:
                await handle_action(websocket, data)
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Conexão fechada: {websocket.remote_address}")
    except Exception as e:
        logger.error(f"Erro inesperado na conexão: {e}")
    finally:
        active_connections.remove(websocket)

async def start_server():
    """Inicializa o servidor backend."""
    prepare_context_structure()

    global agent_runner
    agent_runner = AgentRunner(send_stream_cb, set_status_cb)
    agent_runner.update_model(global_state.model)
    
    logger.info(f"Iniciando Jarvis Backend em ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(connection_handler, WS_HOST, WS_PORT):
        await asyncio.Future()  # Roda indefinidamente

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
