"""
Proactive Scheduler & Autonomous Task Operative for MJ Assistant.
Adapted from OpenJarvis monitor_operative.py & scheduler.py:
Runs background periodic monitors, battery warnings, automated memory
maintenance, and scheduled daily briefings.
"""

import asyncio
import logging
import psutil
from datetime import datetime
from typing import Callable, List, Dict, Any

from backend.config.settings import USER_NAME, ASSISTANT_NAME

logger = logging.getLogger("MJ.Scheduler")


class ProactiveScheduler:
    def __init__(self):
        self.is_running = False
        self._task: asyncio.Task = None
        self.last_battery_alert: int = 100
        self.last_briefing_date: str = ""

    async def start(self):
        """Starts the autonomous background monitor loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("MJ Proactive Scheduler running in background.")

    async def stop(self):
        """Stops the scheduler gracefully."""
        self.is_running = False
        if self._task:
            self._task.cancel()

    async def _monitor_loop(self):
        """Periodic background tick every 60 seconds."""
        while self.is_running:
            try:
                await self._check_battery()
                await self._check_scheduled_digest()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler tick: {e}")

            await asyncio.sleep(60)

    async def _check_battery(self):
        """Monitors laptop battery and alerts if dropping below 20%."""
        battery = psutil.sensors_battery()
        if not battery:
            return

        percent = battery.percent
        is_plugged = battery.power_plugged

        if not is_plugged and percent <= 20 and self.last_battery_alert > 20:
            self.last_battery_alert = percent
            from backend.bridge.phone_hub import phone_hub
            alert_msg = f"Battery warning: {percent} percent bachi hai Noaman. Charger connect kar lijiye."
            logger.warning(alert_msg)
            await phone_hub.broadcast_event({"type": "battery_alert", "percent": percent, "message": alert_msg})
        elif is_plugged:
            self.last_battery_alert = 100

    async def _check_scheduled_digest(self):
        """Checks if it's 9:00 AM and triggers the morning digest automatically once per day."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        if now.hour == 9 and now.minute == 0 and self.last_briefing_date != today_str:
            self.last_briefing_date = today_str
            logger.info("Triggering scheduled morning briefing at 9:00 AM...")
            try:
                from backend.agents.morning_digest import morning_digest
                from backend.bridge.phone_hub import phone_hub
                briefing_text = await morning_digest.generate_briefing()
                await phone_hub.broadcast_event({
                    "type": "morning_digest",
                    "briefing": briefing_text
                })
            except Exception as e:
                logger.error(f"Scheduled digest error: {e}")


# Global instance
proactive_scheduler = ProactiveScheduler()
