import re
import json
import logging
from datetime import datetime
from pathlib import Path
from backend.config.settings import DATA_DIR
from backend.core.memory import memory

logger = logging.getLogger("MJ.Learning")

LEARNED_RULES_FILE = DATA_DIR / "learned_rules.json"

class ContinuousLearningEngine:
    def __init__(self):
        self.rules_file = Path(LEARNED_RULES_FILE)
        self._load_knowledge()

    def _load_knowledge(self):
        if self.rules_file.exists():
            try:
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    self.knowledge = json.load(f)
            except Exception as e:
                logger.error(f"Error loading learned knowledge: {e}")
                self.knowledge = self._default_knowledge()
        else:
            self.knowledge = self._default_knowledge()
            self._save_knowledge()

    def _default_knowledge(self):
        return {
            "learned_facts": [],
            "user_preferences": {},
            "learned_aliases": {},
            "custom_routines": {},
            "corrections_and_rules": []
        }

    def _save_knowledge(self):
        try:
            with open(self.rules_file, "w", encoding="utf-8") as f:
                json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving learned knowledge: {e}")

    def learn_fact(self, fact: str, category: str = "general") -> str:
        """Stores a learned fact into permanent memory"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = {
            "fact": fact,
            "category": category,
            "learned_at": timestamp
        }
        # Check if duplicate
        if not any(f["fact"].lower() == fact.lower() for f in self.knowledge["learned_facts"]):
            self.knowledge["learned_facts"].append(entry)
            self._save_knowledge()
            logger.info(f"Learned new fact: '{fact}'")
        return f"Maine yeh yaad rakh liya hai: '{fact}'."

    def learn_alias(self, alias: str, target: str) -> str:
        """Learns a custom nickname, slang, or shortcut"""
        self.knowledge["learned_aliases"][alias.lower().strip()] = target.lower().strip()
        self._save_knowledge()
        logger.info(f"Learned alias: '{alias}' -> '{target}'")
        return f"Samajh gayi! Ab se '{alias}' ka matlab '{target}' samjhungi."

    def learn_correction(self, rule: str) -> str:
        """Learns a behavioral correction or rule from Noaman"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.knowledge["corrections_and_rules"].append({
            "rule": rule,
            "learned_at": timestamp
        })
        self._save_knowledge()
        logger.info(f"Learned correction rule: '{rule}'")
        return f"Noted! Aage se main is baat ka dhyan rakhungi: '{rule}'."

    def resolve_alias(self, term: str) -> str:
        """Checks if a term has a learned alias"""
        term_lower = term.lower().strip()
        return self.knowledge["learned_aliases"].get(term_lower, term)

    def analyze_and_learn(self, text: str) -> tuple[bool, str]:
        """
        Analyzes conversation to automatically extract lessons, facts, preferences or corrections.
        Returns: (did_learn: bool, ack_message: str)
        """
        t = text.strip()
        t_lower = t.lower()

        # 1. Explicit Teaching: "yaad rakhna / remember that"
        remember_match = re.search(r"(?:yaad rakhna|yaad rakho|remember that|note kar lo)\s*[:,]?\s*(.+)", t_lower)
        if remember_match:
            fact = remember_match.group(1).strip()
            msg = self.learn_fact(fact, category="user_instruction")
            return True, msg

        # 2. Teaching Alias / Meaning: "X ko Y samjho" / "jab main X bolu to uska matlab Y hai"
        alias_match1 = re.search(r"([a-zA-Z0-9\s]+)\s+ko\s+([a-zA-Z0-9\s]+)\s+(?:samjho|samajhna|bolo)", t_lower)
        if alias_match1:
            alias = alias_match1.group(1).strip()
            target = alias_match1.group(2).strip()
            msg = self.learn_alias(alias, target)
            return True, msg

        # 3. Preferences / Facts: "Mera favourite / meri pasand ... hai"
        pref_match = re.search(r"(?:mera|meri)\s+([a-zA-Z0-9\s]+)\s+([a-zA-Z0-9\s]+)\s+hai", t_lower)
        if pref_match and any(w in t_lower for w in ["favourite", "pasand", "best", "friend", "number", "kaam", "ghar", "college"]):
            msg = self.learn_fact(t, category="preference")
            return True, msg

        # 4. Behavioral Corrections: "aisa mat karo / aage se hamesha / dubara mat bolna"
        correction_triggers = ["aage se hamesha", "aisa mat", "aise mat", "ye mat bolo", "correction", "dhyan rakhna"]
        if any(trig in t_lower for trig in correction_triggers):
            msg = self.learn_correction(t)
            return True, msg

        return False, ""

    def get_memory_context_prompt(self) -> str:
        """Compiles all learned facts, rules, and preferences for the LLM system prompt"""
        context_parts = []

        if self.knowledge["learned_facts"]:
            facts = "\n".join([f"- {item['fact']}" for item in self.knowledge["learned_facts"][-15:]])
            context_parts.append(f"### Things You Have Learned About Noaman & Preferences:\n{facts}")

        if self.knowledge["corrections_and_rules"]:
            rules = "\n".join([f"- {item['rule']}" for item in self.knowledge["corrections_and_rules"][-10:]])
            context_parts.append(f"### Custom Rules & Behavioral Guidelines Given By Noaman:\n{rules}")

        if self.knowledge["learned_aliases"]:
            aliases = "\n".join([f"- '{k}' means '{v}'" for k, v in self.knowledge["learned_aliases"].items()])
            context_parts.append(f"### Learned Nicknames & Aliases:\n{aliases}")

        return "\n\n".join(context_parts)

# Global instance
learning_engine = ContinuousLearningEngine()
