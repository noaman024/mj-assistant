import json
import logging
from pathlib import Path
from backend.config.settings import CONTACTS_FILE

logger = logging.getLogger("MJ.ContactManager")

class ContactManager:
    def __init__(self):
        self.contacts_file = Path(CONTACTS_FILE)
        self.contacts = []
        self._load_contacts()

    def _load_contacts(self):
        if self.contacts_file.exists():
            try:
                with open(self.contacts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.contacts = data.get("contacts", [])
            except Exception as e:
                logger.error(f"Error loading contacts: {e}")
                self.contacts = []
        else:
            self.contacts = []

    def _save_contacts(self):
        try:
            with open(self.contacts_file, "w", encoding="utf-8") as f:
                json.dump({"contacts": self.contacts}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving contacts: {e}")

    def add_contact(self, name: str, phone: str, aliases: list = None) -> str:
        """Add or update a contact"""
        aliases = aliases or []
        name_clean = name.strip()
        phone_clean = "".join(filter(lambda c: c.isdigit() or c == "+", phone.strip()))

        # Check existing
        for c in self.contacts:
            if c["name"].lower() == name_clean.lower():
                c["phone"] = phone_clean
                c["whatsapp"] = phone_clean
                if aliases:
                    c["aliases"] = list(set(c.get("aliases", []) + aliases))
                self._save_contacts()
                return f"{name_clean} ka contact update kar diya gaya hai: {phone_clean}"

        new_contact = {
            "name": name_clean,
            "aliases": aliases,
            "phone": phone_clean,
            "whatsapp": phone_clean
        }
        self.contacts.append(new_contact)
        self._save_contacts()
        return f"{name_clean} ka contact save ho gaya hai: {phone_clean}"

    def find_contact(self, query: str) -> dict | None:
        """Find contact by name or alias"""
        q = query.strip().lower()
        for c in self.contacts:
            if c["name"].lower() == q:
                return c
            for alias in c.get("aliases", []):
                if alias.lower() == q:
                    return c
        # Partial match
        for c in self.contacts:
            if q in c["name"].lower():
                return c
        return None

# Global instance
contact_manager = ContactManager()
