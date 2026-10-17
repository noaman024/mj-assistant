import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from backend.config.settings import APP_CACHE_FILE

logger = logging.getLogger("MJ.AppLauncher")

# Common built-in and popular apps mapping
KNOWN_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "brave": "brave",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "vs code": "code",
    "vscode": "code",
    "code": "code",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "paint": "mspaint",
    "file explorer": "explorer",
    "files": "explorer",
    "explorer": "explorer",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "powershell": "powershell",
    "settings": "ms-settings:",
    "task manager": "taskmgr",
    "spotify": "spotify",
    "vlc": "vlc",
    "whatsapp": "whatsapp:",
    "discord": "discord",
    "telegram": "telegram",
    "word": "winword",
    "ms word": "winword",
    "excel": "excel",
    "ms excel": "excel",
    "powerpoint": "powerpnt",
    "capcut": "capcut",
    "blender": "blender",
    "wps": "wps",
    "wps office": "wps",
    "wps pdf": "wps",
    "youtube": "https://www.youtube.com",
    "नोटपैड": "notepad",
    "क्रोम": "chrome",
    "कैलकुलेटर": "calc",
    "व्हाट्सएप": "whatsapp:"
}

# Android package / scheme mappings for phone launching
ANDROID_APPS = {
    "whatsapp": "com.whatsapp",
    "youtube": "com.google.android.youtube",
    "instagram": "com.instagram.android",
    "camera": "android.media.action.IMAGE_CAPTURE",
    "settings": "com.android.settings",
    "chrome": "com.android.chrome",
    "spotify": "com.spotify.music",
    "telegram": "org.telegram.messenger",
    "gallery": "com.google.android.apps.photos",
    "maps": "com.google.android.apps.maps",
    "phone": "android.intent.action.DIAL"
}

class AppLauncher:
    KNOWN_APPS = KNOWN_APPS
    ANDROID_APPS = ANDROID_APPS

    def __init__(self):
        self.KNOWN_APPS = KNOWN_APPS
        self.ANDROID_APPS = ANDROID_APPS
        self.cache_file = Path(APP_CACHE_FILE)
        self.indexed_apps = {}
        self._load_cache()

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.indexed_apps = json.load(f)
            except Exception as e:
                logger.error(f"Error loading apps cache: {e}")
                self.indexed_apps = {}
        else:
            self.scan_windows_apps()

    def _save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.indexed_apps, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving apps cache: {e}")

    def scan_windows_apps(self):
        """Scans Windows Start Menu shortcuts to discover all installed applications"""
        logger.info("Scanning installed Windows applications...")
        search_dirs = [
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        ]

        found = {}
        for base_dir in search_dirs:
            if not base_dir.exists():
                continue
            for lnk in base_dir.rglob("*.lnk"):
                app_name = lnk.stem.lower()
                found[app_name] = str(lnk)

        # Merge with built-in apps
        self.indexed_apps = found
        self._save_cache()
        logger.info(f"Indexed {len(self.indexed_apps)} Windows applications.")

    def launch_laptop_app(self, app_name: str) -> bool:
        """Launches requested application on the Laptop"""
        name_clean = app_name.lower().strip()

        # 1. Check direct aliases
        if name_clean in KNOWN_APPS:
            target = KNOWN_APPS[name_clean]
            try:
                os.startfile(target)
                return True
            except Exception:
                try:
                    subprocess.Popen(target, shell=True)
                    return True
                except Exception as e:
                    logger.warning(f"Alias launch failed for {target}: {e}")

        # 2. Check indexed shortcuts
        for indexed_name, path in self.indexed_apps.items():
            if name_clean in indexed_name or indexed_name in name_clean:
                try:
                    os.startfile(path)
                    return True
                except Exception as e:
                    logger.warning(f"Shortcut launch failed for {path}: {e}")

        # 3. Direct startfile / shell execution fallback
        try:
            os.startfile(name_clean)
            return True
        except Exception:
            try:
                subprocess.Popen(name_clean, shell=True)
                return True
            except Exception as e:
                logger.error(f"Failed to launch {name_clean} on laptop: {e}")
                return False

    def launch_phone_app(self, app_name: str) -> dict:
        """Generates launch intent/signal for connected Phone companion"""
        name_clean = app_name.lower().strip()
        package = ANDROID_APPS.get(name_clean, name_clean)
        logger.info(f"Dispatching phone app launch signal for: {package}")
        return {
            "status": "dispatched",
            "device": "phone",
            "app": name_clean,
            "package": package
        }

    def launch(self, app_name: str, target: str = "laptop") -> str:
        """Smart routing: decides whether to launch on Laptop or Phone"""
        target_lower = target.lower()

        if "phone" in target_lower or "mobile" in target_lower:
            result = self.launch_phone_app(app_name)
            return f"Phone par {app_name} open karne ka signal bhej diya gaya hai."
        else:
            success = self.launch_laptop_app(app_name)
            if success:
                return f"Laptop par {app_name} open ho gaya hai."
            else:
                return f"Maaf kijiye Noaman, laptop par {app_name} nahi mil paya."

# Global instance
app_launcher = AppLauncher()
