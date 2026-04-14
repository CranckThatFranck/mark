import asyncio
import json
import os
import socket
import uuid
from pathlib import Path

import websockets


EXPECTED_BUILTIN_MODELS = [
    "gemini/gemini-3.1-pro-preview-customtools",
    "gemini/gemini-3.1-pro-preview",
    "gemini/gemini-2.5-pro",
    "gemini/gemini-3-flash-preview",
    "gemini/gemini-2.5-flash",
]
CUSTOM_MODEL = "gemini/gemini-2.5-flash-exp"
EXECUTION_MODEL = "gemini/gemini-2.5-flash"
PROMPT = "Responda apenas com a palavra teste."
REQUIRE_LIVE_MODEL = os.environ.get("MARK_SMOKE_REQUIRE_LIVE_MODEL", "0") == "1"
RUN_ID = uuid.uuid4().hex[:8]
KEY_LABEL_1 = f"Smoke 1 {RUN_ID}"
KEY_LABEL_1_EDITED = f"Smoke 1 editada {RUN_ID}"
KEY_LABEL_2 = f"Smoke 2 {RUN_ID}"
KEY_SECRET_1 = f"AIza-SMOKE-{RUN_ID}-1"
KEY_SECRET_1_EDITED = f"AIza-SMOKE-{RUN_ID}-1-EDIT"
KEY_SECRET_2 = f"AIza-SMOKE-{RUN_ID}-2"


async def recv_json(websocket, timeout=5.0):
    raw = await asyncio.wait_for(websocket.recv(), timeout=timeout)
    return json.loads(raw)


async def recv_until_action(websocket, action, timeout=8.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError(f"Tempo esgotado aguardando action_response de {action}")

        message = await recv_json(websocket, timeout=remaining)
        if message.get("type") == "action_response" and message.get("action") == action:
            return message


async def smoke_test():
    host = os.environ.get("MARK_WS_HOST", "127.0.0.1")
    port = os.environ.get("MARK_WS_PORT", "8765")
    uri = f"ws://{host}:{port}"
    print(f"Tentando conectar ao backend em {uri}...")

    websocket = None
    for attempt in range(10):
        try:
            websocket = await websockets.connect(uri)
            break
        except ConnectionRefusedError:
            print(f"Tentativa {attempt + 1}/10 falhou. Aguardando 1s...")
            await asyncio.sleep(1)

    if not websocket:
        print("Falha ao conectar no servidor apos 10 tentativas.")
        return False

    try:
        print("Conectado. Aguardando sync_state inicial...")
        sync_data = await recv_json(websocket, timeout=5.0)
        assert sync_data["type"] == "sync_state"
        assert sync_data["state"]["model"] in EXPECTED_BUILTIN_MODELS
        assert sync_data["models"]["builtin"] == EXPECTED_BUILTIN_MODELS
        assert sync_data["state"]["paths"]["rules_file"].endswith("product_config/initial_rules.txt")
        initial_total_keys = sync_data["state"].get("credentials", {}).get("total_keys", 0)
        print("sync_state inicial recebido com modelo Gemini e catalogo correto.")

        print("Simulando handshake interrompido para validar resiliencia do daemon...")
        raw_socket = socket.create_connection((host, int(port)), timeout=2)
        raw_socket.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n")
        raw_socket.close()
        await asyncio.sleep(0.3)
        await websocket.send(json.dumps({"action": "healthcheck"}))
        response = await recv_until_action(websocket, "healthcheck")
        assert response["action"] == "healthcheck"
        print("Daemon continuou responsivo apos handshake interrompido.")

        print("Enviando healthcheck...")
        await websocket.send(json.dumps({"action": "healthcheck"}))
        response = await recv_until_action(websocket, "healthcheck")
        assert response["type"] == "action_response"
        assert response["action"] == "healthcheck"
        assert response["success"] is True
        print("Healthcheck recebido com sucesso.")

        print("Enviando get_models...")
        await websocket.send(json.dumps({"action": "get_models"}))
        response = await recv_until_action(websocket, "get_models")
        assert response["action"] == "get_models"
        assert response["data"]["builtin"] == EXPECTED_BUILTIN_MODELS
        print("get_models ok.")

        print("Testando cadastro e rotacao manual de API keys Gemini...")
        await websocket.send(
            json.dumps(
                {
                    "action": "add_api_key",
                    "payload": {"label": KEY_LABEL_1, "key": KEY_SECRET_1, "set_active": True},
                }
            )
        )
        response = await recv_until_action(websocket, "add_api_key")
        assert response["action"] == "add_api_key"
        assert response["success"] is True
        first_key_id = next(item["id"] for item in response["data"]["keys"] if item["label"] == KEY_LABEL_1)

        await websocket.send(
            json.dumps(
                {
                    "action": "add_api_key",
                    "payload": {"label": KEY_LABEL_2, "key": KEY_SECRET_2, "set_active": False},
                }
            )
        )
        response = await recv_until_action(websocket, "add_api_key")
        assert response["action"] == "add_api_key"
        assert response["success"] is True
        assert response["data"]["total_keys"] >= 2
        second_key_id = next(item["id"] for item in response["data"]["keys"] if item["label"] == KEY_LABEL_2)

        await websocket.send(
            json.dumps(
                {
                    "action": "update_api_key",
                    "payload": {"id": first_key_id, "label": KEY_LABEL_1_EDITED, "key": KEY_SECRET_1_EDITED},
                }
            )
        )
        response = await recv_until_action(websocket, "update_api_key")
        assert response["action"] == "update_api_key"
        assert response["success"] is True
        assert any(item["label"] == KEY_LABEL_1_EDITED for item in response["data"]["keys"] if item["id"] == first_key_id)

        await websocket.send(
            json.dumps(
                {
                    "action": "select_api_key",
                    "payload": {"id": second_key_id},
                }
            )
        )
        response = await recv_until_action(websocket, "select_api_key")
        assert response["action"] == "select_api_key"
        assert response["success"] is True
        assert response["data"]["active_key_id"] == second_key_id

        await websocket.send(json.dumps({"action": "rotate_api_key"}))
        response = await recv_until_action(websocket, "rotate_api_key")
        assert response["action"] == "rotate_api_key"
        assert response["success"] is True
        assert response["data"]["active_key_id"] != second_key_id

        await websocket.send(json.dumps({"action": "get_api_keys"}))
        response = await recv_until_action(websocket, "get_api_keys")
        assert response["action"] == "get_api_keys"
        assert response["success"] is True
        assert response["data"]["total_keys"] >= 2
        assert all("secret" not in item for item in response["data"].get("keys", []))
        print("Cadastro/rotacao de API keys Gemini confirmado.")

        print("Validando get_config com credenciais mascaradas e fonte persistida...")
        await websocket.send(json.dumps({"action": "get_config"}))
        response = await recv_until_action(websocket, "get_config")
        assert response["action"] == "get_config"
        assert response["success"] is True
        assert response["data"]["credentials"]["source"] == "persisted"
        assert response["data"]["credentials"]["total_keys"] >= 2
        assert all("secret" not in item for item in response["data"]["credentials"].get("keys", []))
        print("get_config ok com credenciais persistidas sem segredos expostos.")

        print("Limpando credenciais persistidas de teste para voltar ao ambiente real antes da execucao...")
        for key_id in (first_key_id, second_key_id):
            await websocket.send(
                json.dumps(
                    {
                        "action": "delete_api_key",
                        "payload": {"id": key_id},
                    }
                )
            )
            response = await recv_until_action(websocket, "delete_api_key")
            assert response["action"] == "delete_api_key"
            assert response["success"] is True

        await websocket.send(json.dumps({"action": "get_config"}))
        response = await recv_until_action(websocket, "get_config")
        assert response["action"] == "get_config"
        assert response["success"] is True
        assert response["data"]["credentials"]["total_keys"] == initial_total_keys
        if initial_total_keys == 0:
            if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
                assert response["data"]["credentials"]["source"] == "environment"
            else:
                assert response["data"]["credentials"]["source"] == "missing"

        await websocket.send(json.dumps({"action": "get_api_keys"}))
        response = await recv_until_action(websocket, "get_api_keys")
        assert response["action"] == "get_api_keys"
        assert response["success"] is True
        assert all(item["id"] not in {first_key_id, second_key_id} for item in response["data"].get("keys", []))
        print("Credenciais persistidas de smoke removidas antes da execucao real.")

        print("Testando hotswap Gemini...")
        await websocket.send(
            json.dumps(
                {
                    "action": "change_model",
                    "payload": {"model": "gemini/gemini-2.5-flash"},
                }
            )
        )
        replies = [
            json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0)),
            json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0)),
        ]
        assert any(item["type"] == "sync_state" and item["state"]["model"] == "gemini/gemini-2.5-flash" for item in replies)
        assert any(item["type"] == "action_response" and item["success"] is True for item in replies)
        print("Hotswap Gemini recebido com sucesso.")

        print("Testando persistencia de modelo Gemini customizado...")
        await websocket.send(
            json.dumps(
                {
                    "action": "change_model",
                    "payload": {"model": CUSTOM_MODEL},
                }
            )
        )
        replies = [
            json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0)),
            json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0)),
        ]
        assert any(item["type"] == "sync_state" and item["state"]["model"] == CUSTOM_MODEL for item in replies)
        assert any(CUSTOM_MODEL in item.get("data", {}).get("models", {}).get("custom", []) for item in replies if item["type"] == "action_response")
        print("Modelo customizado persistido no catalogo.")

        print("Voltando para um Gemini nativo antes da execucao...")
        await websocket.send(
            json.dumps(
                {
                    "action": "change_model",
                    "payload": {"model": EXECUTION_MODEL},
                }
            )
        )
        replies = [
            json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0)),
            json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0)),
        ]
        assert any(item["type"] == "sync_state" and item["state"]["model"] == EXECUTION_MODEL for item in replies)
        print("Modelo nativo restaurado para a execucao.")

        print("Gerando historico de sessao para validar reconexao...")
        await websocket.send(
            json.dumps(
                {
                    "action": "execute_task",
                    "payload": {"prompt": PROMPT},
                }
            )
        )
        action_response = await recv_until_action(websocket, "execute_task")
        assert action_response["type"] == "action_response"
        assert action_response["action"] == "execute_task"
        assert action_response["success"] is True

        print("Abrindo segunda conexao enquanto a tarefa esta em andamento...")
        secondary = await websockets.connect(uri)
        secondary_sync = await recv_json(secondary, timeout=5.0)
        assert secondary_sync["type"] == "sync_state"
        await secondary.close()
        print("Backend aceitou nova conexao durante execucao do agente.")

        seen_user_prompt = False
        seen_model_reply = False
        task_error = ""
        for _ in range(60):
            incoming = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10.0))
            if incoming["type"] == "stream" and incoming["message_type"] == "user" and PROMPT in incoming["content"]:
                seen_user_prompt = True
            if incoming["type"] == "stream" and incoming["message_type"] == "message" and "teste" in incoming["content"].lower():
                seen_model_reply = True
            if incoming["type"] == "stream" and incoming["message_type"] == "status" and incoming["content"].startswith("Erro:"):
                task_error = incoming["content"]
            if incoming["type"] == "sync_state" and incoming["state"]["status"] == "idle" and seen_user_prompt:
                break
        assert seen_user_prompt is True
        if REQUIRE_LIVE_MODEL:
            assert not task_error, task_error
            assert seen_model_reply is True, "Nao houve resposta real do modelo Gemini para a tarefa"
        await websocket.close()

        print("Reconectando para validar handshake com historico e modelos persistidos...")
        websocket = await websockets.connect(uri)
        sync_data = await recv_json(websocket, timeout=5.0)
        assert sync_data["type"] == "sync_state"
        assert sync_data["state"]["model"] == EXECUTION_MODEL
        assert CUSTOM_MODEL in sync_data["models"]["custom"]
        assert any(item["message_type"] == "user" and PROMPT in item["content"] for item in sync_data.get("history", []))
        assert all(item.get("timestamp") for item in sync_data.get("history", []))
        print("Historico e modelo customizado retornaram no handshake.")

        print("Validando rejeicao a modelo nao-Gemini...")
        await websocket.send(
            json.dumps(
                {
                    "action": "change_model",
                    "payload": {"model": "gpt-4o"},
                }
            )
        )
        response = await recv_until_action(websocket, "change_model")
        assert response["type"] == "action_response"
        assert response["action"] == "change_model"
        assert response["success"] is False
        print("Rejeicao a modelo nao-Gemini confirmada.")

        log_dir = os.environ.get("MARK_LOG_DIR", "").strip()
        if log_dir:
            print(f"Validando trilha de logs em {log_dir}...")
            backend_log = Path(log_dir) / "backend.log"
            operations_log = Path(log_dir) / "operations.log"
            errors_log = Path(log_dir) / "errors.log"

            assert backend_log.exists()
            assert operations_log.exists()
            assert errors_log.exists()

            operations_text = operations_log.read_text(encoding="utf-8")
            backend_text = backend_log.read_text(encoding="utf-8")

            assert "api_key_added" in operations_text
            assert "api_key_updated" in operations_text
            assert "api_key_selected" in operations_text
            assert "api_key_rotated_manual" in operations_text
            assert "api_key_deleted" in operations_text
            assert "manual_model_switch_success" in operations_text
            assert "manual_model_switch_failed" in operations_text
            assert "frontend_connection_reconnect" in operations_text or "frontend_connection_open" in operations_text
            assert KEY_SECRET_1 not in operations_text
            assert KEY_SECRET_2 not in operations_text
            assert KEY_SECRET_1_EDITED not in operations_text
            assert KEY_SECRET_1 not in backend_text
            assert KEY_SECRET_2 not in backend_text
            print("Logs operacionais e de backend confirmados sem segredo exposto.")

        print("\nSMOKE TEST DO BACKEND: SUCESSO!")
        await websocket.close()
        return True
    except Exception as exc:
        print(f"\nSMOKE TEST DO BACKEND FALHOU: {exc}")
        return False


if __name__ == "__main__":
    success = asyncio.run(smoke_test())
    raise SystemExit(0 if success else 1)
