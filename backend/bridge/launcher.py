import os
import sys
import time
import shutil
import subprocess
import logging

logger = logging.getLogger("MJ.DesktopLauncher")

def find_browser_executable() -> str | None:
    """Finds Chrome, Edge, or Brave executable on Windows"""
    candidates = [
        # Chrome paths
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        # Edge paths
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        # Brave paths
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    # Fallback to which
    for name in ["chrome", "msedge", "brave"]:
        found = shutil.which(name)
        if found:
            return found

    return None

def launch_desktop_app(port: int = 8000, path: str = "desktop") -> bool:
    """Launches the Futuristic Desktop UI in native standalone application window mode"""
    url = f"http://127.0.0.1:{port}/{path}"
    browser_exe = find_browser_executable()

    if browser_exe:
        logger.info(f"Launching MJ Standalone Desktop Cockpit via: {browser_exe}")
        cmd = [
            browser_exe,
            f"--app={url}",
            "--window-size=1300,840",
            "--window-position=100,60"
        ]
        try:
            subprocess.Popen(cmd)
            return True
        except Exception as e:
            logger.warning(f"Could not launch browser app mode: {e}")

    # Fallback to standard default browser
    try:
        import webbrowser
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        return False

if __name__ == "__main__":
    launch_desktop_app()
