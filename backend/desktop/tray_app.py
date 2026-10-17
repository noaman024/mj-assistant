import sys
import os
import asyncio
import threading
import time
from pathlib import Path

# Add root directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import psutil
import customtkinter as ctk

from backend.config.settings import USER_NAME, ASSISTANT_NAME
from backend.core.orchestrator import orchestrator
from backend.core.diagnostics import diagnostics_engine
from backend.core.security import security_vault
from backend.core.skill_learner import skill_learner
from backend.voice.stt import stt

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MJDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{ASSISTANT_NAME} - Jarvis Autonomous Desktop Assistant")
        self.geometry("860x650")
        self.minsize(740, 520)

        # Background color
        self.configure(fg_color="#0d1117")

        # Voice & Recording States (Hands-Free active by default for 'Hey MJ' wake word)
        self.is_recording = False
        self.hands_free_active = True
        self.is_busy = False

        # Asyncio event loop for orchestrator in background thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

        self._build_ui()
        self._start_metrics_updater()
        self._start_hands_free_listener()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _build_ui(self):
        # Header Bar
        self.header_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=12)
        self.header_frame.pack(fill="x", padx=15, pady=(15, 8))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=f"⚡ {ASSISTANT_NAME} CORE // JARVIS OS",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#58a6ff"
        )
        self.title_label.pack(side="left", padx=16, pady=12)

        self.mic_badge = ctk.CTkLabel(
            self.header_frame,
            text="MIC: LISTENING (HEY MJ) 🟢",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#3fb950",
            fg_color="#1f242c",
            corner_radius=6,
            padx=10,
            pady=4
        )
        self.mic_badge.pack(side="right", padx=(0, 10), pady=12)

        self.user_badge = ctk.CTkLabel(
            self.header_frame,
            text=f"USER: {USER_NAME.upper()} (AUTHORIZED)",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#7ee787",
            fg_color="#1f242c",
            corner_radius=6,
            padx=10,
            pady=4
        )
        self.user_badge.pack(side="right", padx=(10, 8), pady=12)

        # Metrics Card Row
        self.metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_frame.pack(fill="x", padx=15, pady=6)
        self.metrics_frame.columnconfigure((0, 1, 2, 3), weight=1)

        # CPU Card
        self.cpu_card = ctk.CTkFrame(self.metrics_frame, fg_color="#161b22", corner_radius=8)
        self.cpu_card.grid(row=0, column=0, padx=4, sticky="ew")
        self.cpu_lbl = ctk.CTkLabel(self.cpu_card, text="CPU USAGE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#8b949e")
        self.cpu_lbl.pack(pady=(6, 0))
        self.cpu_val = ctk.CTkLabel(self.cpu_card, text="--%", font=ctk.CTkFont(size=16, weight="bold"), text_color="#38bdf8")
        self.cpu_val.pack(pady=(0, 6))

        # RAM Card
        self.ram_card = ctk.CTkFrame(self.metrics_frame, fg_color="#161b22", corner_radius=8)
        self.ram_card.grid(row=0, column=1, padx=4, sticky="ew")
        self.ram_lbl = ctk.CTkLabel(self.ram_card, text="RAM USAGE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#8b949e")
        self.ram_lbl.pack(pady=(6, 0))
        self.ram_val = ctk.CTkLabel(self.ram_card, text="--%", font=ctk.CTkFont(size=16, weight="bold"), text_color="#a855f7")
        self.ram_val.pack(pady=(0, 6))

        # Battery Card
        self.bat_card = ctk.CTkFrame(self.metrics_frame, fg_color="#161b22", corner_radius=8)
        self.bat_card.grid(row=0, column=2, padx=4, sticky="ew")
        self.bat_lbl = ctk.CTkLabel(self.bat_card, text="BATTERY", font=ctk.CTkFont(size=10, weight="bold"), text_color="#8b949e")
        self.bat_lbl.pack(pady=(6, 0))
        self.bat_val = ctk.CTkLabel(self.bat_card, text="--%", font=ctk.CTkFont(size=16, weight="bold"), text_color="#10b981")
        self.bat_val.pack(pady=(0, 6))

        # Vault Card
        self.sec_card = ctk.CTkFrame(self.metrics_frame, fg_color="#161b22", corner_radius=8)
        self.sec_card.grid(row=0, column=3, padx=4, sticky="ew")
        self.sec_lbl = ctk.CTkLabel(self.sec_card, text="SECURITY VAULT", font=ctk.CTkFont(size=10, weight="bold"), text_color="#8b949e")
        self.sec_lbl.pack(pady=(6, 0))
        self.sec_val = ctk.CTkLabel(self.sec_card, text="PROTECTED", font=ctk.CTkFont(size=16, weight="bold"), text_color="#f59e0b")
        self.sec_val.pack(pady=(0, 6))

        # Action Buttons Toolbar
        self.tools_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10)
        self.tools_frame.pack(fill="x", padx=15, pady=6)

        btn_font = ctk.CTkFont(size=12, weight="bold")
        
        self.btn_voice_toggle = ctk.CTkButton(
            self.tools_frame, text="🎙️ Hands-Free: ON", font=btn_font,
            fg_color="#238636", hover_color="#2ea043", text_color="#ffffff",
            command=self._toggle_hands_free
        )
        self.btn_voice_toggle.pack(side="left", padx=8, pady=8)

        self.btn_diag = ctk.CTkButton(
            self.tools_frame, text="🩺 Run Diagnostics", font=btn_font,
            fg_color="#21262d", hover_color="#30363d", text_color="#58a6ff",
            command=self._cmd_diagnostics
        )
        self.btn_diag.pack(side="left", padx=8, pady=8)

        self.btn_vault = ctk.CTkButton(
            self.tools_frame, text="🔒 Toggle Vault", font=btn_font,
            fg_color="#21262d", hover_color="#30363d", text_color="#f59e0b",
            command=self._cmd_toggle_vault
        )
        self.btn_vault.pack(side="left", padx=8, pady=8)

        self.btn_skills = ctk.CTkButton(
            self.tools_frame, text="🧠 Learned Skills", font=btn_font,
            fg_color="#21262d", hover_color="#30363d", text_color="#a855f7",
            command=self._cmd_skills
        )
        self.btn_skills.pack(side="left", padx=8, pady=8)

        self.btn_media = ctk.CTkButton(
            self.tools_frame, text="⏯ Play/Pause", font=btn_font,
            fg_color="#21262d", hover_color="#30363d", text_color="#10b981",
            command=self._cmd_play_pause
        )
        self.btn_media.pack(side="left", padx=8, pady=8)

        self.btn_zip = ctk.CTkButton(
            self.tools_frame, text="📦 Zip Storage", font=btn_font,
            fg_color="#21262d", hover_color="#30363d", text_color="#38bdf8",
            command=self._cmd_zip_backup
        )
        self.btn_zip.pack(side="left", padx=8, pady=8)

        # Log & Response Output Box
        self.log_box = ctk.CTkTextbox(
            self,
            fg_color="#090d13",
            text_color="#c9d1d9",
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=10,
            wrap="word"
        )
        self.log_box.pack(fill="both", expand=True, padx=15, pady=6)

        welcome_text = (
            f"=== {ASSISTANT_NAME} AUTONOMOUS DESKTOP INTERFACE INITIALIZED ===\n"
            f"[SYSTEM] User authenticated as: {USER_NAME}\n"
            f"[SYSTEM] All modules online: YouTube, Phone Dialer, WhatsApp, Storage Zip, Vision & Voice\n"
            f"[VOICE READY] Mic button niche add kar diya gaya hai! '🎤 Speak' daba kar boliye, ya '🎙️ Hands-Free Mic' ON karke direct bolte rahiye.\n\n"
        )
        self.log_box.insert("end", welcome_text)

        # Command Input Bar
        self.input_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10)
        self.input_frame.pack(fill="x", padx=15, pady=(6, 15))

        self.cmd_input = ctk.CTkEntry(
            self.input_frame,
            placeholder_text=f"Ask {ASSISTANT_NAME} anything (e.g. 'YouTube par alfaaz play karo', 'system check karo', 'call Rahul')...",
            font=ctk.CTkFont(size=13),
            fg_color="#0d1117",
            border_color="#30363d",
            height=42
        )
        self.cmd_input.pack(side="left", fill="x", expand=True, padx=(10, 8), pady=8)
        self.cmd_input.bind("<Return>", lambda e: self._on_submit_command())

        self.btn_mic = ctk.CTkButton(
            self.input_frame,
            text="🎤 Speak",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#238636",
            hover_color="#2ea043",
            width=95,
            height=42,
            command=self._on_click_mic
        )
        self.btn_mic.pack(side="right", padx=(0, 8), pady=8)

        self.btn_send = ctk.CTkButton(
            self.input_frame,
            text="EXECUTE",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            width=90,
            height=42,
            command=self._on_submit_command
        )
        self.btn_send.pack(side="right", padx=(0, 10), pady=8)

    def _append_log(self, prefix: str, message: str, color_tag: str = ""):
        self.log_box.insert("end", f"[{prefix}] {message}\n\n")
        self.log_box.see("end")

    def _start_metrics_updater(self):
        def update():
            while True:
                try:
                    cpu = psutil.cpu_percent(interval=0.5)
                    ram = psutil.virtual_memory().percent
                    battery = psutil.sensors_battery()
                    bat_str = f"{round(battery.percent)}%" if battery else "AC Power"

                    sec_str = "UNLOCKED" if security_vault.is_unlocked() else "LOCKED"
                    sec_col = "#10b981" if security_vault.is_unlocked() else "#f59e0b"

                    self.after(0, lambda c=cpu, r=ram, b=bat_str, s=sec_str, sc=sec_col: self._apply_metrics(c, r, b, s, sc))
                except Exception:
                    pass
                time.sleep(2)

        t = threading.Thread(target=update, daemon=True)
        t.start()

    def _apply_metrics(self, cpu, ram, bat, sec_status, sec_col):
        self.cpu_val.configure(text=f"{cpu}%")
        self.ram_val.configure(text=f"{ram}%")
        self.bat_val.configure(text=bat)
        self.sec_val.configure(text=sec_status, text_color=sec_col)

    def _on_submit_command(self):
        cmd = self.cmd_input.get().strip()
        if not cmd:
            return
        self.cmd_input.delete(0, "end")
        self._append_log(USER_NAME.upper(), cmd)

        async def run_cmd():
            self.is_busy = True
            try:
                res = await orchestrator.process_command(cmd)
                self.after(0, lambda: self._append_log(ASSISTANT_NAME.upper(), res))
            finally:
                self.is_busy = False

        asyncio.run_coroutine_threadsafe(run_cmd(), self.loop)

    def _on_click_mic(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.btn_mic.configure(text="🎙️ Sun Rahi Hu...", fg_color="#da3633", hover_color="#b62324")
        self.mic_badge.configure(text="MIC: RECORDING... 🔴", text_color="#f85149")
        self._append_log("SYSTEM", f"Mic active hai {USER_NAME}! Boliye, main sun rahi hu...")

        def listen_worker():
            try:
                stt.calibrate_noise(0.4)
                spoken = stt.listen_command(timeout=8.0)
            except Exception as e:
                spoken = ""

            def finish():
                self.is_recording = False
                self.btn_mic.configure(text="🎤 Speak", fg_color="#238636", hover_color="#2ea043")
                if self.hands_free_active:
                    self.mic_badge.configure(text="MIC: LISTENING 🟢", text_color="#3fb950")
                else:
                    self.mic_badge.configure(text="MIC: READY 🎙️", text_color="#38bdf8")

                if spoken:
                    self.cmd_input.delete(0, "end")
                    self.cmd_input.insert(0, spoken)
                    self._on_submit_command()
                else:
                    self._append_log("SYSTEM", "Aawaz detect nahi hui Noaman, mic button daba kar dobara boliye.")

            self.after(0, finish)

        threading.Thread(target=listen_worker, daemon=True).start()

    def _start_hands_free_listener(self):
        def hands_free_worker():
            stt.calibrate_noise(0.4)
            while self.hands_free_active:
                if self.is_busy or self.is_recording:
                    time.sleep(0.3)
                    continue
                try:
                    spoken = stt.listen_command(timeout=6.0)
                    if not self.hands_free_active:
                        break
                    if spoken:
                        def execute_voice(s=spoken):
                            self.cmd_input.delete(0, "end")
                            self.cmd_input.insert(0, s)
                            self._on_submit_command()
                        self.after(0, execute_voice)
                except Exception:
                    time.sleep(0.4)

        threading.Thread(target=hands_free_worker, daemon=True).start()

    def _toggle_hands_free(self):
        if not self.hands_free_active:
            self.hands_free_active = True
            self.btn_voice_toggle.configure(text="🎙️ Hands-Free: ON", fg_color="#238636", hover_color="#2ea043", text_color="#ffffff")
            self.mic_badge.configure(text="MIC: LISTENING (HEY MJ) 🟢", text_color="#3fb950")
            self._append_log("SYSTEM", f"Hands-Free Voice Mode ON ho gaya hai {USER_NAME}! Aap seedha 'Hey MJ' ya koi bhi command bol sakte hain.")
            self._start_hands_free_listener()
        else:
            self.hands_free_active = False
            self.btn_voice_toggle.configure(text="🎙️ Hands-Free Mic", fg_color="#21262d", hover_color="#30363d", text_color="#38bdf8")
            self.mic_badge.configure(text="MIC: STANDBY 🎙️", text_color="#8b949e")
            self._append_log("SYSTEM", "Hands-Free Voice Mode OFF kar diya hai Noaman.")

    def _cmd_diagnostics(self):
        self.cmd_input.delete(0, "end")
        self.cmd_input.insert(0, "system check karo")
        self._on_submit_command()

    def _cmd_toggle_vault(self):
        if security_vault.is_unlocked():
            res = security_vault.lock_vault()
            self._append_log(ASSISTANT_NAME.upper(), res)
        else:
            self.cmd_input.delete(0, "end")
            self.cmd_input.insert(0, "jarvis")
            self._on_submit_command()

    def _cmd_skills(self):
        self.cmd_input.delete(0, "end")
        self.cmd_input.insert(0, "kya seekha hai batao")
        self._on_submit_command()

    def _cmd_play_pause(self):
        self.cmd_input.delete(0, "end")
        self.cmd_input.insert(0, "pause gana")
        self._on_submit_command()

    def _cmd_zip_backup(self):
        self.cmd_input.delete(0, "end")
        self.cmd_input.insert(0, "data zip karo")
        self._on_submit_command()

def run_app():
    def _launch_server():
        try:
            import uvicorn
            from backend.bridge.server import app
            from backend.config.settings import API_PORT
            uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="warning")
        except Exception as e:
            pass

    threading.Thread(target=_launch_server, daemon=True).start()
    app = MJDesktopApp()
    app.mainloop()

if __name__ == "__main__":
    run_app()
