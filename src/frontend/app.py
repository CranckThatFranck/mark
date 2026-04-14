import asyncio
from datetime import datetime
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk

from ui_config import DEFAULT_BACKEND_HOST, load_frontend_config, normalize_backend_host, save_frontend_config
from ws_client import JarvisWSClient


ADD_MODEL_LABEL = "Adicionar Gemini..."
ADD_API_KEY_LABEL = "Cadastrar API key Gemini..."
EMPTY_API_KEY_LABEL = "Sem chave persistida (usa GOOGLE_API_KEY)"
USER_MESSAGE_TYPES = {"user", "message"}
MERGEABLE_TECHNICAL_TYPES = {"code", "console"}
AUTO_SCROLL_THRESHOLD = 0.04
INPUT_MIN_LINES = 2
INPUT_MAX_LINES = 8
LOCAL_BACKEND_HOSTS = {"127.0.0.1", "localhost", "::1"}
TECHNICAL_HEADERS = {
    "status": "Status",
    "system": "Sistema",
    "code": "Codigo",
    "console": "Console",
}
CONNECTION_STYLES = {
    "connecting": {
        "badge": "Conectando ao backend...",
        "fg": "#2e2a16",
        "text": "#f4d58d",
    },
    "connected": {
        "badge": "Backend conectado",
        "fg": "#1b4332",
        "text": "#d8f3dc",
    },
    "reconnecting": {
        "badge": "Falha temporaria de comunicacao",
        "fg": "#3a2d14",
        "text": "#f7d488",
    },
    "unavailable": {
        "badge": "Backend indisponivel",
        "fg": "#3a181d",
        "text": "#ffb4a2",
    },
    "disconnected": {
        "badge": "Backend desconectado",
        "fg": "#3a181d",
        "text": "#ffb4a2",
    },
}


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mark Alfa")
        self.geometry("1180x800")
        self.minsize(980, 680)
        self.configure(fg_color="#121416")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        frontend_config = load_frontend_config()
        self.backend_host = normalize_backend_host(os.environ.get("MARK_WS_HOST", frontend_config.get("backend_host")))
        self.backend_port = int(os.environ.get("MARK_WS_PORT", "8765"))
        self.ws_client = None
        self.async_loop = None
        self.connection_status = "disconnected"
        self.connection_detail = ""
        self.known_models = []
        self.last_confirmed_model = ""
        self.pending_model_change = None
        self.last_confirmed_mode = "agent"
        self.api_key_catalog = {"active_key_id": None, "keys": []}
        self.api_key_display_to_id = {}
        self._syncing_api_key_menu = False
        self.backend_paths = {}
        self.conversation_blocks = []
        self.technical_blocks = []
        self.last_conversation_block = None
        self.last_technical_block = None
        self.message_queue = queue.SimpleQueue()
        self.technical_panel_collapsed = False
        self._technical_restore_requested = False
        self._sash_initialized = False
        self._last_connection_notice = None
        self._closing_ui = False
        self._poll_after_id = None
        self._sash_after_id = None
        self._input_resize_after_id = None
        self._last_body_pane_height = None
        self._last_input_width = None
        self._current_input_lines = INPUT_MIN_LINES

        self.build_sidebar()
        self.build_main_area()

        self.bind("<Control-Shift-R>", lambda _event: self.open_rules_target())
        self.bind("<Control-Shift-T>", lambda _event: self.toggle_technical_panel())
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._poll_after_id = self.after(50, self.poll_ui_queue)

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#171a1c")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(17, weight=1)

        title_font = ctk.CTkFont(size=22, weight="bold")
        section_font = ctk.CTkFont(size=12, weight="bold")

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Mark Alfa",
            font=title_font,
            anchor="w",
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(24, 8), sticky="ew")

        self.connection_badge = ctk.CTkLabel(
            self.sidebar_frame,
            text=CONNECTION_STYLES["disconnected"]["badge"],
            fg_color=CONNECTION_STYLES["disconnected"]["fg"],
            text_color=CONNECTION_STYLES["disconnected"]["text"],
            corner_radius=6,
            padx=10,
            pady=8,
        )
        self.connection_badge.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="ew")

        self.backend_host_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Host do backend",
            font=section_font,
            anchor="w",
            text_color="#c7d0d9",
        )
        self.backend_host_label.grid(row=2, column=0, padx=20, pady=(0, 6), sticky="ew")

        self.backend_host_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.backend_host_frame.grid(row=3, column=0, padx=20, pady=(0, 6), sticky="ew")
        self.backend_host_frame.grid_columnconfigure(0, weight=1)

        self.backend_host_var = ctk.StringVar(value=self.backend_host)
        self.backend_host_entry = ctk.CTkEntry(
            self.backend_host_frame,
            textvariable=self.backend_host_var,
            placeholder_text=DEFAULT_BACKEND_HOST,
        )
        self.backend_host_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.backend_host_entry.bind("<Return>", self.on_apply_backend_host)

        self.apply_host_btn = ctk.CTkButton(
            self.backend_host_frame,
            text="Aplicar",
            width=78,
            command=self.on_apply_backend_host,
            fg_color="#2b313d",
            hover_color="#384253",
        )
        self.apply_host_btn.grid(row=0, column=1)

        self.backend_target_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Destino atual: Local | 127.0.0.1:8765",
            anchor="w",
            justify="left",
            wraplength=220,
            text_color="#9eaab3",
        )
        self.backend_target_label.grid(row=4, column=0, padx=20, pady=(0, 16), sticky="ew")

        self.mode_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Modo",
            font=section_font,
            anchor="w",
            text_color="#c7d0d9",
        )
        self.mode_label.grid(row=5, column=0, padx=20, pady=(0, 6), sticky="ew")

        self.mode_var = ctk.StringVar(value="agent")
        self.mode_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["agent", "plan"],
            variable=self.mode_var,
            command=self.on_mode_change,
            fg_color="#244d3f",
            button_color="#2c6b57",
            button_hover_color="#1f5344",
        )
        self.mode_menu.grid(row=6, column=0, padx=20, pady=(0, 16), sticky="ew")

        self.model_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Modelo Gemini",
            font=section_font,
            anchor="w",
            text_color="#c7d0d9",
        )
        self.model_label.grid(row=7, column=0, padx=20, pady=(0, 6), sticky="ew")

        self.model_var = ctk.StringVar(value="Carregando...")
        self.model_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Carregando..."],
            variable=self.model_var,
            command=self.on_model_change,
            dynamic_resizing=False,
            fg_color="#2d3d2d",
            button_color="#4a6f45",
            button_hover_color="#39563a",
        )
        self.model_menu.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.add_model_btn = ctk.CTkButton(
            self.sidebar_frame,
            text=ADD_MODEL_LABEL,
            command=self.on_add_model,
            fg_color="#6b4f1f",
            hover_color="#825e24",
        )
        self.add_model_btn.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.api_key_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="API Key Gemini ativa",
            font=section_font,
            anchor="w",
            text_color="#c7d0d9",
        )
        self.api_key_label.grid(row=10, column=0, padx=20, pady=(0, 6), sticky="ew")

        self.api_key_var = ctk.StringVar(value=EMPTY_API_KEY_LABEL)
        self.api_key_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=[EMPTY_API_KEY_LABEL],
            variable=self.api_key_var,
            command=self.on_api_key_selected,
            dynamic_resizing=False,
            fg_color="#2e3642",
            button_color="#3d4c5d",
            button_hover_color="#4a5c72",
        )
        self.api_key_menu.grid(row=11, column=0, padx=20, pady=(0, 8), sticky="ew")

        self.api_key_actions_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.api_key_actions_frame.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.api_key_actions_frame.grid_columnconfigure(0, weight=1)
        self.api_key_actions_frame.grid_columnconfigure(1, weight=1)

        self.add_api_key_btn = ctk.CTkButton(
            self.api_key_actions_frame,
            text=ADD_API_KEY_LABEL,
            command=self.on_add_api_key,
            fg_color="#40534f",
            hover_color="#4f6762",
        )
        self.add_api_key_btn.grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="ew")

        self.edit_api_key_btn = ctk.CTkButton(
            self.api_key_actions_frame,
            text="Editar key",
            command=self.on_edit_api_key,
            fg_color="#2f3e4a",
            hover_color="#3a4d5d",
        )
        self.edit_api_key_btn.grid(row=1, column=0, padx=(0, 6), sticky="ew")

        self.rotate_api_key_btn = ctk.CTkButton(
            self.api_key_actions_frame,
            text="Rotacionar",
            command=self.on_rotate_api_key,
            fg_color="#5a4722",
            hover_color="#6d5729",
        )
        self.rotate_api_key_btn.grid(row=1, column=1, padx=(6, 0), sticky="ew")

        self.sync_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Sincronizar",
            command=self.force_sync,
            fg_color="#25353f",
            hover_color="#2d4655",
        )
        self.sync_btn.grid(row=13, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.rules_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Abrir regras",
            command=self.open_rules_target,
            fg_color="#3d3450",
            hover_color="#4d4266",
        )
        self.rules_btn.grid(row=14, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.rules_dir_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Abrir pasta das regras",
            command=self.open_rules_directory,
            fg_color="#2b313d",
            hover_color="#384253",
        )
        self.rules_dir_btn.grid(row=15, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.toggle_technical_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Ocultar painel tecnico",
            command=self.toggle_technical_panel,
            fg_color="#31414a",
            hover_color="#3b4f59",
        )
        self.toggle_technical_btn.grid(row=16, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.kill_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Interromper",
            command=self.on_kill_switch,
            fg_color="#8c2f39",
            hover_color="#75262f",
        )
        self.kill_btn.grid(row=18, column=0, padx=20, pady=(0, 20), sticky="ew")

        self.update_backend_target_widgets()

    def build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.session_title = ctk.CTkLabel(
            self.header_frame,
            text="Sessao ativa",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        self.session_title.grid(row=0, column=0, sticky="ew")

        self.session_status = ctk.CTkLabel(
            self.header_frame,
            text="Aguardando backend",
            font=ctk.CTkFont(size=13),
            anchor="w",
            text_color="#9eaab3",
        )
        self.session_status.grid(row=1, column=0, pady=(4, 0), sticky="ew")

        self.body_pane = tk.PanedWindow(
            self.main_frame,
            orient="vertical",
            sashwidth=8,
            bg="#121416",
            relief="flat",
            bd=0,
            opaqueresize=True,
            showhandle=False,
        )
        self.body_pane.grid(row=1, column=0, padx=18, sticky="nsew")

        self.conversation_panel = ctk.CTkFrame(self.body_pane, corner_radius=0, fg_color="transparent")
        self.conversation_panel.grid_columnconfigure(0, weight=1)
        self.conversation_panel.grid_rowconfigure(0, weight=1)

        self.conversation_frame = ctk.CTkScrollableFrame(
            self.conversation_panel,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_button_color="#38444c",
            scrollbar_button_hover_color="#4b5962",
        )
        self.conversation_frame.grid(row=0, column=0, sticky="nsew")
        self.conversation_frame.grid_columnconfigure(0, weight=1)

        self.technical_panel = ctk.CTkFrame(self.body_pane, corner_radius=6, fg_color="#101316")
        self.technical_panel.grid_columnconfigure(0, weight=1)
        self.technical_panel.grid_rowconfigure(1, weight=1)

        self.technical_toolbar = ctk.CTkFrame(self.technical_panel, fg_color="transparent")
        self.technical_toolbar.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        self.technical_toolbar.grid_columnconfigure(0, weight=1)

        self.technical_title = ctk.CTkLabel(
            self.technical_toolbar,
            text="Fluxo tecnico",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            text_color="#9eaab3",
        )
        self.technical_title.grid(row=0, column=0, sticky="w")

        self.copy_technical_btn = ctk.CTkButton(
            self.technical_toolbar,
            text="Copiar painel",
            width=110,
            command=self.copy_all_technical_entries,
            fg_color="#39424d",
            hover_color="#46515f",
        )
        self.copy_technical_btn.grid(row=0, column=1, padx=(8, 8))

        self.technical_collapse_btn = ctk.CTkButton(
            self.technical_toolbar,
            text="Recolher",
            width=92,
            command=self.toggle_technical_panel,
            fg_color="#2f3840",
            hover_color="#3a4651",
        )
        self.technical_collapse_btn.grid(row=0, column=2)

        self.technical_frame = ctk.CTkScrollableFrame(
            self.technical_panel,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_button_color="#38444c",
            scrollbar_button_hover_color="#4b5962",
        )
        self.technical_frame.grid(row=1, column=0, padx=6, pady=(0, 8), sticky="nsew")
        self.technical_frame.grid_columnconfigure(0, weight=1)

        self.body_pane.add(self.conversation_panel, stretch="always", minsize=320)
        self.body_pane.add(self.technical_panel, stretch="never", minsize=150)

        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, padx=18, pady=(14, 18), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_editor_frame = ctk.CTkFrame(
            self.input_frame,
            corner_radius=6,
            fg_color="#14181c",
            border_width=1,
            border_color="#273038",
        )
        self.input_editor_frame.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.input_editor_frame.grid_columnconfigure(0, weight=1)
        self.input_editor_frame.grid_rowconfigure(0, weight=1)

        self.input_text = tk.Text(
            self.input_editor_frame,
            height=INPUT_MIN_LINES,
            wrap="word",
            relief="flat",
            bd=0,
            highlightthickness=0,
            bg="#14181c",
            fg="#f4fbf9",
            insertbackground="#f4fbf9",
            selectbackground="#34536a",
            selectforeground="#ffffff",
            undo=True,
            padx=12,
            pady=10,
        )
        input_font = tkfont.nametofont("TkDefaultFont").copy()
        input_font.configure(size=13)
        self.input_text.configure(font=input_font)
        self.input_text.grid(row=0, column=0, sticky="nsew")
        self.input_text.bind("<Return>", self.on_input_return)
        self.input_text.bind("<KP_Enter>", self.on_input_return)
        self.input_text.bind("<Shift-Return>", self.on_input_shift_return)
        self.input_text.bind("<Shift-KP_Enter>", self.on_input_shift_return)
        self.input_text.bind("<<Modified>>", self.on_input_modified)
        self.input_text.edit_modified(False)

        self.input_placeholder = ctk.CTkLabel(
            self.input_editor_frame,
            text="Digite uma tarefa ou mensagem para o Mark...",
            anchor="w",
            text_color="#74808a",
        )
        self.input_placeholder.place(x=14, y=11)
        self.input_placeholder.bind("<Button-1>", lambda _event: self.focus_input())

        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Enviar",
            width=90,
            command=self.on_send,
            fg_color="#2c6b57",
            hover_color="#245545",
        )
        self.send_btn.grid(row=0, column=1)

        self.body_pane.bind("<Configure>", self.on_body_pane_configure)
        self.input_editor_frame.bind("<Configure>", self.on_input_editor_resize)
        self.schedule_input_resize()
        self.schedule_sash_positioning(force=True)

    def backend_target_mode(self):
        return "Local" if self.is_local_backend_host() else "Remoto"

    def backend_target_display(self):
        return f"{self.backend_target_mode()} | {self.backend_host}:{self.backend_port}"

    def is_local_backend_host(self, host=None):
        candidate = normalize_backend_host(host or self.backend_host).lower()
        return candidate in LOCAL_BACKEND_HOSTS

    def update_backend_target_widgets(self):
        self.backend_target_label.configure(text=f"Destino atual: {self.backend_target_display()}")

    def persist_backend_host(self):
        save_frontend_config({"backend_host": self.backend_host})

    def on_body_pane_configure(self, event=None):
        if self._closing_ui or self.technical_panel_collapsed:
            return
        if event is not None and getattr(event, "widget", None) is not self.body_pane:
            return
        current_height = self.body_pane.winfo_height()
        if current_height <= 0:
            return
        if (
            self._last_body_pane_height == current_height
            and self._sash_initialized
            and not self._technical_restore_requested
        ):
            return
        self._last_body_pane_height = current_height
        if not self._sash_initialized or self._technical_restore_requested:
            self.schedule_sash_positioning(force=self._technical_restore_requested)

    def on_input_editor_resize(self, event=None):
        if self._closing_ui:
            return
        if event is not None and getattr(event, "widget", None) is not self.input_editor_frame:
            return
        current_width = self.input_editor_frame.winfo_width()
        if current_width <= 0 or current_width == self._last_input_width:
            return
        self._last_input_width = current_width
        self.schedule_input_resize()

    def schedule_sash_positioning(self, force=False):
        if self._closing_ui or self.technical_panel_collapsed:
            return
        if self._sash_initialized and not (self._technical_restore_requested or force):
            return
        if self._sash_after_id:
            try:
                self.after_cancel(self._sash_after_id)
            except Exception:
                pass
        self._sash_after_id = self.after(80, self.position_initial_sash)

    def position_initial_sash(self):
        self._sash_after_id = None
        if self.technical_panel_collapsed:
            return
        if self._sash_initialized and not self._technical_restore_requested:
            return
        try:
            total_height = self.body_pane.winfo_height()
            if total_height <= 0:
                return
            conversation_height = max(360, total_height - 240)
            current_sash_y = self.body_pane.sash_coord(0)[1]
            if abs(current_sash_y - conversation_height) > 1:
                self.body_pane.sash_place(0, 0, conversation_height)
            self._sash_initialized = True
            self._technical_restore_requested = False
        except Exception:
            pass

    def run_async_loop(self):
        self.async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.async_loop)

        try:
            self.ws_client = JarvisWSClient(
                host=self.backend_host,
                port=self.backend_port,
                ui_callback=self.handle_ws_message,
            )
            self.ws_client.start(self.async_loop)
            self.async_loop.run_forever()
        finally:
            pending_tasks = asyncio.all_tasks(self.async_loop)
            for task in pending_tasks:
                task.cancel()
            if pending_tasks:
                self.async_loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
            self.async_loop.close()

    def start_connection(self):
        threading.Thread(target=self.run_async_loop, daemon=True).start()

    async def restart_ws_client(self):
        previous_client = self.ws_client
        if previous_client:
            await previous_client.close()
        if self._closing_ui or not self.async_loop or self.async_loop.is_closed():
            return
        self.ws_client = JarvisWSClient(
            host=self.backend_host,
            port=self.backend_port,
            ui_callback=self.handle_ws_message,
        )
        self.ws_client.start(self.async_loop)

    def on_close(self):
        self._closing_ui = True
        for after_id in (self._poll_after_id, self._sash_after_id, self._input_resize_after_id):
            if after_id:
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass
        self._poll_after_id = None
        self._sash_after_id = None
        self._input_resize_after_id = None
        if self.async_loop and self.ws_client:
            try:
                close_future = asyncio.run_coroutine_threadsafe(self.ws_client.close(), self.async_loop)
                close_future.result(timeout=2)
            except Exception:
                pass
            try:
                self.async_loop.call_soon_threadsafe(self.async_loop.stop)
            except Exception:
                pass
        self.destroy()

    def handle_ws_message(self, data):
        if self._closing_ui:
            return
        self.message_queue.put(data)

    def poll_ui_queue(self):
        if self._closing_ui or not self.winfo_exists():
            return
        try:
            while True:
                payload = self.message_queue.get_nowait()
                self.process_ws_message(payload)
        except queue.Empty:
            pass

        if self.winfo_exists():
            self._poll_after_id = self.after(50, self.poll_ui_queue)

    def process_ws_message(self, data):
        if self._closing_ui:
            return
        message_type = data.get("type")

        if message_type == "connection_status":
            self.apply_connection_status(data)
            return

        if message_type == "sync_state":
            state = data.get("state", {})
            models = data.get("models")
            if models:
                self.update_model_catalog(models)
            if "history" in data:
                self.render_history(data.get("history", []))
            self.apply_state(state)
            return

        if message_type == "stream":
            self.append_stream_entry(
                data.get("message_type"),
                data.get("content", ""),
                timestamp=data.get("timestamp"),
            )
            return

        if message_type == "action_response":
            self.handle_action_response(data)

    def focus_input(self):
        try:
            self.input_text.focus_set()
        except Exception:
            pass

    def get_input_text(self):
        return self.input_text.get("1.0", "end-1c")

    def clear_input_text(self):
        self.input_text.delete("1.0", "end")
        self.schedule_input_resize()
        self.update_input_placeholder()

    def update_input_placeholder(self):
        has_content = bool(self.get_input_text().strip())
        if has_content:
            self.input_placeholder.place_forget()
        else:
            self.input_placeholder.place(x=14, y=11)

    def schedule_input_resize(self):
        if self._closing_ui:
            return
        if self._input_resize_after_id:
            try:
                self.after_cancel(self._input_resize_after_id)
            except Exception:
                pass
        self._input_resize_after_id = self.after(20, self.update_input_height)

    def update_input_height(self):
        self._input_resize_after_id = None
        if self._closing_ui or not self.winfo_exists():
            return
        try:
            display_lines = int(self.input_text.count("1.0", "end-1c", "displaylines")[0])
        except Exception:
            content = self.get_input_text()
            display_lines = content.count("\n") + 1 if content else INPUT_MIN_LINES
        target_lines = max(INPUT_MIN_LINES, min(INPUT_MAX_LINES, display_lines or INPUT_MIN_LINES))
        if target_lines != self._current_input_lines:
            self.input_text.configure(height=target_lines)
            self._current_input_lines = target_lines
        desired_height = max(48, target_lines * 22)
        if abs(self.input_editor_frame.winfo_height() - desired_height) > 1:
            self.input_editor_frame.configure(height=desired_height)
        self.update_input_placeholder()

    def on_input_modified(self, _event=None):
        try:
            self.input_text.edit_modified(False)
        except Exception:
            pass
        self.schedule_input_resize()

    def on_input_shift_return(self, _event=None):
        self.input_text.insert("insert", "\n")
        self.schedule_input_resize()
        return "break"

    def on_input_return(self, event=None):
        state = getattr(event, "state", 0)
        if state & 0x1:
            return self.on_input_shift_return(event)
        self.on_send()
        return "break"

    def on_apply_backend_host(self, _event=None):
        normalized_host = normalize_backend_host(self.backend_host_var.get())
        self.backend_host_var.set(normalized_host)
        if normalized_host == self.backend_host:
            self.update_backend_target_widgets()
            return "break"

        previous_target = self.backend_target_display()
        self.backend_host = normalized_host
        self.persist_backend_host()
        self.update_backend_target_widgets()
        self.append_technical_entry(
            "system",
            f"Destino do backend alterado de {previous_target} para {self.backend_target_display()}. Reconectando.",
            merge_if_possible=False,
        )

        if self.async_loop and not self.async_loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.restart_ws_client(), self.async_loop)
        return "break"

    def apply_connection_status(self, payload):
        if self._closing_ui:
            return
        status = payload.get("status", "disconnected") if isinstance(payload, dict) else str(payload)
        detail = payload.get("detail", "") if isinstance(payload, dict) else ""
        recovered = bool(payload.get("recovered")) if isinstance(payload, dict) else False
        attempt = payload.get("attempt") if isinstance(payload, dict) else None

        previous_status = self.connection_status
        self.connection_status = status
        self.connection_detail = detail
        self.update_backend_target_widgets()

        style = CONNECTION_STYLES.get(status, CONNECTION_STYLES["disconnected"])
        self.connection_badge.configure(
            text=style["badge"],
            fg_color=style["fg"],
            text_color=style["text"],
        )

        self.send_btn.configure(state="normal" if status == "connected" else "disabled")
        if status != "connected":
            self.set_input_enabled(True)

        notice_key = (status, detail, attempt)
        if notice_key == self._last_connection_notice:
            return

        if status == "connected":
            message = (
                f"Conexao com o backend restabelecida em {self.backend_target_display()}."
                if recovered
                else f"Conexao estabelecida com o backend em {self.backend_target_display()}."
            )
            self.append_technical_entry("system", message)
            self.send_action_async("get_config")
            self.send_action_async("get_api_keys")
            self._last_connection_notice = ("connected", "", None)
            return

        if status == "reconnecting":
            message = f"Falha temporaria de comunicacao em {self.backend_target_display()}. Tentando reconectar automaticamente."
            if detail:
                message = f"{message} Detalhe: {detail}."
            self.append_technical_entry("system", message)
        elif status == "unavailable":
            message = f"Backend indisponivel em {self.backend_target_display()}. O frontend continuara tentando conectar."
            if detail:
                message = f"{message} Detalhe: {detail}."
            self.append_technical_entry("system", message)
        elif previous_status == "connected":
            self.append_technical_entry("system", "Conexao encerrada pelo cliente.")

        self._last_connection_notice = notice_key

    def set_input_enabled(self, enabled: bool):
        desired_state = "normal" if enabled else "disabled"
        if str(self.input_text.cget("state")) != desired_state:
            self.input_text.configure(state=desired_state)
        if enabled:
            self.update_input_placeholder()
        else:
            self.input_placeholder.place_forget()

    def apply_state(self, state):
        self.last_confirmed_mode = state.get("mode", "agent")
        self.mode_var.set(self.last_confirmed_mode)

        current_model = state.get("model", self.last_confirmed_model)
        if current_model:
            self.ensure_model_visible(current_model)
            self.model_var.set(current_model)
            self.last_confirmed_model = current_model

        paths = state.get("paths", {})
        if isinstance(paths, dict):
            self.backend_paths = paths

        credentials = state.get("credentials", {})
        if isinstance(credentials, dict):
            self.update_api_key_catalog(credentials)

        status = state.get("status", "idle")
        active_task = state.get("active_task")
        if status == "running":
            self.send_btn.configure(state="disabled")
            self.set_input_enabled(False)
            if active_task:
                self.session_status.configure(
                    text=f"{self.backend_target_display()} | Executando: {self.truncate_text(active_task, 140)}"
                )
            else:
                self.session_status.configure(text=f"{self.backend_target_display()} | Executando tarefa em andamento")
        else:
            self.send_btn.configure(state="normal" if self.connection_status == "connected" else "disabled")
            self.set_input_enabled(True)
            base_text = f"{self.backend_target_display()} | Modelo ativo: {current_model or 'aguardando sincronizacao'}"
            if self.connection_status in {"reconnecting", "unavailable"} and self.connection_detail:
                base_text = f"{base_text} | Transporte: {self.connection_detail}"
            self.session_status.configure(text=base_text)

    def update_model_catalog(self, catalog):
        if isinstance(catalog, dict):
            model_values = catalog.get("all", [])
        else:
            model_values = catalog or []

        sanitized = []
        seen = set()
        for item in model_values:
            if not isinstance(item, str):
                continue
            normalized = item.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            sanitized.append(normalized)

        if self.last_confirmed_model and self.last_confirmed_model not in sanitized:
            sanitized.insert(0, self.last_confirmed_model)
        if not sanitized:
            sanitized = ["gemini/gemini-3-flash-preview"]

        self.known_models = sanitized
        self.model_menu.configure(values=self.known_models)

    def update_api_key_catalog(self, catalog):
        if not isinstance(catalog, dict):
            return

        raw_keys = catalog.get("keys", [])
        active_key_id = catalog.get("active_key_id")

        sanitized_keys = []
        for item in raw_keys:
            if not isinstance(item, dict):
                continue
            key_id = str(item.get("id", "")).strip()
            label = str(item.get("label", "")).strip()
            masked = str(item.get("masked", "")).strip()
            if not key_id:
                continue
            sanitized_keys.append(
                {
                    "id": key_id,
                    "label": label or "Gemini key",
                    "masked": masked or "***",
                }
            )

        self.api_key_catalog = {
            "active_key_id": active_key_id,
            "keys": sanitized_keys,
        }

        values = []
        mapping = {}
        active_display = ""
        for item in sanitized_keys:
            display = f"{item['label']} | {item['masked']}"
            values.append(display)
            mapping[display] = item["id"]
            if item["id"] == active_key_id:
                active_display = display

        if not values:
            values = [EMPTY_API_KEY_LABEL]
            mapping = {EMPTY_API_KEY_LABEL: None}
            active_display = EMPTY_API_KEY_LABEL
        elif not active_display:
            active_display = values[0]

        self.api_key_display_to_id = mapping
        self._syncing_api_key_menu = True
        self.api_key_menu.configure(values=values)
        self.api_key_var.set(active_display)
        self._syncing_api_key_menu = False

    def get_selected_api_key_id(self):
        selected_display = self.api_key_var.get().strip()
        return self.api_key_display_to_id.get(selected_display)

    def ensure_model_visible(self, model_name):
        if not model_name:
            return
        if model_name not in self.known_models:
            self.known_models = [model_name, *self.known_models]
            self.model_menu.configure(values=self.known_models)

    def handle_action_response(self, data):
        action = data.get("action")
        success = data.get("success")
        payload = data.get("data", {})

        if success:
            if action == "get_status" and isinstance(payload, dict):
                self.apply_state(payload)
                return

            if action == "get_config" and isinstance(payload, dict):
                self.apply_state(payload)
                if payload.get("custom_models"):
                    self.update_model_catalog({"all": [*self.known_models, *payload.get("custom_models", [])]})
                if isinstance(payload.get("credentials"), dict):
                    self.update_api_key_catalog(payload.get("credentials"))
                return

            if action in {"get_api_keys", "add_api_key", "update_api_key", "delete_api_key", "select_api_key", "rotate_api_key"}:
                if isinstance(payload, dict):
                    self.update_api_key_catalog(payload)

                if action == "add_api_key":
                    self.append_technical_entry("system", "API key Gemini cadastrada com sucesso.")
                elif action == "update_api_key":
                    self.append_technical_entry("system", "API key Gemini atualizada com sucesso.")
                elif action == "delete_api_key":
                    self.append_technical_entry("system", "API key Gemini removida com sucesso.")
                elif action == "select_api_key":
                    self.append_technical_entry("system", "API key Gemini ativa alterada manualmente.")
                elif action == "rotate_api_key":
                    self.append_technical_entry("system", "Rotacao manual da API key Gemini concluida.")
                return

            if action in {"get_models", "change_model", "update_config"}:
                if isinstance(payload, dict) and "models" in payload:
                    self.update_model_catalog(payload.get("models"))
                elif action == "get_models":
                    self.update_model_catalog(payload)

                if isinstance(payload, dict) and payload.get("model"):
                    self.last_confirmed_model = payload["model"]
                    self.ensure_model_visible(self.last_confirmed_model)
                    self.model_var.set(self.last_confirmed_model)

                if action == "change_model":
                    confirmed_model = payload.get("model") if isinstance(payload, dict) else ""
                    self.append_technical_entry(
                        "system",
                        f"Troca manual de modelo confirmada com sucesso: {confirmed_model or self.model_var.get()}.",
                    )
                    self.pending_model_change = None
            return

        if action == "change_model" and self.last_confirmed_model:
            self.model_var.set(self.last_confirmed_model)
            failed_target = self.pending_model_change or self.last_confirmed_model
            self.append_technical_entry(
                "system",
                f"Falha na troca manual de modelo para {failed_target}: {data.get('error', 'erro nao informado')}",
            )
            self.pending_model_change = None
            return

        if action in {"add_api_key", "update_api_key", "delete_api_key", "select_api_key", "rotate_api_key"}:
            self.append_technical_entry("system", f"Falha na acao de API key: {data.get('error', 'erro nao informado')}")
            return

        self.append_technical_entry("system", data.get("error", "A acao falhou."))

    def clear_history_views(self):
        for block in self.conversation_blocks:
            block["frame"].destroy()
        for block in self.technical_blocks:
            block["frame"].destroy()
        self.conversation_blocks.clear()
        self.technical_blocks.clear()
        self.last_conversation_block = None
        self.last_technical_block = None

    def render_history(self, history):
        self.clear_history_views()
        for item in history:
            self.append_stream_entry(
                item.get("message_type"),
                item.get("content", ""),
                timestamp=item.get("timestamp"),
                merge_if_possible=True,
            )
        self.scroll_conversation_to_bottom(force=True)
        self.scroll_technical_to_bottom(force=True)

    def append_stream_entry(self, message_type, content, timestamp=None, merge_if_possible=True):
        if content is None:
            return
        content = str(content)
        if not content:
            return

        if message_type in USER_MESSAGE_TYPES:
            self.append_conversation_entry(
                message_type,
                content,
                timestamp=timestamp,
                merge_if_possible=merge_if_possible,
            )
        else:
            self.append_technical_entry(
                message_type,
                content,
                timestamp=timestamp,
                merge_if_possible=merge_if_possible,
            )

    def append_conversation_entry(self, message_type, content, timestamp=None, merge_if_possible=True):
        content = str(content)
        should_follow = self.should_follow_scroll(self.conversation_frame)
        timestamp_label = self.format_timestamp(timestamp or self.local_timestamp())
        if (
            merge_if_possible
            and self.last_conversation_block
            and self.last_conversation_block["message_type"] == message_type
        ):
            self.last_conversation_block["content"] += content
            self.update_text_widget(self.last_conversation_block["textbox"], self.last_conversation_block["content"])
            self.scroll_conversation_to_bottom(force=should_follow)
            return

        is_user = message_type == "user"
        header_text = "Voce" if is_user else "Mark"
        frame_color = "#1f4d44" if is_user else "#1b1f22"
        border_color = "#2fc18c" if is_user else "#d3b457"
        body_color = "#f4fbf9" if is_user else "#f7f7f2"
        header_color = "#d7e3e0" if is_user else "#f3e6a6"
        horizontal_padding = (190, 18) if is_user else (18, 190)
        sticky = "e" if is_user else "w"

        row_index = len(self.conversation_blocks)
        block_frame = ctk.CTkFrame(
            self.conversation_frame,
            corner_radius=6,
            fg_color=frame_color,
            border_width=1,
            border_color=border_color,
        )
        block_frame.grid(row=row_index, column=0, padx=horizontal_padding, pady=6, sticky=sticky)
        block_frame.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(block_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            header_frame,
            text=header_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
            text_color=header_color,
        )
        header.grid(row=0, column=0, sticky="w")

        header_time = ctk.CTkLabel(
            header_frame,
            text=timestamp_label,
            font=ctk.CTkFont(size=11),
            anchor="e",
            text_color="#9eaab3",
        )
        header_time.grid(row=0, column=1, padx=(10, 10), sticky="e")

        copy_btn = ctk.CTkButton(
            header_frame,
            text="Copiar",
            width=70,
            height=26,
            command=None,
            fg_color="#32404a",
            hover_color="#40515e",
        )
        copy_btn.grid(row=0, column=2, sticky="e")

        textbox = self.create_text_widget(
            block_frame,
            content,
            foreground=body_color,
            background=frame_color,
            font_size=14 if is_user else 15,
            monospace=False,
        )
        textbox.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")

        block = {
            "frame": block_frame,
            "textbox": textbox,
            "message_type": message_type,
            "content": content,
            "timestamp": timestamp_label,
        }
        copy_btn.configure(command=lambda block_ref=block: self.copy_to_clipboard(block_ref["content"]))
        self.conversation_blocks.append(block)
        self.last_conversation_block = block

        self.scroll_conversation_to_bottom(force=should_follow)

    def append_technical_entry(self, message_type, content, timestamp=None, merge_if_possible=True):
        if content is None:
            return
        content = str(content)
        if not content:
            return

        should_follow = self.should_follow_scroll(self.technical_frame)
        effective_type = message_type if message_type in TECHNICAL_HEADERS else "system"
        timestamp_label = self.format_timestamp(timestamp or self.local_timestamp())

        if (
            merge_if_possible
            and self.last_technical_block
            and self.last_technical_block["message_type"] == message_type
            and message_type in MERGEABLE_TECHNICAL_TYPES
        ):
            self.last_technical_block["content"] += content
            self.update_text_widget(self.last_technical_block["textbox"], self.last_technical_block["content"])
            self.scroll_technical_to_bottom(force=should_follow)
            return

        colors = {
            "status": ("#e9c46a", "#f3e3b0", "#16140d"),
            "system": ("#8bd3dd", "#d7e4e7", "#0f1417"),
            "code": ("#82d173", "#cbf3c2", "#162119"),
            "console": ("#f4a261", "#ffd7ba", "#261812"),
        }
        header_color, body_color, background = colors.get(effective_type, colors["system"])
        row_index = len(self.technical_blocks)

        block_frame = ctk.CTkFrame(
            self.technical_frame,
            corner_radius=6,
            fg_color="#11161a",
            border_width=1,
            border_color="#273038",
        )
        block_frame.grid(row=row_index, column=0, padx=6, pady=6, sticky="ew")
        block_frame.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(block_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            header_frame,
            text=TECHNICAL_HEADERS.get(message_type, "Fluxo"),
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
            text_color=header_color,
        )
        header.grid(row=0, column=0, sticky="w")

        header_time = ctk.CTkLabel(
            header_frame,
            text=timestamp_label,
            font=ctk.CTkFont(size=11),
            anchor="e",
            text_color="#9eaab3",
        )
        header_time.grid(row=0, column=1, padx=(10, 10), sticky="e")

        copy_btn = ctk.CTkButton(
            header_frame,
            text="Copiar",
            width=70,
            height=26,
            command=None,
            fg_color="#32404a",
            hover_color="#40515e",
        )
        copy_btn.grid(row=0, column=2, sticky="e")

        textbox = self.create_text_widget(
            block_frame,
            content,
            foreground=body_color,
            background=background,
            font_size=12 if effective_type in MERGEABLE_TECHNICAL_TYPES else 11,
            monospace=effective_type in MERGEABLE_TECHNICAL_TYPES,
        )
        textbox.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")

        block = {
            "frame": block_frame,
            "textbox": textbox,
            "message_type": message_type,
            "content": content,
            "timestamp": timestamp_label,
        }
        copy_btn.configure(command=lambda block_ref=block: self.copy_to_clipboard(block_ref["content"]))
        self.technical_blocks.append(block)
        self.last_technical_block = block
        self.scroll_technical_to_bottom(force=should_follow)

    def create_text_widget(self, parent, content, foreground, background, font_size, monospace=False):
        text_widget = tk.Text(
            parent,
            wrap="word",
            height=self.estimate_text_lines(content),
            bg=background,
            fg=foreground,
            relief="flat",
            bd=0,
            highlightthickness=0,
            insertbackground=foreground,
            selectbackground="#34536a",
            selectforeground="#ffffff",
            cursor="xterm",
            padx=0,
            pady=0,
        )
        if monospace:
            widget_font = tkfont.nametofont("TkFixedFont").copy()
            widget_font.configure(size=font_size)
        else:
            widget_font = tkfont.nametofont("TkDefaultFont").copy()
            widget_font.configure(size=font_size)
        text_widget.configure(font=widget_font)
        text_widget.insert("1.0", content)
        text_widget.configure(state="disabled")
        return text_widget

    def update_text_widget(self, widget, content):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(height=self.estimate_text_lines(content), state="disabled")

    def estimate_text_lines(self, content):
        content = str(content)
        lines = content.count("\n") + 1
        wrap_bonus = max(0, len(content) // 90)
        return max(2, min(18, lines + wrap_bonus))

    def get_scroll_canvas(self, scrollable_frame):
        return getattr(scrollable_frame, "_parent_canvas", None)

    def should_follow_scroll(self, scrollable_frame):
        canvas = self.get_scroll_canvas(scrollable_frame)
        if canvas is None:
            return True
        try:
            _, end = canvas.yview()
        except Exception:
            return True
        return end >= 1.0 - AUTO_SCROLL_THRESHOLD

    def scroll_conversation_to_bottom(self, force=True):
        if not force:
            return
        try:
            canvas = self.get_scroll_canvas(self.conversation_frame)
            if canvas is not None:
                canvas.update_idletasks()
                canvas.yview_moveto(1.0)
        except Exception:
            pass

    def scroll_technical_to_bottom(self, force=True):
        if not force:
            return
        try:
            canvas = self.get_scroll_canvas(self.technical_frame)
            if canvas is not None:
                canvas.update_idletasks()
                canvas.yview_moveto(1.0)
        except Exception:
            pass

    def is_conversation_at_bottom(self):
        return self.should_follow_scroll(self.conversation_frame)

    def is_technical_at_bottom(self):
        return self.should_follow_scroll(self.technical_frame)

    def is_backend_connected(self):
        return bool(self.async_loop and self.ws_client and self.ws_client.connected)

    def send_action_async(self, action, payload=None):
        if self.async_loop and self.ws_client and self.ws_client.connected:
            asyncio.run_coroutine_threadsafe(
                self.ws_client.send_action(action, payload),
                self.async_loop,
            )
            return True

        if self.connection_status == "reconnecting":
            self.append_technical_entry(
                "system",
                f"Falha temporaria de comunicacao em {self.backend_target_display()}. Aguarde a reconexao automatica para enviar novos comandos.",
            )
        else:
            self.append_technical_entry(
                "system",
                f"Backend indisponivel em {self.backend_target_display()}. Aguarde a reconexao para enviar comandos.",
            )
        return False

    def on_send(self):
        prompt = self.get_input_text().strip()
        if not prompt:
            return
        if self.send_action_async("execute_task", {"prompt": prompt}):
            self.clear_input_text()

    def on_mode_change(self, value):
        if not self.send_action_async("change_mode", {"mode": value}):
            self.mode_var.set(self.last_confirmed_mode)

    def on_model_change(self, value):
        if not value or value == self.last_confirmed_model:
            return
        self.pending_model_change = value
        if not self.send_action_async("change_model", {"model": value}) and self.last_confirmed_model:
            self.model_var.set(self.last_confirmed_model)
            self.pending_model_change = None

    def on_api_key_selected(self, selected_value):
        if self._syncing_api_key_menu:
            return
        selected_id = self.api_key_display_to_id.get(selected_value)
        if not selected_id:
            return
        if selected_id == self.api_key_catalog.get("active_key_id"):
            return
        self.send_action_async("select_api_key", {"id": selected_id})

    def on_add_api_key(self):
        if not self.is_backend_connected():
            self.append_technical_entry("system", "Conecte ao backend antes de cadastrar uma API key Gemini.")
            return

        label_dialog = ctk.CTkInputDialog(
            text="Nome da chave (opcional):",
            title="Cadastrar API key Gemini",
        )
        label_value = label_dialog.get_input()
        if label_value is None:
            return

        key_dialog = ctk.CTkInputDialog(
            text="Cole a API key Gemini (obrigatorio):",
            title="Cadastrar API key Gemini",
        )
        key_value = key_dialog.get_input()
        if key_value is None:
            return

        normalized_key = key_value.strip()
        if not normalized_key:
            self.append_technical_entry("system", "Cadastro cancelado: API key Gemini vazia.")
            return

        payload = {
            "label": (label_value or "").strip(),
            "key": normalized_key,
            "set_active": True,
        }
        self.send_action_async("add_api_key", payload)

    def on_edit_api_key(self):
        if not self.is_backend_connected():
            self.append_technical_entry("system", "Conecte ao backend antes de editar uma API key Gemini.")
            return

        selected_id = self.get_selected_api_key_id()
        if not selected_id:
            self.append_technical_entry("system", "Selecione uma API key Gemini persistida para editar.")
            return

        current_key = None
        for item in self.api_key_catalog.get("keys", []):
            if item.get("id") == selected_id:
                current_key = item
                break

        if current_key is None:
            self.append_technical_entry("system", "Chave selecionada nao encontrada no catalogo local.")
            return

        label_dialog = ctk.CTkInputDialog(
            text=(
                "Novo nome da chave (deixe vazio para manter):\n"
                f"Atual: {current_key.get('label', 'Gemini key')}"
            ),
            title="Editar API key Gemini",
        )
        new_label = label_dialog.get_input()
        if new_label is None:
            return

        key_dialog = ctk.CTkInputDialog(
            text="Nova API key (deixe vazio para manter a atual):",
            title="Editar API key Gemini",
        )
        new_key = key_dialog.get_input()
        if new_key is None:
            return

        payload = {"id": selected_id}
        if isinstance(new_label, str) and new_label.strip():
            payload["label"] = new_label.strip()
        if isinstance(new_key, str) and new_key.strip():
            payload["key"] = new_key.strip()

        if len(payload) == 1:
            self.append_technical_entry("system", "Edicao cancelada: nenhum campo foi alterado.")
            return

        self.send_action_async("update_api_key", payload)

    def on_rotate_api_key(self):
        if not self.is_backend_connected():
            self.append_technical_entry("system", "Conecte ao backend antes de rotacionar a API key Gemini.")
            return
        self.send_action_async("rotate_api_key")

    def on_add_model(self):
        if not self.is_backend_connected():
            self.append_technical_entry("system", "Conecte ao backend antes de adicionar um modelo Gemini.")
            return

        dialog = ctk.CTkInputDialog(
            text="Digite um modelo Gemini com prefixo gemini/:",
            title="Adicionar modelo Gemini",
        )
        value = dialog.get_input()
        if not value:
            return

        normalized = value.strip()
        if not normalized:
            return

        self.ensure_model_visible(normalized)
        self.model_var.set(normalized)
        self.pending_model_change = normalized
        if not self.send_action_async("change_model", {"model": normalized}) and self.last_confirmed_model:
            self.model_var.set(self.last_confirmed_model)
            self.pending_model_change = None

    def on_kill_switch(self):
        self.send_action_async("interrupt")

    def force_sync(self):
        if not self.is_backend_connected():
            self.append_technical_entry("system", "Sincronizacao indisponivel enquanto o backend nao estiver conectado.")
            return
        self.send_action_async("get_models")
        self.send_action_async("get_status")
        self.send_action_async("get_config")
        self.send_action_async("get_api_keys")

    def toggle_technical_panel(self):
        if self.technical_panel_collapsed:
            try:
                self.body_pane.add(self.technical_panel, stretch="never", minsize=150)
            except tk.TclError:
                pass
            self.technical_panel_collapsed = False
            self._technical_restore_requested = True
            self.toggle_technical_btn.configure(text="Ocultar painel tecnico")
            self.technical_collapse_btn.configure(text="Recolher")
            self.schedule_sash_positioning(force=True)
            return

        try:
            self.body_pane.forget(self.technical_panel)
        except tk.TclError:
            pass
        self.technical_panel_collapsed = True
        self.toggle_technical_btn.configure(text="Expandir painel tecnico")
        self.technical_collapse_btn.configure(text="Expandir")

    def copy_to_clipboard(self, content):
        if not content:
            return
        self.clipboard_clear()
        self.clipboard_append(str(content))

    def copy_all_technical_entries(self):
        payload = []
        for block in self.technical_blocks:
            header = TECHNICAL_HEADERS.get(block["message_type"], "Fluxo")
            payload.append(f"[{block['timestamp']}] {header}\n{block['content']}")
        self.copy_to_clipboard("\n\n".join(payload))

    def resolve_rules_paths(self):
        installed_root = Path(__file__).resolve().parents[1]
        default_rules_file = installed_root / "backend" / "product_config" / "initial_rules.txt"
        rules_file = Path(self.backend_paths.get("rules_file", default_rules_file))
        rules_dir = Path(self.backend_paths.get("rules_dir", rules_file.parent))
        return rules_file, rules_dir

    def open_rules_target(self):
        rules_file, rules_dir = self.resolve_rules_paths()
        if self.open_path_with_desktop(rules_file):
            self.append_technical_entry("system", f"Abrindo arquivo de regras: {rules_file}")
            return
        if self.open_path_with_desktop(rules_dir):
            self.append_technical_entry("system", f"Abrindo pasta das regras: {rules_dir}")
            return
        self.append_technical_entry(
            "system",
            f"Nao foi possivel abrir automaticamente o arquivo de regras. Caminho esperado: {rules_file}",
        )

    def open_rules_directory(self):
        _, rules_dir = self.resolve_rules_paths()
        if self.open_path_with_desktop(rules_dir):
            self.append_technical_entry("system", f"Abrindo pasta das regras: {rules_dir}")
            return
        self.append_technical_entry(
            "system",
            f"Nao foi possivel abrir automaticamente a pasta das regras. Caminho esperado: {rules_dir}",
        )

    def open_path_with_desktop(self, path):
        if not path.exists():
            return False

        launcher = shutil.which("xdg-open")
        command = [launcher, str(path)] if launcher else None
        if command is None:
            gio = shutil.which("gio")
            if gio:
                command = [gio, "open", str(path)]
        if command is None:
            return False

        try:
            subprocess.Popen(command)
            return True
        except Exception:
            return False

    def get_conversation_texts(self):
        return [block["content"] for block in self.conversation_blocks]

    @staticmethod
    def truncate_text(text, max_length):
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    @staticmethod
    def local_timestamp():
        return datetime.now().astimezone().isoformat(timespec="seconds")

    @staticmethod
    def format_timestamp(raw_timestamp):
        if not raw_timestamp:
            return "--:--:--"
        try:
            timestamp = datetime.fromisoformat(str(raw_timestamp))
        except ValueError:
            return str(raw_timestamp)
        return timestamp.astimezone().strftime("%H:%M:%S")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    app = JarvisApp()
    app.start_connection()
    app.mainloop()
