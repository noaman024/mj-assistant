import json
import logging
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from backend.config.settings import DATA_DIR, USER_NAME

logger = logging.getLogger("MJ.SkillLearner")

SKILLS_REGISTRY_FILE = DATA_DIR / "learned_skills.json"
SKILLS_DIR = DATA_DIR / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

class SkillLearner:
    """Manages dynamic skill synthesis, registration, and persistent execution of newly learned workflows"""

    def __init__(self):
        self.skills = {}
        self._load_skills()

    def _load_skills(self):
        if SKILLS_REGISTRY_FILE.exists():
            try:
                with open(SKILLS_REGISTRY_FILE, "r", encoding="utf-8") as f:
                    self.skills = json.load(f)
            except Exception as e:
                logger.error(f"Error loading learned skills: {e}")
                self.skills = {}
        else:
            self.skills = {}

    def _save_skills(self):
        try:
            with open(SKILLS_REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.skills, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving learned skills: {e}")

    async def learn_skill(self, skill_name: str, description: str, steps_or_code: str) -> str:
        """Synthesizes and registers a brand new skill taught or discovered by Noaman"""
        from backend.core.llm_engine import llm

        clean_name = skill_name.lower().replace(" ", "_").strip()
        logger.info(f"Synthesizing new skill: '{clean_name}' - {description}")

        prompt = f"""
You are creating a reusable Python automation skill for {USER_NAME}.
Skill Name: {clean_name}
Description: {description}
Instructions / Implementation details:
{steps_or_code}

Generate a clean, reusable Python function `def run_skill(*args, **kwargs) -> str:` inside a complete script.
Return ONLY valid Python code inside ```python ``` block.
"""
        try:
            raw = await llm.generate_response(prompt)
            code = raw
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    if part.startswith("python"):
                        code = part[6:].strip()
                        break
                    elif "\n" in part:
                        code = part.strip()
                        break

            script_path = SKILLS_DIR / f"{clean_name}.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            self.skills[clean_name] = {
                "name": clean_name,
                "description": description,
                "script_path": str(script_path),
                "created_at": datetime.now().isoformat()
            }
            self._save_skills()

            return f"Maine naya skill '{clean_name}' successfully sikh liya hai Noaman! Ab se aap jab bhi bolenge, main ye kaam turant execute kar sakti hu."
        except Exception as e:
            logger.error(f"Failed to learn skill: {e}")
            return f"Naya skill save karte waqt error aaya: {e}"

    def list_learned_skills(self) -> str:
        """Returns natural language summary of all dynamically learned skills"""
        if not self.skills:
            return "Abhi tak koi naya custom skill register nahi hua hai Noaman. Aap mujhe koi bhi naya workflow sikha sakte hain!"

        summary = f"Noaman, maine abhi tak {len(self.skills)} naye skills sikhe hain:\n"
        for idx, (name, data) in enumerate(self.skills.items(), 1):
            summary += f"{idx}. {name}: {data.get('description', '')}\n"
        return summary.strip()

    def find_matching_skill(self, query: str):
        """Finds if a query matches any learned skill name or description"""
        q = query.lower().strip()
        for name, data in self.skills.items():
            clean_name = name.replace("_", " ")
            if name in q or clean_name in q:
                return name, data
            desc = data.get("description", "").lower()
            if desc and any(word in q for word in desc.split() if len(word) > 4):
                return name, data
        return None, None

    def execute_skill(self, skill_name: str, *args, **kwargs) -> str:
        """Executes a previously learned skill script"""
        clean_name = skill_name.lower().replace(" ", "_").strip()
        if clean_name not in self.skills:
            return f"Skill '{skill_name}' register nahi mila Noaman."

        skill_info = self.skills[clean_name]
        script_path = Path(skill_info["script_path"])
        if not script_path.exists():
            return f"Skill script file '{script_path}' nahi mili Noaman."

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=45,
                encoding="utf-8",
                errors="replace"
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                return output or f"Skill '{clean_name}' successfully execute ho gaya Noaman!"
            else:
                return f"Skill execute karte waqt error: {result.stderr.strip()[:150]}"
        except Exception as e:
            logger.error(f"Error executing skill {clean_name}: {e}")
            return f"Skill execute karte waqt exception aayi: {e}"

# Global instance
skill_learner = SkillLearner()
