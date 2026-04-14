import sys
import time
from pathlib import Path

import customtkinter as ctk


frontend_path = Path(__file__).parent.parent / "src" / "frontend"
sys.path.append(str(frontend_path))

from app import JarvisApp


CUSTOM_MODEL = "gemini/gemini-2.5-flash-exp"
EXECUTION_MODEL = "gemini/gemini-2.5-flash"
PROMPT = "Teste de reconexao do frontend."


def pump(app, seconds=0.1):
    end_time = time.time() + seconds
    while time.time() < end_time:
        app.update()
        time.sleep(0.02)


def wait_for(app, predicate, timeout=10.0, message="Condicao nao atendida"):
    end_time = time.time() + timeout
    while time.time() < end_time:
        app.update()
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError(message)


def get_conversation_texts(app):
    return app.get_conversation_texts()


def run_frontend_smoke():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    app = JarvisApp()
    app.start_connection()

    wait_for(app, lambda: app.connection_status == "connected", message="Frontend nao conectou ao backend")
    wait_for(app, lambda: len(app.known_models) >= 5, message="Catalogo Gemini nao carregou")
    assert not hasattr(app, "region_menu"), "A UI nao deveria mais expor regiao/zona"

    app.send_action_async("change_model", {"model": CUSTOM_MODEL})
    wait_for(app, lambda: CUSTOM_MODEL in app.known_models, message="Modelo customizado nao entrou no catalogo")

    app.send_action_async("change_model", {"model": EXECUTION_MODEL})
    wait_for(app, lambda: app.last_confirmed_model == EXECUTION_MODEL, message="Modelo nativo nao foi restaurado")

    app.input_entry.insert(0, PROMPT)
    app.on_send()
    wait_for(
        app,
        lambda: any(PROMPT in text for text in get_conversation_texts(app)),
        timeout=20.0,
        message="Prompt do usuario nao apareceu na conversa",
    )
    assert any(block["timestamp"] for block in app.conversation_blocks), "Mensagens sem timestamp visivel"
    assert len(app.technical_blocks) > 0, "Painel tecnico nao recebeu eventos"

    print("Forcando interrupcao abrupta do transporte para validar reconexao...")
    app.async_loop.call_soon_threadsafe(app.ws_client.websocket.transport.abort)
    wait_for(
        app,
        lambda: app.connection_status in {"reconnecting", "connected"},
        timeout=10.0,
        message="Frontend nao detectou falha temporaria de transporte",
    )
    wait_for(
        app,
        lambda: app.connection_status == "connected",
        timeout=15.0,
        message="Frontend nao reconectou apos falha temporaria de transporte",
    )
    wait_for(
        app,
        lambda: any(PROMPT in text for text in get_conversation_texts(app)),
        timeout=15.0,
        message="Historico nao reapareceu apos reconexao",
    )

    app.toggle_technical_panel()
    pump(app, 0.2)
    assert app.technical_panel_collapsed is True
    app.toggle_technical_panel()
    pump(app, 0.2)
    assert app.technical_panel_collapsed is False

    app.copy_to_clipboard(PROMPT)
    assert PROMPT in app.clipboard_get()

    pump(app, 0.3)
    app.on_close()

    app_reopened = JarvisApp()
    app_reopened.start_connection()

    wait_for(
        app_reopened,
        lambda: app_reopened.connection_status == "connected",
        message="Frontend reaberto nao reconectou",
    )
    wait_for(
        app_reopened,
        lambda: app_reopened.last_confirmed_model == EXECUTION_MODEL,
        message="Modelo nativo ativo nao reapareceu apos reabrir o frontend",
    )
    wait_for(
        app_reopened,
        lambda: any(PROMPT in text for text in get_conversation_texts(app_reopened)),
        timeout=20.0,
        message="Historico da sessao nao reapareceu no frontend reaberto",
    )
    assert CUSTOM_MODEL in app_reopened.known_models
    assert not hasattr(app_reopened, "region_menu"), "A UI reaberta nao deveria expor regiao/zona"

    pump(app_reopened, 0.3)
    app_reopened.on_close()

    print("SMOKE TEST FRONTEND: SUCESSO!")


if __name__ == "__main__":
    try:
        run_frontend_smoke()
    except AssertionError as exc:
        print(f"\nFALHA NO SMOKE TEST FRONTEND: {exc}")
        raise SystemExit(1)
