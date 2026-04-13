import asyncio
import sys

# Injeta src/frontend no path
from pathlib import Path
frontend_path = Path(__file__).parent.parent / "src" / "frontend"
sys.path.append(str(frontend_path))

from ws_client import JarvisWSClient

async def run_client_smoke():
    messages_received = []
    def mock_ui_callback(data):
        messages_received.append(data)
        print(f"[UI] Recebeu: {data}")

    client = JarvisWSClient(ui_callback=mock_ui_callback)
    
    # Roda cliente em background task
    loop = asyncio.get_running_loop()
    client.start(loop)
    
    # Aguarda conexão e sincro
    print("Aguardando conexao...")
    for _ in range(50): # wait 5s
        if client.connected:
            break
        await asyncio.sleep(0.1)
        
    assert client.connected, "Cliente WS não conectou"
    print("Conectado! Aguardando mensagens...")
    
    # Espera até receber sync_state e connection_status
    await asyncio.sleep(1)
    
    types_received = [m.get("type") for m in messages_received]
    assert "connection_status" in types_received
    assert "sync_state" in types_received
    
    print("Enviando change_mode para testar tolerância a falhas...")
    await client.send_action("change_mode", {"mode": "plan"})
    await asyncio.sleep(0.5)
    
    # Checa a nova mensagem
    assert any(m.get("type") == "action_response" and m.get("action") == "change_mode" for m in messages_received)
    
    print("\nSMOKE TEST FRONTEND WS_CLIENT: SUCESSO!")
    sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(run_client_smoke())
    except AssertionError as e:
        print(f"\nFALHA NO SMOKE TEST FRONTEND: {e}")
        sys.exit(1)
