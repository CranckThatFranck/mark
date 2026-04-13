import asyncio
import websockets
import json
import time

async def smoke_test():
    uri = "ws://127.0.0.1:8765"
    print(f"Tentando conectar ao backend em {uri}...")
    
    websocket = None
    for i in range(10):
        try:
            websocket = await websockets.connect(uri)
            break
        except ConnectionRefusedError:
            print(f"Tentativa {i+1}/10 falhou. Aguardando 1s...")
            await asyncio.sleep(1)
            
    if not websocket:
        print("Falha ao conectar no servidor após 10 tentativas.")
        return False
        
    try:
        print("Conectado. Aguardando sync_state inicial...")
        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(response)
        assert data["type"] == "sync_state", f"Esperado sync_state, recebido: {data['type']}"
        print("sync_state inicial recebido com sucesso!")
        
        print("Enviando healthcheck...")
        await websocket.send(json.dumps({"action": "healthcheck"}))
        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(response)
        assert data["type"] == "action_response"
        assert data["action"] == "healthcheck"
        assert data["success"] == True
        print("Healthcheck recebido com sucesso!")
        
        print("Enviando get_models...")
        await websocket.send(json.dumps({"action": "get_models"}))
        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(response)
        assert data["action"] == "get_models"
        assert len(data["data"]["models"]) > 0
        print(f"get_models ok. Modelos: {data['data']['models']}")

        print("\nSMOKE TEST DO BACKEND: SUCESSO!")
        await websocket.close()
        return True
    except Exception as e:
        print(f"\nSMOKE TEST DO BACKEND FALHOU: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(smoke_test())
    import sys
    sys.exit(0 if success else 1)
