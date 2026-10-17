import sys
import asyncio

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from backend.bridge.server import app
from backend.bridge.phone_hub import phone_hub
from backend.core.orchestrator import orchestrator
from backend.voice.tts import tts

client = TestClient(app)

async def run_phase4_tests():
    # Mock TTS for fast non-blocking execution
    tts.speak = AsyncMock()

    print("=" * 65)
    print("      MJ ASSISTANT - PHASE 4 VERIFICATION TEST SUITE")
    print("       (Cross-Device Ecosystem: Phone <-> Laptop)")
    print("=" * 65)

    # 1. PWA & Web Controller Endpoints
    print("\n[Test 1] Testing PWA & Web Controller Endpoints...")
    res_index = client.get("/")
    assert res_index.status_code == 200, f"Failed: Index returned {res_index.status_code}"
    assert "MJ" in res_index.text and "Noaman" in res_index.text
    print("  -> GET / returned PWA Web Controller successfully.")

    res_manifest = client.get("/manifest.json")
    assert res_manifest.status_code == 200
    assert res_manifest.json().get("name") == "MJ Mobile Controller"
    print("  -> GET /manifest.json returned valid PWA manifest.")

    res_status = client.get("/api/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert "laptop" in status_data and "phone" in status_data
    print(f"  -> GET /api/status returned Laptop CPU ({status_data['laptop']['cpu']}%) and Phone status.")
    print("--> Test 1 Passed!")

    # 2. Remote Command Execution from Phone to Laptop
    print("\n[Test 2] Testing Remote Command Dispatch from Phone...")
    res_cmd = client.post("/api/command", json={"query": "volume badhao", "source": "phone"})
    assert res_cmd.status_code == 200
    assert res_cmd.json()["status"] == "success"
    print(f"  -> Dispatched: 'volume badhao' | Response: {res_cmd.json()['response']}")
    print("--> Test 2 Passed!")

    # 3. Live Screen Mirror Snapshot Stream
    print("\n[Test 3] Testing High-Speed Live Screen Snapshot...")
    res_screen = client.get("/api/screen/snapshot")
    assert res_screen.status_code == 200
    assert res_screen.headers["content-type"] == "image/jpeg"
    assert len(res_screen.content) > 1000  # Valid non-empty JPEG
    print(f"  -> GET /api/screen/snapshot captured JPEG screen frame ({len(res_screen.content)} bytes).")
    print("--> Test 3 Passed!")

    # 4. Find My Phone (Loud Ringing Siren)
    print("\n[Test 4] Testing Find My Phone Voice Trigger...")
    # Simulate a phone connected to hub
    phone_hub.phone_status["connected"] = True

    res_ring = await orchestrator.process_command("Mera phone dhundo")
    print(f"  -> Command: 'Mera phone dhundo' | Result: '{res_ring}'")
    assert "alarm" in res_ring.lower() or "phone" in res_ring.lower()
    assert phone_hub.phone_status["is_ringing"] is True

    # Stop Ring
    res_stop = await orchestrator.process_command("Alarm band karo")
    print(f"  -> Command: 'Alarm band karo' | Result: '{res_stop}'")
    assert phone_hub.phone_status["is_ringing"] is False
    print("--> Test 4 Passed (Find My Phone & Stop Ring validated)!")

    # 5. Phone Battery Telemetry Reporting
    print("\n[Test 5] Testing Phone Battery Status Monitoring...")
    # Simulate Phone PWA sending battery status via WebSocket / API
    phone_hub.update_phone_telemetry(battery=82, charging=True, device="Noaman's Android Phone")
    
    res_batt = await orchestrator.process_command("Phone ki battery kitni hai?")
    print(f"  -> Command: 'Phone ki battery kitni hai?' | Result: '{res_batt}'")
    assert "82%" in res_batt and "charger" in res_batt
    print("--> Test 5 Passed (Phone battery accurately reported)!")

    # 6. Bidirectional App Routing (Phone vs Laptop)
    print("\n[Test 6] Testing Bidirectional Smart App Routing...")
    # Phone target
    res_phone_app = await orchestrator.process_command("Phone par WhatsApp open karo")
    print(f"  -> Command: 'Phone par WhatsApp open karo' | Result: '{res_phone_app}'")
    assert "phone" in res_phone_app.lower()

    # Laptop target
    res_laptop_app = await orchestrator.process_command("Laptop par Notepad open karo")
    print(f"  -> Command: 'Laptop par Notepad open karo' | Result: '{res_laptop_app}'")
    assert "laptop" in res_laptop_app.lower()
    print("--> Test 6 Passed (Smart device-aware routing verified)!")

    # 7. Cross-Device Wireless Clipboard Sync
    print("\n[Test 7] Testing Cross-Device Clipboard Sync...")
    clip_text = "MJ Assistant Test Clipboard Sync - Secret Code 1234"
    res_clip = client.post("/api/clipboard", json={"text": clip_text})
    assert res_clip.status_code == 200
    assert phone_hub.clipboard_content == clip_text
    print(f"  -> Clipboard synced successfully: '{phone_hub.clipboard_content[:30]}...'")
    print("--> Test 7 Passed!")

    print("\n" + "=" * 65)
    print("ALL PHASE 4 CROSS-DEVICE ECOSYSTEM TESTS PASSED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_phase4_tests())
