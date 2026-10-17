import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from backend.config.settings import DATA_DIR, USER_NAME, ASSISTANT_NAME
from backend.tools.contact_manager import contact_manager
from backend.core.llm_engine import llm
from backend.voice.tts import tts
from backend.bridge.phone_hub import phone_hub

logger = logging.getLogger("MJ.CallScreening")

VOICEMAILS_FILE = DATA_DIR / "voicemails.json"
VOICEMAILS_AUDIO_DIR = DATA_DIR / "voicemails"
VOICEMAILS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class CallScreeningEngine:
    """Manages AI call screening, interactive voicemail prompting, STT transcription, and multi-device alerts"""

    def __init__(self):
        self.voicemails_file = Path(VOICEMAILS_FILE)
        self.voicemails = []
        self.screening_mode_active = True  # Auto-screen when busy / missed
        self._load_voicemails()

    def _load_voicemails(self):
        if self.voicemails_file.exists():
            try:
                with open(self.voicemails_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.voicemails = data.get("voicemails", [])
            except Exception as e:
                logger.error(f"Error loading voicemails: {e}")
                self.voicemails = []
        else:
            self.voicemails = []

    def _save_voicemails(self):
        try:
            with open(self.voicemails_file, "w", encoding="utf-8") as f:
                json.dump({"voicemails": self.voicemails}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving voicemails: {e}")

    def get_screening_prompt(self, caller_name: str = "Caller") -> str:
        """Returns the natural AI voice greeting spoken to caller on pickup"""
        return (
            f"Hey! Main {USER_NAME} ki AI assistant {ASSISTANT_NAME} bol rahi hu. "
            f"{USER_NAME} abhi busy hain aur call attend nahi kar sakte. "
            f"Kripya apna message batayein, main un tak zaroor pohocha dungi."
        )

    async def analyze_caller_message(self, caller_name: str, transcript: str) -> dict:
        """Analyzes caller transcript with AI to extract summary, urgency, and action items"""
        if not transcript.strip():
            return {
                "summary": "Caller ne koi spasht message nahi chhoda.",
                "urgency": "LOW",
                "action": "No action needed"
            }

        prompt = f"""
You are {ASSISTANT_NAME}, analyzing a phone voicemail left for your user, {USER_NAME}.
Caller Name: {caller_name}
Voicemail Transcript: "{transcript}"

Analyze this voicemail and provide a JSON response with:
1. "summary": A concise 1-sentence summary in Roman Hindi (Hinglish).
2. "urgency": Exactly one of ["URGENT", "IMPORTANT", "CASUAL", "SPAM"].
3. "action": What {USER_NAME} should do (e.g. "Call back immediately", "Ignore", etc.).

Format output strictly as JSON without extra text:
{{"summary": "...", "urgency": "...", "action": "..."}}
"""
        try:
            ai_response = await llm.generate_response(prompt)
            # Clean json block if LLM wrapped in ```json
            if "```" in ai_response:
                ai_response = ai_response.split("```")[1]
                if ai_response.startswith("json"):
                    ai_response = ai_response[4:]
            data = json.loads(ai_response.strip())
            return {
                "summary": data.get("summary", transcript),
                "urgency": data.get("urgency", "NORMAL"),
                "action": data.get("action", "Check message")
            }
        except Exception as e:
            logger.warning(f"AI analysis fallback for voicemail: {e}")
            # Heuristic urgency
            text_lower = transcript.lower()
            urgency = "URGENT" if any(w in text_lower for w in ["jaldi", "urgent", "emergency", "abhibhi", "turant"]) else "NORMAL"
            return {
                "summary": transcript,
                "urgency": urgency,
                "action": f"{caller_name} ko call back karein"
            }

    async def process_incoming_voicemail(
        self,
        phone_number: str,
        transcript: str,
        audio_bytes: bytes = None,
        caller_name: str = None
    ) -> dict:
        """Processes screened voicemail, performs AI analysis, saves alert card, and broadcasts notification"""
        # Resolve caller name if not provided
        if not caller_name or caller_name == "Unknown":
            contact = contact_manager.find_contact(phone_number)
            caller_name = contact["name"] if contact else (caller_name or phone_number)

        # AI analysis
        analysis = await self.analyze_caller_message(caller_name, transcript)

        # Save audio file if provided
        vm_id = f"vm_{int(time.time())}"
        audio_rel_path = ""
        if audio_bytes:
            audio_path = VOICEMAILS_AUDIO_DIR / f"{vm_id}.wav"
            try:
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)
                audio_rel_path = f"/api/call/audio/{vm_id}.wav"
            except Exception as e:
                logger.error(f"Error saving audio file: {e}")

        # Formulate Voicemail Alert Card
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        voicemail_entry = {
            "id": vm_id,
            "caller_name": caller_name,
            "phone_number": phone_number,
            "timestamp": now_str,
            "transcript": transcript,
            "summary": analysis["summary"],
            "urgency": analysis["urgency"],
            "action": analysis["action"],
            "audio_url": audio_rel_path,
            "read": False
        }

        # Save persistently
        self.voicemails.insert(0, voicemail_entry)
        self._save_voicemails()

        # Multi-Device Delivery:
        # 1. Broadcast over WebSocket to Phone PWA & Laptop UI
        await phone_hub.broadcast({
            "type": "new_voicemail",
            "voicemail": voicemail_entry
        })

        # 2. Spoken Voice Alert
        alert_speech = f"Noaman, {caller_name} ki taraf se ek voicemail aayi hai: {analysis['summary']}"
        try:
            await tts.speak(alert_speech)
        except Exception as e:
            logger.warning(f"Could not vocalize voicemail alert: {e}")

        logger.info(f"Voicemail processed & delivered: {caller_name} ({analysis['urgency']})")
        return voicemail_entry

    def get_unread_voicemails(self) -> list:
        return [vm for vm in self.voicemails if not vm.get("read", False)]

    def mark_all_as_read(self):
        for vm in self.voicemails:
            vm["read"] = True
        self._save_voicemails()

    def get_summary_report(self) -> str:
        """Returns voice summary of missed voicemails"""
        unread = self.get_unread_voicemails()
        if not unread:
            return "Noaman, aapke paas koi nayi voicemail nahi hai. Sab cleared hai!"

        report = f"Noaman, aapke paas {len(unread)} naye voicemails hain: "
        for i, vm in enumerate(unread[:3], 1):
            report += f"{i}. {vm['caller_name']} ne kaha: '{vm['summary']}'. "
        return report

call_screener = CallScreeningEngine()
