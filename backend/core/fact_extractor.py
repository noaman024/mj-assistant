"""
Fact Extractor and Episodic Memory Engine for MJ Assistant.
Adapted from OpenJarvis memory extraction architecture:
Distills durable user facts (preferences, identity, projects, contacts)
from conversations in the background without blocking execution.
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from backend.config.settings import USER_NAME, ASSISTANT_NAME, MEMORY_FILE
from backend.core.llm_engine import llm

logger = logging.getLogger("MJ.FactExtractor")

_EXTRACTION_PROMPT = f"""
You are the memory engine for {ASSISTANT_NAME}, personal AI assistant for {USER_NAME}.
Analyze this conversation turn between {USER_NAME} and {ASSISTANT_NAME}.
Extract any durable, long-term facts about {USER_NAME} worth remembering for future sessions:
- Personal preferences, coding style, tech stack preferences
- Ongoing projects, tasks, or goals
- Friends, family, or contacts mentioned
- Hardware, devices, or environment details

Rules:
1. Ignore temporary one-off greetings or transient questions.
2. Return ONLY a valid JSON array of short fact strings.
3. If there are no durable facts to remember, return [].
4. Each fact should be clear and under 150 characters.
"""


class FactExtractor:
    def __init__(self, memory_file: str = MEMORY_FILE):
        self.memory_path = Path(memory_file)
        self._ensure_storage()

    def _ensure_storage(self):
        if not self.memory_path.exists():
            default_data = {
                "user_profile": {"name": USER_NAME},
                "assistant_profile": {"name": ASSISTANT_NAME},
                "durable_facts": [
                    f"{USER_NAME} prefers modern Indian Hinglish conversation style.",
                    f"{USER_NAME} requires all numbers, percentages, and metrics in English only.",
                    f"{ASSISTANT_NAME} is a smart, friendly, warm feminine companion and coding partner."
                ],
                "conversations": []
            }
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)

    def get_all_facts(self) -> List[str]:
        """Returns all stored durable facts."""
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("durable_facts", [])
        except Exception:
            return []

    def save_fact(self, fact_text: str) -> bool:
        """Saves a new fact if not already present."""
        clean = fact_text.strip()
        if not clean:
            return False

        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            facts = data.get("durable_facts", [])
            # Deduplicate by lowercase similarity
            if any(f.lower() == clean.lower() for f in facts):
                return False

            facts.append(clean)
            data["durable_facts"] = facts
            data["last_updated"] = datetime.now().isoformat()

            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"New durable fact remembered: '{clean}'")
            return True
        except Exception as e:
            logger.error(f"Error saving fact: {e}")
            return False

    async def extract_and_remember(self, user_text: str, assistant_text: str):
        """Asynchronously extracts durable facts from conversation exchange."""
        if not user_text or len(user_text.strip()) < 8:
            return

        exchange = f"User ({USER_NAME}): {user_text}\nAssistant ({ASSISTANT_NAME}): {assistant_text}"

        try:
            prompt = f"{_EXTRACTION_PROMPT}\n\nConversation Turn:\n{exchange}\n\nJSON array:"
            raw_response = await llm.ask(prompt)

            # Extract JSON array
            raw_text = raw_response.strip()
            if "[" in raw_text and "]" in raw_text:
                start = raw_text.find("[")
                end = raw_text.rfind("]") + 1
                facts = json.loads(raw_text[start:end])
                if isinstance(facts, list):
                    for fact in facts:
                        if isinstance(fact, str) and len(fact) > 5:
                            self.save_fact(fact)
        except Exception as e:
            logger.debug(f"Fact extraction skipped: {e}")

    def get_relevant_facts(self, query: str, limit: int = 5) -> List[str]:
        """Simple keyword-relevance matching for facts."""
        facts = self.get_all_facts()
        if not facts:
            return []

        q_words = set(query.lower().split())
        scored = []
        for fact in facts:
            f_words = set(fact.lower().split())
            overlap = len(q_words.intersection(f_words))
            scored.append((overlap, fact))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [fact for score, fact in scored[:limit]]


# Global instance
fact_extractor = FactExtractor()
