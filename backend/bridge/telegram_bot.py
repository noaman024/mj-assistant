import os
import asyncio
import logging
from backend.config.settings import USER_NAME, ASSISTANT_NAME
from backend.tools.system_control import system_control

logger = logging.getLogger("MJ.TelegramBridge")

class TelegramBridge:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.authorized_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.is_running = False

    async def handle_incoming_message(self, chat_id: str, text: str) -> str:
        """Processes message received via Telegram from Noaman"""
        if self.authorized_chat_id and str(chat_id) != str(self.authorized_chat_id):
            logger.warning(f"Unauthorized Telegram access attempt from chat_id: {chat_id}")
            return "Unauthorized access. Only Noaman can control MJ."

        logger.info(f"Telegram remote command: '{text}'")
        
        # Special Telegram action: Send live screenshot
        if any(w in text.lower() for w in ["screenshot", "screen photo", "screen dikhao"]):
            filepath, msg = system_control.take_screenshot()
            return f"{msg} (File: {filepath})"

        # Process normal orchestrator command
        from backend.core.orchestrator import orchestrator
        response = await orchestrator.process_command(text, source_device="telegram")
        return response

    def is_configured(self) -> bool:
        return bool(self.bot_token)

telegram_bridge = TelegramBridge()
