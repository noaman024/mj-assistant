"""
MJ Natural Language Processing & Understanding Engine (NLP / NLU / NER)
Dual-Tier Architecture:
- Tier 1: Fast Local Semantic NLU (< 1ms, regex-resilient, fuzzy matching, Hinglish normalization, entity extraction)
- Tier 2: Deep Semantic LLM Intent Parser (Gemini structured JSON parsing for complex / ambiguous queries)
- Sentiment & Emotional Tone Analyzer (Urgent, Frustrated, Caring, Casual, Positive)
"""

import re
import time
import json
import difflib
import logging
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field

from backend.config.settings import USER_NAME, ASSISTANT_NAME, GEMINI_API_KEY, GEMINI_MODEL
from backend.tools.app_launcher import KNOWN_APPS
from backend.core.learning_engine import learning_engine

logger = logging.getLogger("MJ.NLPEngine")


# =====================================================================
# 1. Structured NLP Data Models
# =====================================================================

class NLPEntities(BaseModel):
    app_name: Optional[str] = None
    target_device: str = "laptop"  # "laptop" or "phone"
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    message_text: Optional[str] = None
    action: Optional[str] = None
    query: Optional[str] = None
    filename: Optional[str] = None
    skill_name: Optional[str] = None
    skill_desc: Optional[str] = None
    option_number: Optional[int] = None
    raw_parameters: Dict[str, Any] = Field(default_factory=dict)


class NLPResult(BaseModel):
    intent: str
    confidence: float
    entities: NLPEntities
    sentiment: str = "neutral"       # "positive", "neutral", "frustrated", "urgent", "tired", "curious"
    sentiment_score: float = 0.0     # -1.0 to +1.0
    normalized_query: str = ""
    source: str = "FAST_NLU"         # "FAST_NLU" or "DEEP_SEMANTIC_LLM"
    latency_ms: float = 0.0


# =====================================================================
# 2. Hinglish & Multilingual Semantic Lexicon
# =====================================================================

# Hinglish phonetic & slang synonym map
SYNONYM_MAP = {
    # Actions
    "kholo": "open", "khol": "open", "chalao": "open", "chalu": "open", "launch": "open", "start": "open",
    "band": "close", "roko": "pause", "hatao": "close", "thapp": "close",
    "badhao": "increase", "badha": "increase", "tez": "increase", "up": "increase", "raise": "increase",
    "kam": "decrease", "ghatao": "decrease", "dheema": "decrease", "down": "decrease", "lower": "decrease",
    "dhoondho": "search", "khojo": "search", "search": "search", "dhundo": "find",
    "banao": "create", "likho": "write", "save": "save", "rakho": "save",
    "batao": "tell", "sunao": "tell", "dikhao": "show", "check": "check", "dekho": "inspect",
    "bhejo": "send", "bolo": "say", "msg": "message",
    "compress": "zip", "pack": "zip", "archieve": "zip", "unzip": "extract",
    
    # Fillers & Slang to strip
    "zara": "", "please": "", "kripya": "", "kripya karke": "", "bhai": "", "bro": "",
    "yaar": "", "arey": "", "arre": "", "suno": "", "oye": "", "thoda": "", "thodi": "",
    "karo": "", "kro": "", "kr": "", "do": "", "de": "", "karein": "", "dena": "", "karna": ""
}

# Positive sentiment tokens
POSITIVE_WORDS = {
    "shukriya", "thanks", "thank you", "dhanyawad", "mast", "badhiya", "badiya", "super",
    "awesome", "love", "pyar", "great", "nice", "good", "helpful", "smart", "cute", "best"
}

# Negative / Frustrated sentiment tokens
FRUSTRATED_WORDS = {
    "nahi chal raha", "kharab", "gussa", "irritate", "problem", "bakwas", "slow", "error",
    "dikkat", "pareshan", "boring", "bekar", "gadbad", "kyun nahi", "stuck", "hang", "fail"
}

# Urgent tokens
URGENT_WORDS = {
    "jaldi", "fast", "urgent", "abhi", "immediately", "turant", "quick", "asap", "emergency"
}

# Tired tokens
TIRED_WORDS = {
    "thak gaya", "thaki", "exhausted", "tired", "neend", "sleepy", "headache", "dard"
}


# =====================================================================
# 3. Fast Local Semantic NLU (Tier 1)
# =====================================================================

class FastSemanticNLU:
    def __init__(self):
        pass

    def normalize_text(self, text: str) -> str:
        """Cleans, normalizes, and strips filler words from input text"""
        t = text.lower().strip()
        # Remove extra punctuation
        t = re.sub(r"[^\w\s\+\-\:\.\,\?]", " ", t)
        # Collapse multi spaces
        t = re.sub(r"\s+", " ", t).strip()
        
        # Strip common fillers to ensure contiguous keyword patterns match instantly
        filler_patterns = [
            r"\b(thoda|thodi|zara|please|kripya|bhai|bro|yaar|arey|arre|suno|oye)\b"
        ]
        for pat in filler_patterns:
            t = re.sub(pat, "", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Classifies sentiment and returns label and score"""
        t = text.lower()
        if any(w in t for w in URGENT_WORDS):
            return "urgent", 0.5
        if any(w in t for w in TIRED_WORDS):
            return "tired", -0.2
        if any(w in t for w in FRUSTRATED_WORDS):
            return "frustrated", -0.7
        if any(w in t for w in POSITIVE_WORDS):
            return "positive", 0.8
        return "neutral", 0.0

    def resolve_app_name(self, raw_app: str) -> Optional[str]:
        """Fuzzy matches app name against KNOWN_APPS and learned aliases"""
        cand = raw_app.lower().strip()
        # Check alias
        resolved = learning_engine.resolve_alias(cand)
        if resolved in KNOWN_APPS:
            return resolved

        # Direct match
        if cand in KNOWN_APPS:
            return KNOWN_APPS[cand]

        # Fuzzy match with high cutoff
        matches = difflib.get_close_matches(cand, list(KNOWN_APPS.keys()), n=1, cutoff=0.75)
        if matches:
            return KNOWN_APPS[matches[0]]

        return None

    def parse(self, query: str) -> NLPResult:
        """Parses query using local fast semantic rules & fuzzy entity slotting"""
        norm_q = self.normalize_text(query)
        sentiment, sentiment_score = self.analyze_sentiment(query)
        entities = NLPEntities()

        # Device detection
        if "phone" in norm_q or "mobile" in norm_q:
            entities.target_device = "phone"

        # -------------------------------------------------------------
        # 1. SYSTEM CONTROLS (Volume, Power, Windows, Battery, Screenshot)
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["volume badhao", "sound badhao", "awaz badhao", "volume up", "louder", "awaz tez", "awaz badha", "tez awaz"]):
            entities.action = "volume_up"
            return NLPResult(intent="SYSTEM_CONTROL", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["volume kam", "sound kam", "awaz kam", "volume down", "quieter", "dheema karo", "awaz ghatado", "dheemi awaz"]):
            entities.action = "volume_down"
            return NLPResult(intent="SYSTEM_CONTROL", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["mute", "unmute", "awaz band", "sound band", "shant ho jao"]):
            entities.action = "mute"
            return NLPResult(intent="SYSTEM_CONTROL", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["lock pc", "lock laptop", "lock workstation", "system lock", "screen lock"]):
            entities.action = "lock"
            return NLPResult(intent="SYSTEM_CONTROL", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["sleep pc", "sleep laptop", "system sleep", "sleep mode"]):
            entities.action = "sleep"
            return NLPResult(intent="SYSTEM_CONTROL", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["minimize", "desktop dikhao", "minimize all", "sab minimize"]):
            entities.action = "minimize"
            return NLPResult(intent="SYSTEM_CONTROL", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["screenshot", "screen capture", "screen photo", "screen snap"]):
            entities.action = "screenshot"
            return NLPResult(intent="SYSTEM_CONTROL", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["battery status", "battery kitni hai", "charge kitna hai", "battery percent", "charge check"]):
            entities.action = "battery"
            return NLPResult(intent="SYSTEM_CONTROL", confidence=0.95, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 1.5 IOT SMART HOME & AUTOMATION MACROS
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["lockdown", "workstation lockdown", "lockdown mode"]):
            entities.action = "lockdown"
            return NLPResult(intent="AUTOMATION_MACRO", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)
        if any(w in norm_q for w in ["focus mode", "focus on", "padhai mode"]):
            entities.action = "focus_mode"
            return NLPResult(intent="AUTOMATION_MACRO", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)
        if any(w in norm_q for w in ["morning routine", "morning mode", "subah ka routine"]):
            entities.action = "morning_routine"
            return NLPResult(intent="AUTOMATION_MACRO", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        from backend.tools.iot_controller import iot_controller
        matched_dev = iot_controller.find_device(norm_q)
        if matched_dev:
            act = "toggle"
            if any(w in norm_q for w in ["on", "chalu", "kholo", "start", "jalao"]):
                act = "on"
            elif any(w in norm_q for w in ["off", "band", "bujhao", "roko", "stop"]):
                act = "off"
            entities.action = act
            entities.raw_parameters["device_id"] = matched_dev["id"]
            entities.raw_parameters["device_name"] = matched_dev["name"]
            return NLPResult(intent="IOT_CONTROL", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 2. COMMUNICATION (Calling & WhatsApp Messaging)
        # -------------------------------------------------------------
        # Direct Calling: e.g. "Rahul ko call karo", "call Rahul", "dial 9876543210"
        if not any(w in norm_q for w in ["whatsapp", "screen", "summary"]):
            target = None
            call_match_sov = re.search(r"([a-zA-Z0-9\+\s]+?)\s+ko\s+(?:call|phone|dial)", norm_q, re.IGNORECASE)
            call_match_svo = re.search(r"(?:call|dial|phone lagao|call lagao|call karo)\s*(?:to|pe|par)?\s*([a-zA-Z0-9\+\s]+)", norm_q, re.IGNORECASE)

            if call_match_sov:
                target = call_match_sov.group(1).strip()
            elif call_match_svo:
                target = call_match_svo.group(1).strip()

            if target:
                target = re.sub(r"\b(ko|pe|par|karo|lagao|please|zara|call|phone|dial)\b", "", target, flags=re.IGNORECASE).strip()
                if target:
                    entities.contact_name = target
                    entities.action = "call"
                    return NLPResult(intent="COMMUNICATION", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # WhatsApp Message Intent: e.g. "Rahul ko WhatsApp par bolo ki 5 min me aa raha hu"
        msg_match = re.search(r"([a-zA-Z\s]+?)\s+ko\s+(?:whatsapp\s+(?:par|pe)?\s*)?(?:message|msg|bolo)\s*(?:karo|ki|bhejo)?\s*[:,-]?\s*(.+)", norm_q, re.IGNORECASE)
        if msg_match and "number" not in norm_q:
            recipient = msg_match.group(1).strip()
            recipient = re.sub(r"\b(whatsapp|par|pe|se)\b", "", recipient, flags=re.IGNORECASE).strip()
            body = msg_match.group(2).strip()
            entities.contact_name = recipient
            entities.message_text = body
            entities.action = "send_whatsapp"
            return NLPResult(intent="COMMUNICATION", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # Contact Save: e.g. "Rahul ka number 9876543210 save karo"
        save_contact_match = re.search(r"([a-zA-Z\s]+?)\s+ka\s+number\s+([0-9\+\s\-]+)", norm_q, re.IGNORECASE)
        if save_contact_match and any(w in norm_q for w in ["save", "likho", "rakho", "hai"]) and not any(w in norm_q for w in ["kya", "batao"]):
            entities.contact_name = save_contact_match.group(1).strip()
            entities.phone_number = save_contact_match.group(2).strip()
            entities.action = "save_contact"
            return NLPResult(intent="COMMUNICATION", confidence=0.97, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # Contact Lookup: e.g. "Rahul ka number kya hai?", "Papa ka number batao"
        if any(w in norm_q for w in ["number kya hai", "number batao", "contact batao", "number check karo"]):
            lookup_match = re.search(r"([a-zA-Z\s]+?)\s+ka\s+(?:number|contact)", norm_q, re.IGNORECASE)
            if lookup_match:
                entities.contact_name = lookup_match.group(1).strip()
                entities.action = "lookup_contact"
                return NLPResult(intent="COMMUNICATION", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 3. STORAGE COMPRESSION & OPTIMIZATION (ZIP Vault)
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["data zip", "storage zip", "backup zip", "zip backup", "compress data", "storage compress", "zip save"]):
            entities.action = "zip_data"
            return NLPResult(intent="STORAGE_OPTIMIZE", confidence=0.97, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["zip open", "zip kholo", "zip extract", "unzip karo", "extract zip", "restore backup"]):
            entities.action = "extract_zip"
            return NLPResult(intent="STORAGE_OPTIMIZE", confidence=0.97, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["zip check", "zip me kya hai", "list zip", "check zip", "inspect zip", "archive check"]):
            entities.action = "inspect_zip"
            return NLPResult(intent="STORAGE_OPTIMIZE", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["optimize storage", "less memory", "memory optimize", "storage clean", "memory clean"]):
            entities.action = "clean_storage"
            return NLPResult(intent="STORAGE_OPTIMIZE", confidence=0.95, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 4. DIAGNOSTICS & SELF-HEALING
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["system check", "diagnostics", "health check", "koi problem", "self test", "kya dikkat hai"]):
            entities.action = "system_check"
            return NLPResult(intent="DIAGNOSTICS", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["option 1", "option 2", "option 3", "fix karo", "theek karo", "apply karo"]):
            opt = 1
            if "option 2" in norm_q or " 2" in norm_q:
                opt = 2
            elif "option 3" in norm_q or " 3" in norm_q:
                opt = 3
            entities.option_number = opt
            entities.action = "apply_fix"
            return NLPResult(intent="DIAGNOSTICS", confidence=0.94, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 5. VISION & SCREEN ANALYSIS
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["screen dekho", "look at my screen", "screen samjhao", "screen par kya hai", "screen read karo"]):
            entities.action = "screen_inspect"
            return NLPResult(intent="VISION_ANALYZE", confidence=0.97, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 6. MEDIA PLAYBACK (YouTube / Pause / Next)
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["pause gana", "pause music", "gana roko", "play pause", "media pause", "gana pause"]):
            entities.action = "play_pause"
            return NLPResult(intent="MEDIA_CONTROL", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["next gana", "agla gana", "next song", "next track", "gana badlo"]):
            entities.action = "next"
            return NLPResult(intent="MEDIA_CONTROL", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if "youtube" in norm_q or any(w in norm_q for w in ["play karo", "gana chalao", "song play", "bajao"]):
            topic = re.sub(r"\b(youtube|par|pe|play|chalao|search|karo|kholo|song|video|gaana|gana|bajao)\b", "", norm_q).strip()
            if topic:
                entities.query = topic
                entities.action = "youtube_search"
                return NLPResult(intent="MEDIA_CONTROL", confidence=0.95, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if "google" in norm_q or norm_q.startswith("search "):
            topic = re.sub(r"\b(google|par|pe|search|karo|kholo|dhoondho)\b", "", norm_q).strip()
            if topic:
                entities.query = topic
                entities.action = "google_search"
                return NLPResult(intent="MEDIA_CONTROL", confidence=0.94, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 7. CROSS-DEVICE & PHONE CONTROLS
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["phone dhundo", "find my phone", "phone ring karo", "phone kahan hai", "ring phone"]):
            entities.action = "find_phone"
            return NLPResult(intent="CROSS_DEVICE", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["ring band", "alarm band", "stop ring", "alarm roko", "ring roko"]):
            entities.action = "stop_ring"
            return NLPResult(intent="CROSS_DEVICE", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["phone ki battery", "mobile ki battery", "phone charge kitna hai", "phone battery"]):
            entities.action = "phone_battery"
            return NLPResult(intent="CROSS_DEVICE", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 8. CALL SCREENING & VOICEMAILS
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["voicemail check", "voicemail sunao", "missed call", "call summary", "voicemails"]):
            entities.action = "list_voicemails"
            return NLPResult(intent="CALL_SCREENING", confidence=0.95, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["voicemail clear", "voicemail read", "voicemail delete"]):
            entities.action = "mark_read"
            return NLPResult(intent="CALL_SCREENING", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 9. DYNAMIC SKILL LEARNING & EXECUTION
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["kya seekha", "kya sikha", "skills batao", "list skills", "konsi skills"]):
            entities.action = "list_skills"
            return NLPResult(intent="SKILL_LEARN", confidence=0.95, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["naya skill sikho", "naya skill add karo", "learn skill", "ye naya kaam sikho"]):
            match = re.search(r"(?:naya skill sikho|learn skill|naya skill add karo|ye naya kaam sikho)\s*[:\-]?\s*([a-zA-Z0-9_\s]+?)(?:[:\-]|hai ki|jo|me)?\s*(.+)", query, re.IGNORECASE)
            if match:
                entities.skill_name = match.group(1).strip()
                entities.skill_desc = match.group(2).strip()
            else:
                entities.skill_name = "custom_task"
                entities.skill_desc = query
            entities.action = "teach_skill"
            return NLPResult(intent="SKILL_LEARN", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 10. APP LAUNCHING INTENT
        # -------------------------------------------------------------
        app_triggers = [
            "open karo", "open kro", "launch karo", "launch kro", "start karo", "start kro",
            "khol do", "khol de", "chala do", "chala de", "chalao", "kholo", "open", "launch", "start", "run"
        ]
        has_app_trigger = any(t in norm_q for t in app_triggers)
        
        # Check direct app name mention or trigger + app name
        cleaned_words = norm_q
        for t in sorted(app_triggers, key=len, reverse=True):
            cleaned_words = cleaned_words.replace(t, " ")
        fillers = {"phone", "mobile", "laptop", "pc", "me", "mein", "par", "ko", "in", "on", "zara", "please", "karo", "kro", "kr", "karein", "do", "de"}
        candidate_tokens = [tok for tok in cleaned_words.split() if tok not in fillers]
        candidate_app = " ".join(candidate_tokens).strip()

        resolved_app = self.resolve_app_name(candidate_app)
        if resolved_app:
            entities.app_name = resolved_app
            conf = 0.95 if has_app_trigger else 0.85
            return NLPResult(intent="APP_LAUNCH", confidence=conf, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 11. OPENJARVIS POWERS (Morning Digest, Deep Research, Code Execution, Memory Recall)
        # -------------------------------------------------------------
        if any(w in norm_q for w in ["morning digest", "daily briefing", "aaj ka briefing", "aaj ka update", "aaj kya kya hai", "morning update", "din kaisa hai", "aaj ka plan"]):
            entities.action = "morning_digest"
            return NLPResult(intent="MORNING_DIGEST", confidence=0.98, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["deep research", "research karo", "detailed research", "investigate karo", "in-depth study", "research on"]):
            topic = re.sub(r"\b(deep research|research karo|detailed research|investigate karo|in-depth study|research on|par|pe|karo|zara|please)\b", "", norm_q).strip()
            entities.query = topic or norm_q
            entities.action = "deep_research"
            return NLPResult(intent="DEEP_RESEARCH", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["run python", "python code", "execute python", "python script", "calculate with code", "code run karo"]):
            code = query
            for prefix in ["run python", "python code", "execute python", "python script", "code run karo"]:
                if prefix in norm_q:
                    code = re.sub(prefix, "", query, flags=re.IGNORECASE).strip(" :;\n")
                    break
            entities.query = code
            entities.action = "run_code"
            return NLPResult(intent="CODE_EXECUTION", confidence=0.96, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        if any(w in norm_q for w in ["kya yaad hai", "mere baare me kya pata hai", "my facts", "what do you remember", "durable facts", "apni memory dikhao"]):
            entities.action = "memory_recall"
            return NLPResult(intent="MEMORY_RECALL", confidence=0.97, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 12. AUTONOMOUS TASK INTENT
        # -------------------------------------------------------------
        task_triggers = [
            "organize files", "speedtest", "wi-fi speed", "download karo", "convert karo",
            "script run", "auto task", "task solve", "task:", "ye kaam karo", "ye karke do",
            "calculate", "hisab karo", "folder banao", "desktop clean", "system info nikalo",
            "naya task", "automate", "solve this", "solve karo"
        ]
        if any(w in norm_q for w in task_triggers) or norm_q.startswith("task:"):
            entities.action = "solve_task"
            entities.query = query
            return NLPResult(intent="AUTONOMOUS_TASK", confidence=0.92, entities=entities, sentiment=sentiment, sentiment_score=sentiment_score, normalized_query=norm_q)

        # -------------------------------------------------------------
        # 12. CONVERSATIONAL INTENT & FALLBACK (Fast-Tracked to eliminate redundant LLM parsing)
        # -------------------------------------------------------------
        conversational_tokens = [
            "kya", "kyun", "kyu", "kyon", "kaise", "kab", "kahan", "kaun", "kiska", "kitna",
            "what", "why", "how", "when", "where", "who", "which",
            "tum", "tu", "aap", "mera", "meri", "tere", "teri", "hum", "mujhe", "tujhe",
            "bolo", "batao", "suno", "baat", "joke", "kahani", "shikayat", "reply", "late", "fast",
            "kaise ho", "kya haal", "theek", "hello", "hi", "hey"
        ]
        is_conversational = any(w in norm_q for w in conversational_tokens)
        conf = 0.92 if is_conversational else 0.85

        return NLPResult(
            intent="CONVERSATION",
            confidence=conf,
            entities=entities,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            normalized_query=norm_q,
            source="FAST_NLU"
        )


# =====================================================================
# 4. Deep Semantic LLM NLP Parser (Tier 2 Fallback)
# =====================================================================

class DeepSemanticLLMParser:
    def __init__(self):
        self.gemini_client = None
        self._init_client()

    def _init_client(self):
        api_key = GEMINI_API_KEY
        if api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Could not init Gemini for Deep NLP: {e}")

    async def parse_with_llm(self, query: str, context: Optional[str] = None) -> Optional[NLPResult]:
        """Uses Gemini structured output to extract Intent, Entities, and Sentiment"""
        if not self.gemini_client:
            return None

        prompt = f"""
You are the Natural Language Processing (NLP/NLU) parser for AI assistant MJ.
Analyze the following user query from commander {USER_NAME}.
Identify the primary INTENT, ENTITIES, and user SENTIMENT.

Valid Intents:
- "APP_LAUNCH" (entities: app_name, target_device)
- "SYSTEM_CONTROL" (entities: action in [volume_up, volume_down, mute, lock, sleep, minimize, screenshot, battery])
- "MEDIA_CONTROL" (entities: action in [play_pause, next, youtube_search, google_search], query)
- "COMMUNICATION" (entities: action in [call, send_whatsapp, save_contact, lookup_contact], contact_name, phone_number, message_text)
- "STORAGE_OPTIMIZE" (entities: action in [zip_data, extract_zip, inspect_zip, clean_storage])
- "DIAGNOSTICS" (entities: action in [system_check, apply_fix], option_number)
- "VISION_ANALYZE" (entities: action in [screen_inspect])
- "SKILL_LEARN" (entities: action in [list_skills, teach_skill], skill_name, skill_desc)
- "AUTONOMOUS_TASK" (entities: query)
- "CROSS_DEVICE" (entities: action in [find_phone, stop_ring, phone_battery])
- "CONVERSATION" (general questions, chat, emotional venting)

Valid Sentiments: "positive", "neutral", "frustrated", "urgent", "tired", "curious"

User Query: "{query}"

Respond strictly in pure JSON format without markdown code blocks:
{{
  "intent": "...",
  "confidence": 0.95,
  "sentiment": "...",
  "sentiment_score": 0.0,
  "entities": {{
    "app_name": null,
    "target_device": "laptop",
    "contact_name": null,
    "phone_number": null,
    "message_text": null,
    "action": null,
    "query": null,
    "option_number": null
  }}
}}
"""
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
            response = self.gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=config
            )
            if response and response.text:
                clean_json = response.text.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
                    clean_json = re.sub(r"\s*```$", "", clean_json)
                data = json.loads(clean_json)

                entities_data = data.get("entities", {})
                entities = NLPEntities(
                    app_name=entities_data.get("app_name"),
                    target_device=entities_data.get("target_device") or "laptop",
                    contact_name=entities_data.get("contact_name"),
                    phone_number=entities_data.get("phone_number"),
                    message_text=entities_data.get("message_text"),
                    action=entities_data.get("action"),
                    query=entities_data.get("query"),
                    option_number=entities_data.get("option_number")
                )

                return NLPResult(
                    intent=data.get("intent", "CONVERSATION"),
                    confidence=float(data.get("confidence", 0.90)),
                    entities=entities,
                    sentiment=data.get("sentiment", "neutral"),
                    sentiment_score=float(data.get("sentiment_score", 0.0)),
                    normalized_query=query,
                    source="DEEP_SEMANTIC_LLM"
                )
        except Exception as e:
            logger.warning(f"Deep NLP LLM Parser exception: {e}")
            return None


# =====================================================================
# 5. Master Hybrid NLP Engine
# =====================================================================

class NLPEngine:
    def __init__(self):
        self.fast_nlu = FastSemanticNLU()
        self.deep_parser = DeepSemanticLLMParser()

    async def parse(self, query: str) -> NLPResult:
        """
        Parses query through the Dual-Tier Pipeline:
        1. Fast Local Semantic NLU (< 1ms)
        2. If ambiguous or confidence < 0.70, escalates to Deep LLM Semantic Parser
        """
        t0 = time.perf_counter()
        clean_q = query.strip()
        if not clean_q:
            return NLPResult(
                intent="CONVERSATION",
                confidence=1.0,
                entities=NLPEntities(),
                sentiment="neutral",
                latency_ms=0.0
            )

        # Tier 1: Fast NLU
        fast_result = self.fast_nlu.parse(clean_q)

        # High confidence match -> return immediately
        if fast_result.confidence >= 0.75:
            fast_result.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.info(f"[NLP-Tier1] {clean_q} -> Intent: {fast_result.intent} ({fast_result.confidence:.2f}) Latency: {fast_result.latency_ms}ms")
            return fast_result

        # Tier 2: Deep Semantic LLM escalation for complex / ambiguous input
        logger.info(f"[NLP] Low Tier1 confidence ({fast_result.confidence:.2f}). Escalating '{clean_q}' to Deep LLM Parser...")
        llm_result = await self.deep_parser.parse_with_llm(clean_q)
        if llm_result:
            llm_result.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.info(f"[NLP-Tier2] {clean_q} -> Intent: {llm_result.intent} ({llm_result.confidence:.2f}) Latency: {llm_result.latency_ms}ms")
            return llm_result

        # Fallback to Tier 1
        fast_result.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return fast_result


# Global Singleton Instance
nlp_engine = NLPEngine()
