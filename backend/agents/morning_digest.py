"""
Morning Digest & Daily Briefing Agent for MJ Assistant.
Adapted from OpenJarvis morning_digest agent architecture:
Synthesizes system status, pending tasks, recent voicemails,
and weather/news into a natural spoken briefing for Noaman.
"""

import psutil
import logging
from datetime import datetime
from typing import Dict, Any, List

from backend.config.settings import USER_NAME, ASSISTANT_NAME
from backend.core.llm_engine import llm
from backend.core.memory import memory
from backend.call_screening import call_screener

logger = logging.getLogger("MJ.MorningDigest")


class MorningDigestAgent:
    def __init__(self):
        self.agent_id = "morning_digest"

    def collect_data(self) -> Dict[str, Any]:
        """Collects telemetry, tasks, voicemails, and system state."""
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")

        # 1. System Health
        battery = psutil.sensors_battery()
        batt_percent = battery.percent if battery else 100
        batt_plugged = battery.power_plugged if battery else True
        cpu_usage = psutil.cpu_percent(interval=None)
        ram_usage = psutil.virtual_memory().percent

        # 2. Notes & Tasks
        notes = memory.memory.get("notes", [])
        pending_notes = notes[-3:] if notes else []

        # 3. Screened Voicemails
        unread_vms = call_screener.get_unread_voicemails()
        vm_summaries = []
        for vm in unread_vms[:3]:
            vm_summaries.append(f"Call from {vm.get('caller_name', 'Unknown')}: {vm.get('summary', '')}")

        return {
            "date": date_str,
            "time": time_str,
            "cpu_percent": cpu_usage,
            "ram_percent": ram_usage,
            "battery_percent": batt_percent,
            "battery_plugged": batt_plugged,
            "pending_notes": pending_notes,
            "voicemails": vm_summaries
        }

    async def generate_briefing(self) -> str:
        """Synthesizes the morning digest into a warm, natural Hinglish briefing."""
        data = self.collect_data()

        prompt = f"""
You are {ASSISTANT_NAME}, a smart, loving, energetic personal female assistant and companion talking directly to {USER_NAME}.
Generate a crisp, spoken morning digest based on this collected data:

- Date & Time: {data['date']}, {data['time']}
- Laptop Health: CPU {data['cpu_percent']}%, RAM {data['ram_percent']}%, Battery {data['battery_percent']}% ({'charging' if data['battery_plugged'] else 'on battery'})
- Recent Notes/Tasks: {data['pending_notes'] if data['pending_notes'] else 'No pending to-dos'}
- Unread Screened Calls/Voicemails: {data['voicemails'] if data['voicemails'] else 'No missed calls'}

CRITICAL RULES:
1. Address the user ONLY as {USER_NAME}.
2. Tone: Warm, sweet, natural Indian girl voice ("kar rahi hu", "samajh gayi", "bata rahi hu").
3. MANDATORY: Say ALL numbers, percentages, and metrics strictly in ENGLISH (e.g. "eighty-five percent", "ten AM", "two missed calls", "zero issues"). Never use Hindi numbers like 'do', 'pachaas', etc.
4. Keep the entire briefing under 150 words so it is quick to listen to.
5. Highlight battery and tasks if any, and wish Noaman a super productive day ahead!
"""
        try:
            briefing = await llm.ask(prompt)
            return briefing.strip()
        except Exception as e:
            logger.error(f"Error generating briefing: {e}")
            return f"Good morning {USER_NAME}! Aaj {data['date']} hai, battery {data['battery_percent']} percent par hai aur laptop smooth chal raha hai. Have a wonderful day!"


# Global instance
morning_digest = MorningDigestAgent()
