import json
import logging
from pathlib import Path
from backend.config.settings import MEMORY_FILE, CONTACTS_FILE

logger = logging.getLogger("MJ.Memory")

class MemoryManager:
    def __init__(self):
        self.memory_path = Path(MEMORY_FILE)
        self.contacts_path = Path(CONTACTS_FILE)
        self._load_memory()
        self._load_contacts()

    def _load_memory(self):
        if self.memory_path.exists():
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
                self.memory = {}
        else:
            self.memory = {}

    def _save_memory(self):
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def _load_contacts(self):
        if self.contacts_path.exists():
            try:
                with open(self.contacts_path, "r", encoding="utf-8") as f:
                    self.contacts = json.load(f).get("contacts", [])
            except Exception as e:
                logger.error(f"Error loading contacts: {e}")
                self.contacts = []
        else:
            self.contacts = []

    def get_user_name(self) -> str:
        return self.memory.get("user_profile", {}).get("name", "Noaman")

    def get_assistant_name(self) -> str:
        return self.memory.get("assistant_profile", {}).get("name", "MJ")

    def add_note(self, text: str):
        if "notes" not in self.memory:
            self.memory["notes"] = []
        self.memory["notes"].append(text)
        self._save_memory()

    def get_contact(self, query: str):
        query_clean = query.strip().lower()
        for contact in self.contacts:
            if contact["name"].lower() == query_clean:
                return contact
            for alias in contact.get("aliases", []):
                if alias.lower() == query_clean:
                    return contact
        return None

# Global instance
memory = MemoryManager()
