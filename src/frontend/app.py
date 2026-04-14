import asyncio
import queue
import threading
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk

from ws_client import JarvisWSClient


ADD_MODEL_LABEL = "Adicionar Gemini..."
USER_MESSAGE_TYPES = {"user", "message"}
TECHNICAL_HEADERS = {
    "status": "Status",
    "system": "Sistema",
    "code": "Codigo",
    "console": "Console",
}


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mark Alfa")
        self.geometry("1120x760")
        self.minsize(940, 640)
        self.configure(fg_color="#121416")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.ws_client = None
        self.async_loop = None
        self.connection_status = "disconnected"
        self.known_models = []
        self.last_confirmed_model = ""
        self.last_confirmed_mode = "agent"
        self.conversation_blocks = []
        self.conversation_labels = []
        self.last_conversation_block = None
        self.last_technical_type = None
        self.message_queue = queue.SimpleQueue()

        self.build_sidebar()
        self.build_main_area()

        self.bind("<Configure>", self.on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(50, self.poll_ui_queue)

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#171a1c")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

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
            text="Backend desconectado",
            fg_color="#3a181d",
            text_color="#ffb4a2",
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

        self.kill_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Interromper",
            command=self.on_kill_switch,
            fg_color="#8c2f39",
            hover_color="#75262f",
        )
        self.kill_btn.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")

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

        self.conversation_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_button_color="#38444c",
            scrollbar_button_hover_color="#4b5962",
        )
        self.conversation_frame.grid(row=1, column=0, padx=18, sticky="nsew")
        self.conversation_frame.grid_columnconfigure(0, weight=1)

        self.technical_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.technical_frame.grid(row=2, column=0, padx=18, pady=(8, 0), sticky="ew")
        self.technical_frame.grid_columnconfigure(0, weight=1)

        self.technical_title = ctk.CTkLabel(
            self.technical_frame,
            text="Fluxo tecnico",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            text_color="#9eaab3",
        )
        self.technical_title.grid(row=0, column=0, pady=(0, 6), sticky="ew")

        self.technical_box = ctk.CTkTextbox(
            self.technical_frame,
            height=190,
            corner_radius=6,
            fg_color="#0f1214",
            border_width=1,
            border_color="#273038",
            wrap="word",
            state="disabled",
        )
        self.technical_box.grid(row=1, column=0, sticky="ew")
        self.configure_technical_tags()

        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=3, column=0, padx=18, pady=(14, 18), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Digite uma tarefa ou mensagem para o Mark...",
            height=40,
        )
        self.input_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.input_entry.bind("<Return>", lambda event: self.on_send())

        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Enviar",
            width=90,
            command=self.on_send,
            fg_color="#2c6b57",
            hover_color="#245545",
        )
        self.send_btn.grid(row=0, column=1)

    def configure_technical_tags(self):
        textbox = self.technical_box._textbox

        monospace = tkfont.nametofont("TkFixedFont").copy()
        monospace.configure(size=11)

        textbox.tag_configure(
            "status_header",
            foreground="#e9c46a",
            font=("TkDefaultFont", 11, "bold"),
            spacing1=10,
            spacing3=2,
        )
        textbox.tag_configure(
            "status_body",
            foreground="#f3e3b0",
            font=("TkDefaultFont", 11),
            lmargin1=14,
            lmargin2=14,
            spacing3=8,
        )
        textbox.tag_configure(
            "system_header",
            foreground="#8bd3dd",
            font=("TkDefaultFont", 11, "bold"),
            spacing1=10,
            spacing3=2,
        )
        textbox.tag_configure(
            "system_body",
            foreground="#d7e4e7",
            font=("TkDefaultFont", 11),
            lmargin1=14,
            lmargin2=14,
            spacing3=8,
        )
        textbox.tag_configure(
            "code_header",
            foreground="#82d173",
            font=("TkDefaultFont", 11, "bold"),
            spacing1=10,
            spacing3=2,
        )
        textbox.tag_configure(
            "code_body",
            foreground="#cbf3c2",
            background="#162119",
            font=monospace,
            lmargin1=14,
            lmargin2=14,
            spacing3=8,
        )
        textbox.tag_configure(
            "console_header",
            foreground="#f4a261",
            font=("TkDefaultFont", 11, "bold"),
            spacing1=10,
            spacing3=2,
        )
        textbox.tag_configure(
            "console_body",
            foreground="#ffd7ba",
            background="#261812",
            font=monospace,
            lmargin1=14,
            lmargin2=14,
            spacing3=8,
        )

    def on_window_resize(self, _event=None):
        self.after(50, self.update_message_wraplengths)

    def update_message_wraplengths(self):
        available_width = max(self.conversation_frame.winfo_width() - 220, 320)
        wraplength = int(available_width * 0.8)
        for label in self.conversation_labels:
            label.configure(wraplength=wraplength)

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
            self.apply_connection_status(data.get("status", "disconnected"))
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
            self.append_stream_entry(data.get("message_type"), data.get("content", ""))
            return

        if message_type == "action_response":
            self.handle_action_response(data)

    def apply_connection_status(self, status):
        previous_status = self.connection_status
        self.connection_status = status

        if status == "connected":
            self.connection_badge.configure(
                text="Backend conectado",
                fg_color="#1b4332",
                text_color="#d8f3dc",
            )
            if previous_status == "disconnected":
                self.append_technical_entry("system", "Conexao estabelecida com o backend.")
        else:
            self.connection_badge.configure(
                text="Backend desconectado",
                fg_color="#3a181d",
                text_color="#ffb4a2",
            )
            self.send_btn.configure(state="disabled")
            self.input_entry.configure(state="normal")
            if previous_status == "connected":
                self.append_technical_entry("system", "Conexao perdida. O frontend vai tentar reconectar.")

    def apply_state(self, state):
        self.last_confirmed_mode = state.get("mode", "agent")
        self.mode_var.set(self.last_confirmed_mode)

        current_model = state.get("model", self.last_confirmed_model)
        if current_model:
            self.ensure_model_visible(current_model)
            self.model_var.set(current_model)
            self.last_confirmed_model = current_model

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
            self.session_status.configure(text=f"Modelo ativo: {current_model or 'aguardando sincronizacao'}")

    def update_model_catalog(self, catalog):
        if isinstance(catalog, dict):
            model_values = catalog.get("all", [])
        else:
            model_values = catalog or []

        sanitized = [item for item in model_values if isinstance(item, str) and item]
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
                    self.update_model_catalog(
                        {
                            "all": [*self.known_models, *payload.get("custom_models", [])],
                        }
                    )
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
            block.destroy()
        self.conversation_blocks.clear()
        self.conversation_labels.clear()
        self.last_conversation_block = None
        self.last_technical_type = None

        self.technical_box.configure(state="normal")
        self.technical_box.delete("1.0", "end")
        self.technical_box.configure(state="disabled")

    def render_history(self, history):
        self.clear_history_views()
        for item in history:
            self.append_stream_entry(item.get("message_type"), item.get("content", ""), merge_if_possible=True)
        self.update_message_wraplengths()

    def append_stream_entry(self, message_type, content, merge_if_possible=True):
        if not content:
            return

        if message_type in USER_MESSAGE_TYPES:
            self.append_conversation_entry(message_type, content, merge_if_possible=merge_if_possible)
        else:
            self.append_technical_entry(message_type, content, merge_if_possible=merge_if_possible)

    def append_conversation_entry(self, message_type, content, merge_if_possible=True):
        if (
            merge_if_possible
            and self.last_conversation_block
            and self.last_conversation_block["message_type"] == message_type
        ):
            current_text = self.last_conversation_block["label"].cget("text")
            self.last_conversation_block["label"].configure(text=current_text + content)
            self.scroll_conversation_to_bottom()
            return

        is_user = message_type == "user"
        header_text = "Voce" if is_user else "Mark"
        frame_color = "#1f4d44" if is_user else "#1b1f22"
        border_color = "#2fc18c" if is_user else "#d3b457"
        body_color = "#f4fbf9" if is_user else "#f7f7f2"
        body_font = ctk.CTkFont(size=14 if is_user else 15, weight="normal")
        header_font = ctk.CTkFont(size=11, weight="bold")
        horizontal_padding = (150, 18) if is_user else (18, 150)
        sticky = "e" if is_user else "w"

        row_index = len(self.conversation_blocks)
        block = ctk.CTkFrame(
            self.conversation_frame,
            corner_radius=6,
            fg_color=frame_color,
            border_width=1,
            border_color=border_color,
        )
        block.grid(row=row_index, column=0, padx=horizontal_padding, pady=6, sticky=sticky)
        block.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            block,
            text=header_text,
            font=header_font,
            anchor="w",
            text_color="#d7e3e0" if is_user else "#f3e6a6",
        )
        header.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="ew")

        body = ctk.CTkLabel(
            block,
            text=content,
            justify="left",
            anchor="w",
            text_color=body_color,
            font=body_font,
            wraplength=540,
        )
        body.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")

        self.conversation_blocks.append(block)
        self.conversation_labels.append(body)
        self.last_conversation_block = {"message_type": message_type, "label": body}

        self.update_message_wraplengths()
        self.scroll_conversation_to_bottom()

    def append_technical_entry(self, message_type, content, merge_if_possible=True):
        if not content:
            return

        header_name = TECHNICAL_HEADERS.get(message_type, "Fluxo")
        header_tag = f"{message_type if message_type in TECHNICAL_HEADERS else 'system'}_header"
        body_tag = f"{message_type if message_type in TECHNICAL_HEADERS else 'system'}_body"

        self.technical_box.configure(state="normal")
        if (
            merge_if_possible
            and self.last_technical_type == message_type
            and message_type in {"code", "console"}
        ):
            self.technical_box.insert("end", f"{content}\n", body_tag)
        else:
            self.technical_box.insert("end", f"{header_name}\n", header_tag)
            self.technical_box.insert("end", f"{content}\n\n", body_tag)
        self.technical_box.configure(state="disabled")
        self.technical_box.see("end")
        self.last_technical_type = message_type

    def scroll_conversation_to_bottom(self):
        try:
            self.conversation_frame._parent_canvas.yview_moveto(1.0)
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
        else:
            self.append_technical_entry("system", "Backend desconectado. Aguarde a reconexao para enviar comandos.")
            return False

    def on_send(self):
        prompt = self.input_entry.get().strip()
        if not prompt:
            return
        self.send_action_async("execute_task", {"prompt": prompt})
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
            self.append_technical_entry("system", "Backend desconectado. Sincronizacao indisponivel no momento.")
            return
        self.send_action_async("get_models")
        self.send_action_async("get_status")

    @staticmethod
    def truncate_text(text, max_length):
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    app = JarvisApp()
    app.start_connection()
    app.mainloop()
