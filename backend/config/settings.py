import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Load environment variables
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

# User & Assistant Configuration
USER_NAME = os.getenv("USER_NAME", "Noaman")
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "MJ")
WAKE_WORDS = ["hey mj", "mj", "hello mj"]

# AI Model Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Voice Configuration (Edge-TTS Fallback)
# en-IN-NeerjaNeural or hi-IN-SwaraNeural or ur-IN-GulNeural for natural subcontinent accent
TTS_VOICE = os.getenv("TTS_VOICE", "hi-IN-SwaraNeural")
TTS_RATE = os.getenv("TTS_RATE", "+15%")
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")

# ElevenLabs Configuration (Exact Voice Clone / Community Voice: Swati S)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "qFwAIpwqlpqZbTYpttVi")  # Swati S (Empathetic, Intimate & Cozy)
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

# Storage Files
MEMORY_FILE = DATA_DIR / "memories.json"
CONTACTS_FILE = DATA_DIR / "contacts.json"
APP_CACHE_FILE = DATA_DIR / "apps_cache.json"

# Server Port
API_PORT = int(os.getenv("API_PORT", "8000"))
WS_PORT = int(os.getenv("WS_PORT", "8001"))
