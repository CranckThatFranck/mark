
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path("/home/francisco/Documentos/repos/mark/src/frontend")))
from ws_client import JarvisWSClient

async def reset_mode():
    c = JarvisWSClient()
    l = asyncio.get_running_loop()
    c.start(l)
    await asyncio.sleep(1)
    await c.send_action("change_mode", {"mode": "agent"})
    await asyncio.sleep(1)

asyncio.run(reset_mode())
