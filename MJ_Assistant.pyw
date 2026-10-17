#!/usr/bin/env python3
"""
MJ Assistant - Standalone Windows Desktop Software
Runs Background Bridge Server + Launches Holographic Cyberpunk Cockpit Window.
"""

import sys
import os
import time
import threading
from pathlib import Path

# Set root directory
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

# Ensure required directories exist
(CURRENT_DIR / "data").mkdir(exist_ok=True)
(CURRENT_DIR / "data" / "skills").mkdir(parents=True, exist_ok=True)
(CURRENT_DIR / "data" / "autonomous_tasks").mkdir(parents=True, exist_ok=True)

def _start_bridge_server():
    """Runs the bridge server in background for desktop & mobile phone sync"""
    try:
        import uvicorn
        from backend.bridge.server import app
        from backend.config.settings import API_PORT
        uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="warning")
    except Exception as e:
        pass

if __name__ == "__main__":
    # 1. Start Server in background daemon thread
    server_thread = threading.Thread(target=_start_bridge_server, daemon=True)
    server_thread.start()
    time.sleep(1.0)

    # 2. Launch Futuristic Desktop Cockpit in Standalone Native Window Mode
    from backend.bridge.launcher import launch_desktop_app
    launch_desktop_app(port=8000, path="desktop")

    # 3. Keep daemon alive
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

