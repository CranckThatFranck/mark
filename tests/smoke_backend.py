import asyncio
import json
import os

import websockets


EXPECTED_BUILTIN_MODELS = [
    "gemini/gemini-3-flash-preview",
    "gemini/gemini-3.1-pro-preview-customtools",
    "gemini/gemini-3.1-pro-preview",
    "gemini/gemini-2.5-pro",
    "gemini/gemini-2.5-flash",
]
CUSTOM_MODEL = "gemini/gemini-2.5-flash-exp"
PROMPT = "Responda apenas com a palavra teste."


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
        sync_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        sync_data = json.loads(sync_raw)
        assert sync_data["type"] == "sync_state"
        assert sync_data["state"]["model"] in EXPECTED_BUILTIN_MODELS
        assert sync_data["models"]["builtin"] == EXPECTED_BUILTIN_MODELS
        print("sync_state inicial recebido com modelo Gemini e catalogo correto.")

        print("Enviando healthcheck...")
        await websocket.send(json.dumps({"action": "healthcheck"}))
        response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0))
        assert response["type"] == "action_response"
        assert response["action"] == "healthcheck"
        assert response["success"] is True
        print("Healthcheck recebido com sucesso.")

        print("Enviando get_models...")
        await websocket.send(json.dumps({"action": "get_models"}))
        response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0))
        assert response["action"] == "get_models"
        assert response["data"]["builtin"] == EXPECTED_BUILTIN_MODELS
        print("get_models ok.")

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

        print("Gerando historico de sessao para validar reconexao...")
        await websocket.send(
            json.dumps(
                {
                    "action": "execute_task",
                    "payload": {"prompt": PROMPT},
                }
            )
        )
        action_response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0))
        assert action_response["type"] == "action_response"
        assert action_response["action"] == "execute_task"
        assert action_response["success"] is True

        seen_user_prompt = False
        for _ in range(60):
            incoming = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10.0))
            if incoming["type"] == "stream" and incoming["message_type"] == "user" and PROMPT in incoming["content"]:
                seen_user_prompt = True
            if incoming["type"] == "sync_state" and incoming["state"]["status"] == "idle" and seen_user_prompt:
                break
        assert seen_user_prompt is True
        await websocket.close()

        print("Reconectando para validar handshake com historico e modelos persistidos...")
        websocket = await websockets.connect(uri)
        sync_data = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0))
        assert sync_data["type"] == "sync_state"
        assert sync_data["state"]["model"] == CUSTOM_MODEL
        assert CUSTOM_MODEL in sync_data["models"]["custom"]
        assert any(item["message_type"] == "user" and PROMPT in item["content"] for item in sync_data.get("history", []))
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
        response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5.0))
        assert response["type"] == "action_response"
        assert response["action"] == "change_model"
        assert response["success"] is False
        print("Rejeicao a modelo nao-Gemini confirmada.")

        print("\nSMOKE TEST DO BACKEND: SUCESSO!")
        await websocket.close()
        return True
    except Exception as exc:
        print(f"\nSMOKE TEST DO BACKEND FALHOU: {exc}")
        return False


if __name__ == "__main__":
    success = asyncio.run(smoke_test())
    raise SystemExit(0 if success else 1)
