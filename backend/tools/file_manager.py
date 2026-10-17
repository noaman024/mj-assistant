import os
import logging
from pathlib import Path

logger = logging.getLogger("MJ.FileManager")

USER_HOME = Path.home()
DESKTOP_DIR = USER_HOME / "Desktop"
DOCUMENTS_DIR = USER_HOME / "Documents"
DOWNLOADS_DIR = USER_HOME / "Downloads"

class FileManager:
    def __init__(self):
        pass

    def create_text_file(self, filename: str, content: str = "", location: str = "desktop") -> str:
        """Create a text file on Desktop or Documents"""
        target_dir = DESKTOP_DIR if location.lower() == "desktop" else DOCUMENTS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        if not filename.endswith(".txt"):
            filename += ".txt"

        filepath = target_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"File created at {filepath}")
            return f"{location.capitalize()} par '{filename}' file create kar di hai."
        except Exception as e:
            logger.error(f"Error creating file {filename}: {e}")
            return f"File banane me dikkat aayi: {e}"

    def search_file(self, query: str, search_in: str = "desktop") -> str:
        """Search for a file on Desktop, Downloads, or Documents"""
        base_dir = DESKTOP_DIR if search_in == "desktop" else DOWNLOADS_DIR
        query_lower = query.lower()

        matches = []
        try:
            for item in base_dir.rglob(f"*{query}*"):
                if item.is_file():
                    matches.append(item.name)
                if len(matches) >= 5:
                    break
        except Exception:
            pass

        if matches:
            return f"Files mil gayi: {', '.join(matches)}"
        return f"'{query}' naam ki koi file nahi mili."

# Global instance
file_manager = FileManager()
