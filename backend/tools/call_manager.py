import os
import re
import logging
import asyncio
import webbrowser
from backend.tools.contact_manager import contact_manager
from backend.bridge.phone_hub import phone_hub

logger = logging.getLogger("MJ.CallManager")

class CallManager:
    def __init__(self):
        pass

    async def dial_contact(self, recipient: str) -> str:
        """Dials a contact or phone number via Windows Phone Link, PWA bridge, or WhatsApp Call"""
        clean_name = recipient.strip()
        # Clean helper words
        for w in ["call", "karo", "lagao", "milao", "dial", "ko", "par", "pe", "phone", "se"]:
            clean_name = re.sub(rf"\b{w}\b", "", clean_name, flags=re.IGNORECASE).strip()

        if not clean_name:
            return "Kise call lagana hai Noaman? Kripya naam ya number batayein."

        # Check if clean_name is directly a numeric phone number
        digits_only = re.sub(r"[^\d+]", "", clean_name)
        if len(digits_only) >= 10:
            target_name = "Number"
            target_phone = digits_only
        else:
            # Look up contact in contacts.json
            contact = contact_manager.find_contact(clean_name)
            if not contact:
                return f"'{clean_name}' contact list me nahi mila Noaman. Aap number bol sakte hain ya 'contact save karo' bol sakte hain."
            target_name = contact.get("name", clean_name)
            target_phone = contact.get("phone", "")

        if not target_phone:
            return f"{target_name} ka phone number save nahi hai Noaman. Kripya pehle unka number batayein."

        clean_phone = re.sub(r"[^\d+]", "", target_phone)

        # 1. Broadcast to Connected Mobile PWA (opens native dialer on phone)
        pwa_sent = False
        try:
            pwa_sent = await phone_hub.broadcast({
                "type": "dial_call",
                "number": clean_phone,
                "name": target_name
            })
        except Exception as e:
            logger.debug(f"PWA broadcast error: {e}")

        # 2. Trigger Windows Phone Link / Default OS Dialer
        pc_dialed = False
        try:
            os.startfile(f"tel:{clean_phone}")
            pc_dialed = True
        except Exception as e:
            logger.warning(f"Windows tel: launch failed: {e}")

        # 3. Fallback to WhatsApp chat/call link if OS dialer failed
        if not pc_dialed and not pwa_sent:
            webbrowser.open(f"https://wa.me/{clean_phone}")

        if pwa_sent:
            return f"{target_name} ({clean_phone}) ko call lagayi ja rahi hai, phone par dialer open ho gaya hai."
        elif pc_dialed:
            return f"{target_name} ({clean_phone}) ko Windows Phone Link se call lagayi ja rahi hai."
        else:
            return f"{target_name} ({clean_phone}) ka calling page open kar diya gaya hai."

# Global instance
call_manager = CallManager()
