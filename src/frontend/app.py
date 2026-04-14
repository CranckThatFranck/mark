import asyncio
from datetime import datetime
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk

from ws_client import JarvisWSClient


ADD_MODEL_LABEL = "Adicionar Gemini..."
USER_MESSAGE_TYPES = {"user", "message"}
MERGEABLE_TECHNICAL_TYPES = {"code", "console"}
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

        self.ws_client = None
        self.async_loop = None
        self.connection_status = "disconnected"
        self.connection_detail = ""
        self.known_models = []
        self.last_confirmed_model = ""
        self.last_confirmed_mode = "agent"
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

        self.build_sidebar()
        self.build_main_area()

        self.bind("<Configure>", self.on_window_resize)
        self.bind("<Control-Shift-R>", lambda _event: self.open_rules_target())
        self.bind("<Control-Shift-T>", lambda _event: self.toggle_technical_panel())
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(50, self.poll_ui_queue)

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#171a1c")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(11, weight=1)

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

        self.mode_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Modo",
            font=section_font,
            anchor="w",
            text_color="#c7d0d9",
        )
        self.mode_label.grid(row=2, column=0, padx=20, pady=(0, 6), sticky="ew")

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
        self.mode_menu.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")

        self.model_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Modelo Gemini",
            font=section_font,
            anchor="w",
            text_color="#c7d0d9",
        )
        self.model_label.grid(row=4, column=0, padx=20, pady=(0, 6), sticky="ew")

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
        self.model_menu.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.add_model_btn = ctk.CTkButton(
            self.sidebar_frame,
            text=ADD_MODEL_LABEL,
            command=self.on_add_model,
            fg_color="#6b4f1f",
            hover_color="#825e24",
        )
        self.add_model_btn.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.sync_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Sincronizar",
            command=self.force_sync,
            fg_color="#25353f",
            hover_color="#2d4655",
        )
        self.sync_btn.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.rules_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Abrir regras",
            command=self.open_rules_target,
            fg_color="#3d3450",
            hover_color="#4d4266",
        )
        self.rules_btn.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.rules_dir_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Abrir pasta das regras",
            command=self.open_rules_directory,
            fg_color="#2b313d",
            hover_color="#384253",
        )
        self.rules_dir_btn.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.toggle_technical_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Ocultar painel tecnico",
            command=self.toggle_technical_panel,
            fg_color="#31414a",
            hover_color="#3b4f59",
        )
        self.toggle_technical_btn.grid(row=10, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.kill_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Interromper",
            command=self.on_kill_switch,
            fg_color="#8c2f39",
            hover_color="#75262f",
        )
        self.kill_btn.grid(row=12, column=0, padx=20, pady=(0, 20), sticky="ew")

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

        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Digite uma tarefa ou mensagem para o Mark...",
            height=40,
        )
        self.input_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.input_entry.bind("<Return>", lambda _event: self.on_send())

        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Enviar",
            width=90,
            command=self.on_send,
            fg_color="#2c6b57",
            hover_color="#245545",
        )
        self.send_btn.grid(row=0, column=1)

        self.after(150, self.position_initial_sash)

    def on_window_resize(self, _event=None):
        if not self.technical_panel_collapsed and self._technical_restore_requested:
            self.after(100, self.position_initial_sash)

    def position_initial_sash(self):
        if self.technical_panel_collapsed:
            return
        if self._sash_initialized and not self._technical_restore_requested:
            return
        try:
            total_height = self.body_pane.winfo_height()
            if total_height <= 0:
                return
            conversation_height = max(360, total_height - 240)
            self.body_pane.sash_place(0, 0, conversation_height)
            self._sash_initialized = True
            self._technical_restore_requested = False
        except Exception:
            pass

    def run_async_loop(self):
        self.async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.async_loop)

        try:
            self.ws_client = JarvisWSClient(ui_callback=self.handle_ws_message)
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

    def on_close(self):
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
        self.message_queue.put(data)

    def poll_ui_queue(self):
        try:
            while True:
                payload = self.message_queue.get_nowait()
                self.process_ws_message(payload)
        except queue.Empty:
            pass

        if self.winfo_exists():
            self.after(50, self.poll_ui_queue)

    def process_ws_message(self, data):
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

    def apply_connection_status(self, payload):
        status = payload.get("status", "disconnected") if isinstance(payload, dict) else str(payload)
        detail = payload.get("detail", "") if isinstance(payload, dict) else ""
        recovered = bool(payload.get("recovered")) if isinstance(payload, dict) else False
        attempt = payload.get("attempt") if isinstance(payload, dict) else None

        previous_status = self.connection_status
        self.connection_status = status
        self.connection_detail = detail

        style = CONNECTION_STYLES.get(status, CONNECTION_STYLES["disconnected"])
        self.connection_badge.configure(
            text=style["badge"],
            fg_color=style["fg"],
            text_color=style["text"],
        )

        self.send_btn.configure(state="normal" if status == "connected" else "disabled")
        if status != "connected":
            self.input_entry.configure(state="normal")

        notice_key = (status, detail, attempt)
        if notice_key == self._last_connection_notice:
            return

        if status == "connected":
            message = "Conexao com o backend restabelecida." if recovered else "Conexao estabelecida com o backend."
            self.append_technical_entry("system", message)
            self._last_connection_notice = ("connected", "", None)
            return

        if status == "reconnecting":
            message = "Falha temporaria de comunicacao. Tentando reconectar automaticamente."
            if detail:
                message = f"{message} Detalhe: {detail}."
            self.append_technical_entry("system", message)
        elif status == "unavailable":
            message = "Backend indisponivel no momento. O frontend continuara tentando conectar."
            if detail:
                message = f"{message} Detalhe: {detail}."
            self.append_technical_entry("system", message)
        elif previous_status == "connected":
            self.append_technical_entry("system", "Conexao encerrada pelo cliente.")

        self._last_connection_notice = notice_key

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

        status = state.get("status", "idle")
        active_task = state.get("active_task")
        if status == "running":
            self.send_btn.configure(state="disabled")
            self.input_entry.configure(state="disabled")
            if active_task:
                self.session_status.configure(text=f"Executando: {self.truncate_text(active_task, 140)}")
            else:
                self.session_status.configure(text="Executando tarefa em andamento")
        else:
            self.send_btn.configure(state="normal" if self.connection_status == "connected" else "disabled")
            self.input_entry.configure(state="normal")
            base_text = f"Modelo ativo: {current_model or 'aguardando sincronizacao'}"
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
            return

        if action == "change_model" and self.last_confirmed_model:
            self.model_var.set(self.last_confirmed_model)
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
        self.scroll_conversation_to_bottom()
        self.scroll_technical_to_bottom()

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
        timestamp_label = self.format_timestamp(timestamp or self.local_timestamp())
        if (
            merge_if_possible
            and self.last_conversation_block
            and self.last_conversation_block["message_type"] == message_type
        ):
            self.last_conversation_block["content"] += content
            self.update_text_widget(self.last_conversation_block["textbox"], self.last_conversation_block["content"])
            self.scroll_conversation_to_bottom()
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

        self.scroll_conversation_to_bottom()

    def append_technical_entry(self, message_type, content, timestamp=None, merge_if_possible=True):
        if content is None:
            return
        content = str(content)
        if not content:
            return

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
            self.scroll_technical_to_bottom()
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
        self.scroll_technical_to_bottom()

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

    def scroll_conversation_to_bottom(self):
        try:
            self.conversation_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def scroll_technical_to_bottom(self):
        try:
            self.technical_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

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
                "Falha temporaria de comunicacao em andamento. Aguarde a reconexao automatica para enviar novos comandos.",
            )
        else:
            self.append_technical_entry(
                "system",
                "Backend indisponivel. Aguarde a reconexao para enviar comandos.",
            )
        return False

    def on_send(self):
        prompt = self.input_entry.get().strip()
        if not prompt:
            return
        if self.send_action_async("execute_task", {"prompt": prompt}):
            self.input_entry.delete(0, "end")

    def on_mode_change(self, value):
        if not self.send_action_async("change_mode", {"mode": value}):
            self.mode_var.set(self.last_confirmed_mode)

    def on_model_change(self, value):
        if not self.send_action_async("change_model", {"model": value}) and self.last_confirmed_model:
            self.model_var.set(self.last_confirmed_model)

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
        if not self.send_action_async("change_model", {"model": normalized}) and self.last_confirmed_model:
            self.model_var.set(self.last_confirmed_model)

    def on_kill_switch(self):
        self.send_action_async("interrupt")

    def force_sync(self):
        if not self.is_backend_connected():
            self.append_technical_entry("system", "Sincronizacao indisponivel enquanto o backend nao estiver conectado.")
            return
        self.send_action_async("get_models")
        self.send_action_async("get_status")

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
            self.after(150, self.position_initial_sash)
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
