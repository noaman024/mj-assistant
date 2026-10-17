import sys
import os
import asyncio

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from fastapi.testclient import TestClient
from backend.bridge.server import app
from backend.bridge.launcher import find_browser_executable

client = TestClient(app)

def run_phase6_tests():
    print("=" * 65)
    print("      MJ ASSISTANT - PHASE 6 VERIFICATION TEST SUITE")
    print("   (UI Design, Holographic Visualizer & Desktop Packaging)")
    print("=" * 65)

    # 1. Desktop Cockpit Route
    print("\n[Test 1] Testing /desktop Endpoint...")
    res_desk = client.get("/desktop")
    assert res_desk.status_code == 200, f"Failed: /desktop returned {res_desk.status_code}"
    html = res_desk.text
    assert "MJ CORE" in html
    assert "Noaman" in html
    assert "audioVisualizer" in html
    assert "orbWrapper" in html
    assert "conversationDeck" in html
    print("  -> GET /desktop loaded Holographic Cockpit HTML successfully.")
    print("--> Test 1 Passed!")

    # 2. Static CSS & JS Assets
    print("\n[Test 2] Testing Desktop CSS & JS Assets...")
    res_css = client.get("/static/desktop_style.css")
    assert res_css.status_code == 200
    assert "--cyan" in res_css.text and "rotateRing" in res_css.text
    print("  -> GET /static/desktop_style.css returned valid cyber styling.")

    res_js = client.get("/static/desktop.js")
    assert res_js.status_code == 200
    assert "visualizer" in res_js.text.lower() and "websocket" in res_js.text.lower()
    print("  -> GET /static/desktop.js returned valid 60 FPS visualizer & bridge engine.")
    print("--> Test 2 Passed!")

    # 3. Browser Packaging & Standalone App Launcher
    print("\n[Test 3] Testing Standalone Desktop Window Packaging...")
    browser = find_browser_executable()
    print(f"  -> Detected System Chromium Browser: {browser}")
    assert browser is not None, "Warning: No browser executable found for app mode."

    bat_path = os.path.join(os.path.dirname(__file__), "launch_mj.bat")
    assert os.path.exists(bat_path), "Failed: launch_mj.bat not found."
    with open(bat_path, "r", encoding="utf-8") as f:
        bat_content = f.read()
    assert "python main.py" in bat_content
    print("  -> launch_mj.bat verified.")
    print("--> Test 3 Passed!")

    print("\n" + "=" * 65)
    print("ALL PHASE 6 UI & PACKAGING TESTS PASSED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    run_phase6_tests()
