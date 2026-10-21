"""
Centralized Automation Engine for MJ Assistant (JARVIS-Grade).
Coordinates:
- Windows Desktop Actuation (Processes, Apps, Files, Settings)
- IoT Smart Home Actuation (REST / MQTT)
- Pre-Execution Vocal Announcements & Post-Execution Confirmations
- Multi-Step Macros (Morning Routine, Workstation Lockdown, Focus Mode)
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
from typing import Dict, Any, List, Optional

from backend.config.settings import USER_NAME, ASSISTANT_NAME, DATA_DIR
from backend.tools.system_control import system_control
from backend.tools.app_launcher import app_launcher
from backend.tools.file_manager import file_manager
from backend.tools.iot_controller import iot_controller

logger = logging.getLogger("MJ.AutomationEngine")


class AutomationEngine:
    def __init__(self):
        self.macros = {
            "lockdown": {
                "name": "Workstation Lockdown",
                "pre_announce": f"Workstation lockdown initiate kar rahi hu {USER_NAME}...",
                "actions": [
                    {"type": "system", "action": "minimize_all"},
                    {"type": "iot", "device": "bedroom_light", "action": "off"},
                    {"type": "system", "action": "lock_pc"}
                ],
                "post_confirm": f"Workstation successfully locked and lights turned off, {USER_NAME}."
            },
            "focus_mode": {
                "name": "Focus Mode",
                "pre_announce": f"Focus mode active kar rahi hu {USER_NAME}...",
                "actions": [
                    {"type": "system", "action": "minimize_all"},
                    {"type": "app", "name": "code"},
                    {"type": "iot", "device": "desk_lamp", "action": "on"}
                ],
                "post_confirm": f"Focus mode active hai {USER_NAME}. Code editor open hai aur desk lamp on hai."
            },
            "morning_routine": {
                "name": "Morning Routine",
                "pre_announce": f"Morning initialization start kar rahi hu {USER_NAME}...",
                "actions": [
                    {"type": "iot", "device": "bedroom_light", "action": "on"},
                    {"type": "iot", "device": "smart_plug", "action": "on"},
                    {"type": "app", "name": "chrome"}
                ],
                "post_confirm": f"Good morning {USER_NAME}! Systems are primed and ready."
            }
        }

    async def execute_macro(self, macro_name: str) -> Dict[str, Any]:
        """Executes a multi-action automation macro with pre/post announcements"""
        macro = self.macros.get(macro_name.lower().strip())
        if not macro:
            return {"success": False, "message": f"Macro '{macro_name}' nahi mila {USER_NAME}."}

        results = []
        for step in macro["actions"]:
            step_type = step.get("type")
            if step_type == "system":
                act = step.get("action")
                func = getattr(system_control, act, None)
                if func:
                    results.append(func())
            elif step_type == "app":
                results.append(app_launcher.launch(step.get("name")))
            elif step_type == "iot":
                res = await iot_controller.execute_action(step.get("device"), step.get("action"), step.get("value"))
                results.append(res.get("message"))
            await asyncio.sleep(0.3)

        return {
            "success": True,
            "macro": macro["name"],
            "pre_announce": macro["pre_announce"],
            "post_confirm": macro["post_confirm"],
            "results": results
        }

    def execute_powershell(self, script: str) -> Dict[str, Any]:
        """Executes a system PowerShell command safely"""
        try:
            logger.info(f"Executing PowerShell automation: {script[:80]}...")
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=15
            )
            return {
                "success": proc.returncode == 0,
                "output": proc.stdout.strip(),
                "error": proc.stderr.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_task_with_vocal_loop(self, task_type: str, params: Dict[str, Any], tts_engine) -> str:
        """
        JARVIS Vocal Feedback & Confirmation Loop:
        1. Pre-Execution Announcement via TTS
        2. Execute Task / Script
        3. Post-Execution Confirmation via TTS
        """
        pre_announcement = ""
        post_confirmation = ""

        if task_type == "lock_pc":
            pre_announcement = f"Workstation lock kar rahi hu {USER_NAME}."
            await tts_engine.speak(pre_announcement)
            system_control.lock_pc()
            post_confirmation = "Workstation locked."
            return post_confirmation

        elif task_type == "app_launch":
            app_name = params.get("app_name", "app")
            pre_announcement = f"{app_name.capitalize()} open kar rahi hu {USER_NAME}..."
            await tts_engine.speak(pre_announcement)
            res = app_launcher.launch(app_name, target=params.get("target", "laptop"))
            post_confirmation = res
            await tts_engine.speak(post_confirmation)
            return post_confirmation

        elif task_type == "system_scan":
            pre_announcement = f"System diagnostics scan initiate kar rahi hu {USER_NAME}..."
            await tts_engine.speak(pre_announcement)
            from backend.core.diagnostics import diagnostics_engine
            res = diagnostics_engine.get_spoken_advisory_report()
            post_confirmation = res
            await tts_engine.speak(post_confirmation)
            return post_confirmation

        elif task_type == "iot_control":
            device_id = params.get("device")
            action = params.get("action")
            pre_announcement = f"{device_id.replace('_', ' ').capitalize()} ko {action} kar rahi hu {USER_NAME}..."
            await tts_engine.speak(pre_announcement)
            res_dict = await iot_controller.execute_action(device_id, action)
            post_confirmation = res_dict.get("message", "Task complete.")
            await tts_engine.speak(post_confirmation)
            return post_confirmation

        # Default fallback
        return "Task executed."


# Global Singleton Instance
automation_engine = AutomationEngine()
