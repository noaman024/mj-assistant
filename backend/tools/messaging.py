import os
import re
import webbrowser
import urllib.parse
import logging
from backend.tools.contact_manager import contact_manager

logger = logging.getLogger("MJ.Messaging")

class MessageAutomator:
    def __init__(self):
        self.pending_message = None
        self.awaiting_message_for = None  # Contact name awaiting message text

    def prepare_whatsapp_message(self, recipient_name: str, message_text: str = "") -> tuple[bool, str, dict]:
        """Looks up contact and prepares WhatsApp message payload"""
        clean_name = recipient_name.strip()
        for w in ["whatsapp", "par", "pe", "ko", "se", "message", "msg", "bolo", "karo", "bhejo"]:
            clean_name = re.sub(rf"\b{w}\b", "", clean_name, flags=re.IGNORECASE).strip()

        contact = contact_manager.find_contact(clean_name)

        if not contact or not contact.get("phone"):
            # Check if clean_name itself has digits
            digits = re.sub(r"[^\d+]", "", clean_name)
            if len(digits) >= 10:
                contact = {"name": digits, "phone": digits}
            else:
                return False, f"'{clean_name}' ka phone number save nahi hai Noaman. Kripya pehle unka number batayein.", {}

        phone = contact.get("phone", "").replace("+", "").replace(" ", "").replace("-", "")
        if len(phone) == 10:
            phone = "91" + phone

        # If user didn't provide message text yet, ask for it
        if not message_text.strip():
            self.awaiting_message_for = contact["name"]
            return False, f"Haan Noaman, {contact['name']} ko kya WhatsApp message bhejna hai?", {}

        payload = {
            "recipient": contact["name"],
            "phone": phone,
            "message": message_text.strip()
        }
        self.pending_message = payload
        self.awaiting_message_for = None

        confirm_prompt = f"Kya main {contact['name']} ko yeh WhatsApp message bhej du: '{message_text}'?"
        return True, confirm_prompt, payload

    def send_whatsapp(self, payload: dict = None) -> str:
        """Sends WhatsApp message via desktop protocol or Web URL"""
        p = payload or self.pending_message
        if not p:
            return "Koi pending message nahi mila."

        phone = p["phone"]
        text = p["message"]
        encoded_text = urllib.parse.quote(text)

        # 1. Try Windows WhatsApp Protocol
        protocol_url = f"whatsapp://send?phone={phone}&text={encoded_text}"
        try:
            os.startfile(protocol_url)
            self.pending_message = None
            self.awaiting_message_for = None
            return f"{p['recipient']} ko WhatsApp message bhej diya gaya hai."
        except Exception as e:
            logger.warning(f"Protocol launch failed ({e}), opening WhatsApp Web...")

        # 2. Fallback to WhatsApp Web
        web_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_text}"
        webbrowser.open(web_url)
        self.pending_message = None
        self.awaiting_message_for = None
        return f"{p['recipient']} ka WhatsApp chat message ke sath open kar diya gaya hai."

# Global instance
message_automator = MessageAutomator()
