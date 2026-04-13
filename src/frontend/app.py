import customtkinter as ctk
import asyncio
import threading
import json
import os
import sys
from ws_client import JarvisWSClient

# Import das configs que definem a lista de modelos (podemos ler hardcoded se preferir, ou usar a requisicao get_models)
SUPPORTED_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229"
]

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Mark Alfa - Jarvis")
        self.geometry("900x650")
        
        # Configurar grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.ws_client = None
        self.async_loop = None
        
        self.build_sidebar()
        self.build_main_area()
        

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Mark Alfa", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="🔴 Desconectado", text_color="red")
        self.status_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        self.mode_var = ctk.StringVar(value="agent")
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["agent", "plan"], variable=self.mode_var, command=self.on_mode_change)
        self.mode_menu.grid(row=2, column=0, padx=20, pady=10)
        
        self.model_var = ctk.StringVar(value=SUPPORTED_MODELS[0])
        self.model_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=SUPPORTED_MODELS, variable=self.model_var, command=self.on_model_change)
        self.model_menu.grid(row=3, column=0, padx=20, pady=10)
        
        self.config_btn = ctk.CTkButton(self.sidebar_frame, text="Configurações", command=self.open_config_window)
        self.config_btn.grid(row=4, column=0, padx=20, pady=10)
        
        self.kill_btn = ctk.CTkButton(self.sidebar_frame, text="KILL SWITCH", fg_color="red", hover_color="darkred", command=self.on_kill_switch)
        self.kill_btn.grid(row=6, column=0, padx=20, pady=20)

    def open_config_window(self):
        if hasattr(self, "config_window") and self.config_window.winfo_exists():
            self.config_window.focus()
            return
            
        self.config_window = ctk.CTkToplevel(self)
        self.config_window.title("Configurações")
        self.config_window.geometry("400x300")
        self.config_window.transient(self)
        
        label = ctk.CTkLabel(self.config_window, text="Configurações do Mark Alfa", font=ctk.CTkFont(size=16, weight="bold"))
        label.pack(pady=20)
        
        info = ctk.CTkLabel(self.config_window, text="O ambiente Cloud e chaves são lidos\nautomaticamente pelo sistema.\n\nPara atualizar modelo ou modo,\nuse o menu principal.")
        info.pack(pady=10)
        
        btn = ctk.CTkButton(self.config_window, text="Sincronizar Estado", command=self.force_sync)
        btn.pack(pady=20)

    def force_sync(self):
        self.send_action_async("get_status")
        if hasattr(self, "config_window"):
            self.config_window.destroy()

    def build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        self.chat_box = ctk.CTkTextbox(self.main_frame, state="disabled", wrap="word")
        self.chat_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Digite sua tarefa ou prompt...")
        self.input_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.input_entry.bind("<Return>", lambda event: self.on_send())
        
        self.send_btn = ctk.CTkButton(self.input_frame, text="Enviar", width=80, command=self.on_send)
        self.send_btn.grid(row=0, column=1)

    def append_chat(self, prefix, message, text_color=None):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"[{prefix}] {message}\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def run_async_loop(self):
        self.async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.async_loop)
        
        self.ws_client = JarvisWSClient(ui_callback=self.handle_ws_message)
        self.ws_client.start(self.async_loop)
        
        self.async_loop.run_forever()

    def start_connection(self):
        threading.Thread(target=self.run_async_loop, daemon=True).start()

    def handle_ws_message(self, data):
        """Disparado via thread do asyncio, deve chamar atualizações de UI via after"""
        self.after(0, self._process_ws_message, data)
        
    def _process_ws_message(self, data):
        msg_type = data.get("type")
        
        if msg_type == "connection_status":
            if data["status"] == "connected":
                self.status_label.configure(text="🟢 Conectado", text_color="green")
                self.append_chat("System", "Conectado ao backend!")
            else:
                self.status_label.configure(text="🔴 Desconectado", text_color="red")
                
        elif msg_type == "sync_state":
            state = data.get("state", {})
            self.mode_var.set(state.get("mode", "agent"))
            self.model_var.set(state.get("model", "gemini-2.5-flash"))
            status = state.get("status", "idle")
            
            if status == "running":
                self.send_btn.configure(state="disabled")
            else:
                self.send_btn.configure(state="normal")
                
        elif msg_type == "stream":
            mtype = data.get("message_type")
            content = data.get("content", "")
            
            if mtype == "user":
                self.append_chat("Você", content)
            elif mtype == "message":
                self.append_chat("Jarvis", content)
            elif mtype == "status":
                self.append_chat("Status", content)
            elif mtype == "code":
                self.append_chat("Código", f"\n{content}\n")
            elif mtype == "console":
                self.append_chat("Console", f"\n{content}\n")
            elif mtype == "system":
                self.append_chat("Sistema", content)
                
        elif msg_type == "action_response":
            if not data.get("success"):
                self.append_chat("Erro", data.get("error", "Ação falhou"))

    def send_action_async(self, action, payload=None):
        if self.async_loop and self.ws_client:
            asyncio.run_coroutine_threadsafe(
                self.ws_client.send_action(action, payload), 
                self.async_loop
            )

    def on_send(self):
        text = self.input_entry.get().strip()
        if text:
            self.send_action_async("execute_task", {"prompt": text})
            self.input_entry.delete(0, "end")

    def on_mode_change(self, value):
        self.send_action_async("change_mode", {"mode": value})
        
    def on_model_change(self, value):
        self.send_action_async("change_model", {"model": value})

    def on_kill_switch(self):
        self.send_action_async("interrupt")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = JarvisApp()
    app.start_connection()
    app.mainloop()

