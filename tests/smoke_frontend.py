import sys
import time
from pathlib import Path

import customtkinter as ctk


frontend_path = Path(__file__).parent.parent / "src" / "frontend"
sys.path.append(str(frontend_path))

from app import INPUT_MIN_LINES, JarvisApp


CUSTOM_MODEL = "gemini/gemini-2.5-flash-exp"
EXECUTION_MODEL = "gemini/gemini-2.5-flash"
PROMPT = "Responda apenas com a palavra teste."


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


def get_canvas_end(scrollable_frame):
    return scrollable_frame._parent_canvas.yview()[1]


def get_canvas_start(scrollable_frame):
    return scrollable_frame._parent_canvas.yview()[0]


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

    multiline_prompt = "Linha 1 do teste\nLinha 2 do teste\nLinha 3 do teste\nLinha 4 do teste"
    app.input_text.insert("1.0", multiline_prompt)
    app.on_input_shift_return()
    app.input_text.insert("end", "Linha 5 do teste")
    pump(app, 0.2)
    assert "\n" in app.get_input_text(), "Shift+Enter nao inseriu quebra de linha"
    assert int(app.input_text.cget("height")) > INPUT_MIN_LINES, "Campo de entrada nao expandiu verticalmente"

    app.clear_input_text()
    app.input_text.insert("1.0", PROMPT)
    app.on_input_return()
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

    print("Validando autoscroll da conversa e do painel tecnico...")
    for index in range(18):
        app.append_conversation_entry("message", f"Bloco extra da conversa {index}.", merge_if_possible=False)
        app.append_technical_entry("system", f"Evento tecnico extra {index}.", merge_if_possible=False)
    pump(app, 0.3)
    assert app.is_conversation_at_bottom() is True, "Conversa nao ficou ancorada no final"
    assert app.is_technical_at_bottom() is True, "Painel tecnico nao ficou ancorado no final"

    app.conversation_frame._parent_canvas.yview_moveto(0.0)
    app.technical_frame._parent_canvas.yview_moveto(0.0)
    app.append_conversation_entry("message", "Nao puxar conversa para baixo enquanto leio historico.", merge_if_possible=False)
    app.append_technical_entry("system", "Nao puxar painel tecnico para baixo enquanto leio historico.", merge_if_possible=False)
    pump(app, 0.3)
    assert app.is_conversation_at_bottom() is False, "Conversa voltou para o fim enquanto o usuario lia historico"
    assert app.is_technical_at_bottom() is False, "Painel tecnico voltou para o fim enquanto o usuario lia historico"
    assert get_canvas_start(app.conversation_frame) <= 0.1, "Conversa saiu demais da area que o usuario estava lendo"
    assert get_canvas_start(app.technical_frame) <= 0.1, "Painel tecnico saiu demais da area que o usuario estava lendo"

    app.conversation_frame._parent_canvas.yview_moveto(1.0)
    app.technical_frame._parent_canvas.yview_moveto(1.0)
    app.append_conversation_entry("message", "Seguir conversa quando eu estiver no fim.", merge_if_possible=False)
    app.append_technical_entry("system", "Seguir painel tecnico quando eu estiver no fim.", merge_if_possible=False)
    pump(app, 0.3)
    assert app.is_conversation_at_bottom() is True, "Conversa nao retomou autoscroll ao voltar para o fim"
    assert app.is_technical_at_bottom() is True, "Painel tecnico nao retomou autoscroll ao voltar para o fim"

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
