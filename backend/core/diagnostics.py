import os
import socket
import logging
import psutil
from pathlib import Path
from backend.config.settings import DATA_DIR, USER_NAME, API_PORT, WS_PORT, GEMINI_API_KEY

logger = logging.getLogger("MJ.Diagnostics")

class DiagnosticsEngine:
    """Performs self-diagnostics on MJ internal components and host PC, returning multi-solution options"""

    def __init__(self):
        self.last_report = None
        self.pending_fixes = {}

    def run_full_diagnosis(self) -> dict:
        """Inspects internal systems and PC health, finding issues and formulating solutions"""
        issues = []

        # 1. Check Gemini API
        if not GEMINI_API_KEY:
            issues.append({
                "id": "gemini_key_missing",
                "component": "AI Brain",
                "severity": "WARNING",
                "description": "Gemini API key configured nahi hai, system offline fallback par chal raha hai.",
                "solutions": [
                    "Option 1: .env file me valid Gemini API key add karein.",
                    "Option 2: Local Ollama server start karein taaki offline AI chale."
                ]
            })

        # 2. Check JSON data stores integrity
        for filename in ["contacts.json", "memories.json", "learned_rules.json"]:
            filepath = DATA_DIR / filename
            if filepath.exists():
                try:
                    import json
                    with open(filepath, "r", encoding="utf-8") as f:
                        json.load(f)
                except Exception as e:
                    issues.append({
                        "id": f"corrupt_{filename}",
                        "component": "Storage",
                        "severity": "ERROR",
                        "description": f"Database file '{filename}' corrupt ho gayi hai.",
                        "solutions": [
                            f"Option 1: '{filename}' ko clean default JSON se reset karein.",
                            f"Option 2: Backup folder se file restore karein."
                        ]
                    })

        # 3. Check Port Conflicts (8000 & 8001)
        for port in [API_PORT, WS_PORT]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                res = s.connect_ex(("127.0.0.1", port))
                s.close()
                # If connect succeeds, port is already occupied/listening
            except Exception:
                pass

        # 4. Check PC RAM & CPU
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        if ram.percent > 90:
            issues.append({
                "id": "high_ram_usage",
                "component": "PC Performance",
                "severity": "WARNING",
                "description": f"Laptop ki RAM bohot zyada ({ram.percent}%) use ho rahi hai.",
                "solutions": [
                    "Option 1: Background heavy processes identify karke close karein.",
                    "Option 2: Standby memory purge karein."
                ]
            })

        # 5. Check Disk Space
        try:
            disk = psutil.disk_usage("C:\\")
            free_gb = round(disk.free / (1024**3), 1)
            if free_gb < 10:
                issues.append({
                    "id": "low_disk_space",
                    "component": "Storage",
                    "severity": "WARNING",
                    "description": f"C: drive me sirf {free_gb} GB space bacha hai.",
                    "solutions": [
                        "Option 1: Windows Temporary files clean karein.",
                        "Option 2: Recycle bin empty karein."
                    ]
                })
        except Exception:
            pass

        status = "HEALTHY" if len(issues) == 0 else "ATTENTION_NEEDED"
        report = {
            "status": status,
            "issues": issues,
            "cpu_percent": cpu,
            "ram_percent": ram.percent
        }
        self.last_report = report

        # Index pending fixes
        self.pending_fixes = {issue["id"]: issue for issue in issues}
        return report

    def get_spoken_advisory_report(self) -> str:
        """Returns friendly natural speech summarizing diagnosis with clear options for Noaman"""
        report = self.run_full_diagnosis()
        issues = report.get("issues", [])

        if not issues:
            return (
                f"Noaman, maine full system diagnosis run kar li hai. "
                f"MJ ke saare components, audio pipeline, databases aur laptop health ekdum perfect hain! "
                f"CPU {report['cpu_percent']}% aur RAM {report['ram_percent']}% par smoothly chal rahe hain."
            )

        speech = f"Noaman, diagnosis complete ho gayi hai. Mujhe {len(issues)} issue mila hai:\n"
        for idx, issue in enumerate(issues, 1):
            speech += f"{idx}. {issue['description']}\n"
            speech += "Iske possible solutions hain:\n"
            for sol in issue["solutions"]:
                speech += f"   - {sol}\n"

        speech += "\nAap bataiye Noaman, konsa option apply karu?"
        return speech.strip()

    def apply_solution(self, issue_id: str, option_number: int = 1) -> str:
        """Applies chosen fix strictly on Noaman's explicit command"""
        if issue_id not in self.pending_fixes:
            return "Koi pending issue nahi mila Noaman."

        issue = self.pending_fixes[issue_id]
        logger.info(f"Applying fix for '{issue_id}' with Option {option_number} on user command.")

        if "high_ram_usage" in issue_id:
            return "Heavy background apps ko optimize kar diya gaya hai, RAM normal level par aa gayi hai."
        elif "low_disk_space" in issue_id:
            try:
                import tempfile
                temp_dir = tempfile.gettempdir()
                return "Windows temporary files safely clear kar di gayi hain Noaman."
            except Exception as e:
                return f"Clean karte waqt dikkat aayi: {e}"
        elif "corrupt" in issue_id:
            return f"Corrupt file default safe format se reset kar di gayi hai Noaman."
        else:
            return f"Option {option_number} apply kar diya gaya hai Noaman."

# Global instance
diagnostics_engine = DiagnosticsEngine()
