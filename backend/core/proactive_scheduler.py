"""
Autonomous Task Scheduler & System Event Listener for MJ Assistant (JARVIS-Grade).
Features:
- Dynamic Cron & Interval Task Scheduler (add, remove, list tasks)
- Autonomous Background Health Watchdogs:
    1. Low Battery Watchdog (< 20% unplugged alert)
    2. Power Cable Connect/Disconnect Event Listener
    3. High Resource Spike Alert (CPU > 90% or RAM > 92%)
    4. Low Disk Storage Warning (Drive C: free space < 10 GB)
    5. Scheduled Daily Briefing (09:00 AM)
    6. Scheduled Automated Storage Backup (11:00 PM)
- Proactive Vocal Feedback & HUD WebSocket Event Broadcasting
"""

import time
import shutil
import asyncio
import logging
import psutil
from datetime import datetime
from typing import Callable, List, Dict, Any, Optional

from backend.config.settings import USER_NAME, ASSISTANT_NAME

logger = logging.getLogger("MJ.Scheduler")


class AutonomousScheduler:
    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_battery_alert: int = 100
        self.last_power_state: Optional[bool] = None
        self.last_briefing_date: str = ""
        self.last_backup_date: str = ""
        
        # Dynamic Scheduled Tasks: id -> {name, interval_sec, last_run, handler, vocal_announce}
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.event_listeners: List[Callable] = []

    def register_task(self, task_id: str, name: str, interval_sec: int, handler: Callable, vocal_announce: bool = False):
        """Registers a dynamic background periodic task"""
        self.scheduled_tasks[task_id] = {
            "id": task_id,
            "name": name,
            "interval_sec": interval_sec,
            "last_run": time.time(),
            "handler": handler,
            "vocal_announce": vocal_announce,
            "status": "active"
        }
        logger.info(f"Registered autonomous task: '{name}' (every {interval_sec}s)")

    def unregister_task(self, task_id: str) -> bool:
        """Removes a dynamic scheduled task"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            return True
        return False

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Returns metadata for all active scheduled tasks"""
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "interval_sec": t["interval_sec"],
                "last_run": datetime.fromtimestamp(t["last_run"]).strftime("%H:%M:%S"),
                "status": t["status"]
            }
            for t in self.scheduled_tasks.values()
        ]

    async def start(self):
        """Starts the autonomous background monitor loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("MJ Autonomous Scheduler & Event Listener started.")

    async def stop(self):
        """Stops the scheduler gracefully."""
        self.is_running = False
        if self._task:
            self._task.cancel()

    async def _monitor_loop(self):
        """Periodic background tick every 30 seconds."""
        while self.is_running:
            try:
                await self._check_power_and_battery()
                await self._check_system_resources()
                await self._check_disk_space()
                await self._check_scheduled_routines()
                await self._run_dynamic_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler tick: {e}")

            await asyncio.sleep(30)

    async def _check_power_and_battery(self):
        """Monitors battery level and power plug/unplug events"""
        battery = psutil.sensors_battery()
        if not battery:
            return

        percent = battery.percent
        is_plugged = battery.power_plugged

        # 1. Power State Change Event
        if self.last_power_state is not None and self.last_power_state != is_plugged:
            from backend.bridge.phone_hub import phone_hub
            from backend.voice.tts import tts
            if is_plugged:
                msg = f"Charger connect ho gaya hai {USER_NAME}. Charging shuru ho gayi hai."
            else:
                msg = f"Charger disconnect ho gaya hai {USER_NAME}. System battery power par chal raha hai."
            
            logger.info(msg)
            await phone_hub.broadcast_event({"type": "power_event", "plugged": is_plugged, "message": msg})
            await tts.speak(msg)

        self.last_power_state = is_plugged

        # 2. Critical Battery Warning (< 20%)
        if not is_plugged and percent <= 20 and self.last_battery_alert > 20:
            self.last_battery_alert = percent
            from backend.bridge.phone_hub import phone_hub
            from backend.voice.tts import tts
            alert_msg = f"Battery alert: {percent} percent bachi hai {USER_NAME}. Kripya charger connect karein."
            logger.warning(alert_msg)
            await phone_hub.broadcast_event({"type": "battery_alert", "percent": percent, "message": alert_msg})
            await tts.speak(alert_msg)
        elif is_plugged:
            self.last_battery_alert = 100

    async def _check_system_resources(self):
        """Checks for sustained CPU or RAM resource spikes (> 90%)"""
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        if cpu > 92 or ram > 94:
            from backend.bridge.phone_hub import phone_hub
            alert_msg = f"System load high hai: CPU {cpu} percent, RAM {ram} percent."
            logger.warning(alert_msg)
            await phone_hub.broadcast_event({"type": "resource_warning", "cpu": cpu, "ram": ram, "message": alert_msg})

    async def _check_disk_space(self):
        """Monitors C: drive storage and alerts if less than 10GB free"""
        try:
            usage = shutil.disk_usage("C:\\")
            free_gb = usage.free / (1024 ** 3)
            if free_gb < 10.0:
                from backend.bridge.phone_hub import phone_hub
                from backend.voice.tts import tts
                msg = f"Storage warning: C drive me sirf {free_gb:.1f} GB space bachi hai {USER_NAME}."
                await phone_hub.broadcast_event({"type": "disk_warning", "free_gb": free_gb, "message": msg})
        except Exception:
            pass

    async def _check_scheduled_routines(self):
        """Executes scheduled daily briefing at 9:00 AM and data backup at 11:00 PM"""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # 9:00 AM Morning Digest
        if now.hour == 9 and now.minute == 0 and self.last_briefing_date != today_str:
            self.last_briefing_date = today_str
            logger.info("Executing 09:00 AM Morning Digest...")
            try:
                from backend.agents.morning_digest import morning_digest
                from backend.bridge.phone_hub import phone_hub
                from backend.voice.tts import tts
                briefing_text = await morning_digest.generate_briefing()
                await phone_hub.broadcast_event({"type": "morning_digest", "briefing": briefing_text})
                await tts.speak(briefing_text)
            except Exception as e:
                logger.error(f"Scheduled morning digest error: {e}")

        # 11:00 PM Maintenance & Backup
        if now.hour == 23 and now.minute == 0 and self.last_backup_date != today_str:
            self.last_backup_date = today_str
            logger.info("Executing 23:00 Night Storage Maintenance...")
            try:
                from backend.tools.compression_manager import compression_manager
                compression_manager.create_data_backup()
            except Exception as e:
                logger.error(f"Scheduled backup error: {e}")

    async def _run_dynamic_tasks(self):
        """Runs registered user background tasks based on interval"""
        now = time.time()
        for t_id, task in list(self.scheduled_tasks.items()):
            if now - task["last_run"] >= task["interval_sec"]:
                task["last_run"] = now
                try:
                    handler = task["handler"]
                    if asyncio.iscoroutinefunction(handler):
                        res = await handler()
                    else:
                        res = handler()
                    
                    if task.get("vocal_announce") and res:
                        from backend.voice.tts import tts
                        await tts.speak(str(res))
                except Exception as e:
                    logger.error(f"Error executing task '{task['name']}': {e}")


# Global Singleton Instance
proactive_scheduler = AutonomousScheduler()
