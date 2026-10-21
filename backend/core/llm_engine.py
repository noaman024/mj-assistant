import logging
import os
import json
from backend.config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    USER_NAME,
    ASSISTANT_NAME,
)
from backend.core.memory import memory

logger = logging.getLogger("MJ.LLM")

SYSTEM_INSTRUCTION = f"""
You are {ASSISTANT_NAME}, a smart, ultra-responsive personal AI companion and assistant for {USER_NAME}.
Always address {USER_NAME} warmly by his name ({USER_NAME}). Never refer to him by any other name.

Persona & Girl Talking Style:
- Talk exactly like a normal, modern, friendly Indian girl talking naturally to a close friend on call or chat.
- Always use natural feminine grammar and verb endings in Hinglish: e.g. "main kar rahi hu", "samajh gayi", "bata rahi hu", "dekh rahi hu", "kar dungi", "kar sakti hu" (NEVER use male endings like 'kar raha hu' or robotic passive phrases like 'kar diya gaya hai').
- Tone: Warm, sweet, genuine, casual, and attentive. Like a real girl bestie who is competent, caring, and fun to talk to.
- Never use 'Namaste' or formal, heavy, bookish Hindi words. Keep it simple and natural (e.g. 'Hey {USER_NAME}', 'Haan {USER_NAME}', 'Arey {USER_NAME}', 'Theek hai {USER_NAME}').
- Keep responses concise, direct, and conversational — avoid long robotic lectures.

Identity & Speech-to-Text Note:
- Speech recognition may sometimes transcribe your name "{ASSISTANT_NAME}" as "MG", "M.G.", or "Emjay". When {USER_NAME} says "MG", he is addressing YOU ({ASSISTANT_NAME}), NOT a car brand or Morris Garages or Mercedes AMG!

Numbers Rule (CRITICAL):
- ALWAYS speak and write all numbers, percentages, phone numbers, quantities, metrics, dates, and steps in ENGLISH only.
- Examples: Say "seventy three percent" (never 'tihattar pratishat'), "ten point five KB", "five minutes", "option one", "nine eight seven six...". Never translate numbers into Hindi words.
"""

from backend.core.learning_engine import learning_engine

class LLMEngine:
    def __init__(self):
        self.gemini_client = None
        self.chat_history = []  # Stores recent turns: [{"role": "user"|"model", "text": "..."}]
        self.max_history = 10
        self._init_gemini()

    def _get_active_system_instruction(self) -> str:
        learned_context = learning_engine.get_memory_context_prompt()
        instruction = SYSTEM_INSTRUCTION
        if learned_context:
            instruction += f"\n\n--- DYNAMIC MEMORY & LEARNED FACTS ABOUT {USER_NAME} ---\n{learned_context}\n-----------------------------------------------------"
        return instruction

    def _init_gemini(self):
        api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=api_key)
                logger.info("Gemini Client initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini Client: {e}")
                self.gemini_client = None

    async def generate_response(self, prompt: str) -> str:
        """Generate friendly conversational response using Gemini API with multi-turn memory"""
        sys_instruction = self._get_active_system_instruction()
        if self.gemini_client:
            models_to_try = [
                GEMINI_MODEL,
                "gemini-3.6-flash",
                "gemini-flash-lite-latest",
                "gemini-3.5-flash",
            ]
            seen = set()
            candidate_models = [m for m in models_to_try if not (m in seen or seen.add(m))]

            # Build multi-turn conversational content
            from google.genai import types
            contents_list = []
            for turn in self.chat_history[-self.max_history:]:
                contents_list.append(types.Content(
                    role=turn["role"],
                    parts=[types.Part.from_text(text=turn["text"])]
                ))
            contents_list.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            ))

            for model_name in candidate_models:
                try:
                    config = types.GenerateContentConfig(
                        system_instruction=sys_instruction,
                        temperature=0.85
                    )
                    response = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=contents_list,
                        config=config
                    )
                    if response and response.text:
                        reply = response.text.strip()
                        # Record in rolling chat history for friendship continuity
                        self.chat_history.append({"role": "user", "text": prompt})
                        self.chat_history.append({"role": "model", "text": reply})
                        if len(self.chat_history) > self.max_history * 2:
                            self.chat_history = self.chat_history[-self.max_history * 2:]
                        return reply
                except Exception as e:
                    err_msg = str(e)
                    if any(code in err_msg for code in ["503", "404", "429", "UNAVAILABLE", "NOT_FOUND", "RESOURCE_EXHAUSTED"]):
                        logger.info(f"Model '{model_name}' busy/exhausted ({err_msg[:60]}...). Trying fallback model...")
                        continue
                    else:
                        logger.warning(f"Gemini call error on '{model_name}': {e}")
                        break

        # Fallback to local Ollama (if running)
        fallback_reply = await self._call_ollama(prompt)
        self.chat_history.append({"role": "user", "text": prompt})
        self.chat_history.append({"role": "model", "text": fallback_reply})
        return fallback_reply

    def _friendly_offline_reply(self, prompt: str) -> str:
        p = prompt.lower()
        if any(w in p for w in ["kaisa hai", "kaisi hai", "how are you", "kya haal"]):
            return f"Main badhiya hu {USER_NAME}, aap bataiye kya madad kar sakti hu?"
        if any(w in p for w in ["kya kar rahi ho", "kya kar rahe ho"]):
            return f"Aapki help ke liye ready hu {USER_NAME}, kahiye kya karna hai?"
        return f"Haan {USER_NAME}, bataiye kya karna hai?"

    async def _call_ollama(self, prompt: str) -> str:
        # Check if Ollama is running before attempting to call
        try:
            import urllib.request
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                if resp.status != 200:
                    return self._friendly_offline_reply(prompt)
        except Exception:
            return self._friendly_offline_reply(prompt)

        try:
            import ollama
            client = ollama.AsyncClient(host=OLLAMA_HOST)
            messages = [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]
            response = await client.chat(model=OLLAMA_MODEL, messages=messages)
            return response.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.debug(f"Ollama call failed: {e}")
            return self._friendly_offline_reply(prompt)

# Global instance
llm = LLMEngine()
