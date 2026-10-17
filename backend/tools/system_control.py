import os
import ctypes
import logging
from datetime import datetime
from pathlib import Path
import pyautogui
import psutil

pyautogui.FAILSAFE = False
from backend.config.settings import DATA_DIR

logger = logging.getLogger("MJ.SystemControl")

SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

class SystemController:
    def __init__(self):
        pass

    # --- Volume Controls ---
    def volume_up(self, steps: int = 5) -> str:
        for _ in range(steps):
            pyautogui.press("volumeup")
        return "Volume badha diya hai."

    def volume_down(self, steps: int = 5) -> str:
        for _ in range(steps):
            pyautogui.press("volumedown")
        return "Volume kam kar diya hai."

    def mute(self) -> str:
        pyautogui.press("volumemute")
        return "Volume mute/unmute kar diya hai."

    # --- Window & Display Controls ---
    def minimize_all(self) -> str:
        pyautogui.hotkey("win", "d")
        return "Saari windows minimize kar di hain."

    def switch_window(self) -> str:
        pyautogui.hotkey("alt", "tab")
        return "Window switch kar di hai."

    def close_active_window(self) -> str:
        pyautogui.hotkey("alt", "f4")
        return "Active window close kar di hai."

    # --- Power & Security Controls ---
    def lock_pc(self) -> str:
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Laptop lock kar diya hai."
        except Exception as e:
            logger.error(f"Error locking PC: {e}")
            return "Lock karne me dikkat aayi."

    def sleep_pc(self) -> str:
        try:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "Laptop sleep mode me daal diya hai."
        except Exception as e:
            logger.error(f"Error sleeping PC: {e}")
            return "Sleep karne me dikkat aayi."

    # --- Battery & Diagnostics ---
    def get_system_stats(self) -> str:
        battery = psutil.sensors_battery()
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()

        status_text = f"CPU use {cpu_usage}% hai, RAM {ram.percent}% used hai."
        if battery:
            plugged = "charger laga hai" if battery.power_plugged else "battery par chal raha hai"
            status_text += f" Battery {battery.percent}% hai aur {plugged}."
        return status_text

    # --- Screen Vision & Screenshot ---
    def _capture_screen_image(self):
        try:
            return pyautogui.screenshot()
        except Exception:
            try:
                from PIL import ImageGrab
                return ImageGrab.grab(all_screens=True)
            except Exception as e:
                logger.warning(f"Screen capture fallback triggered: {e}")
                from PIL import Image, ImageDraw
                img = Image.new("RGB", (960, 540), color=(10, 16, 26))
                draw = ImageDraw.Draw(img)
                draw.text((360, 260), "Desktop Display Locked / Standby", fill=(0, 240, 255))
                return img

    def take_screenshot(self) -> tuple[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = SCREENSHOTS_DIR / f"screenshot_{timestamp}.png"
        screenshot = self._capture_screen_image()
        screenshot.save(filepath)
        logger.info(f"Screenshot saved to {filepath}")
        return str(filepath), "Screen capture kar li hai."

    def get_screen_jpeg_bytes(self, max_width: int = 960, quality: int = 55) -> bytes:
        """Captures screen in-memory, scales it down, and returns compressed JPEG bytes for real-time mobile streaming"""
        import io
        img = self._capture_screen_image()
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            img = img.resize((max_width, new_height))
        
        # Convert RGB if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()

# Global instance
system_control = SystemController()
