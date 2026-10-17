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
from backend.call_screening import call_screener
from backend.core.orchestrator import orchestrator
from backend.voice.tts import tts

client = TestClient(app)

async def run_phase5_tests():
    # Mock TTS for fast execution
    tts.speak = AsyncMock()

    print("=" * 65)
    print("      MJ ASSISTANT - PHASE 5 VERIFICATION TEST SUITE")
    print("       (AI Call Screening & Smart Voicemail)")
    print("=" * 65)

    # 1. Interactive Voice Greeting
    print("\n[Test 1] Testing Interactive Auto-Pickup Voice Greeting...")
    prompt = call_screener.get_screening_prompt("Rahul")
    print(f"  -> Spoken Prompt: '{prompt}'")
    assert "MJ" in prompt and "Noaman" in prompt
    assert "Namaste" not in prompt  # Strict tone rule compliance
    print("--> Test 1 Passed!")

    # 2. Voicemail Ingestion & AI Analysis
    print("\n[Test 2] Testing Voicemail Ingestion & AI Analysis...")
    sample_transcript = "Bhai jaldi college aaja, practical exam shuru hone wali hai!"
    entry = await call_screener.process_incoming_voicemail(
        phone_number="+919876543210",
        transcript=sample_transcript,
        caller_name="Rahul"
    )
    assert entry is not None
    assert entry["caller_name"] == "Rahul"
    assert entry["urgency"] in ["URGENT", "IMPORTANT"]
    assert len(entry["summary"]) > 0
    print(f"  -> Analyzed Entry: Caller={entry['caller_name']} | Urgency={entry['urgency']}")
    print(f"  -> Summary: \"{entry['summary']}\"")
    print("--> Test 2 Passed!")

    # 3. Persistent Storage Verification
    print("\n[Test 3] Testing Persistent Storage in voicemails.json...")
    assert len(call_screener.voicemails) > 0
    top_vm = call_screener.voicemails[0]
    assert top_vm["caller_name"] == "Rahul"
    print(f"  -> Voicemails Count: {len(call_screener.voicemails)} | Top ID: {top_vm['id']}")
    print("--> Test 3 Passed!")

    # 4. REST API Endpoints (/api/call/voicemails & /api/call/voicemail)
    print("\n[Test 4] Testing Call Screening REST APIs...")
    res_list = client.get("/api/call/voicemails")
    assert res_list.status_code == 200
    data = res_list.json()
    assert "voicemails" in data and len(data["voicemails"]) > 0
    print(f"  -> GET /api/call/voicemails returned {len(data['voicemails'])} voicemails.")

    # Ingest another voicemail via API
    res_post = client.post("/api/call/voicemail", json={
        "caller_name": "Papa",
        "phone_number": "+919988776655",
        "transcript": "Beta ghar aate waqt dahi le aana."
    })
    assert res_post.status_code == 200
    vm_papa = res_post.json()["voicemail"]
    assert vm_papa["caller_name"] == "Papa"
    print(f"  -> POST /api/call/voicemail created: {vm_papa['caller_name']} - \"{vm_papa['summary']}\"")
    print("--> Test 4 Passed!")

    # 5. Voice Interaction via Assistant Orchestrator
    print("\n[Test 5] Testing Voice Voicemail Check Query...")
    res_query = await orchestrator.process_command("Koi voicemail aayi hai kya?")
    print(f"  -> Command: 'Koi voicemail aayi hai kya?' | Result: \"{res_query}\"")
    assert "voicemail" in res_query.lower() or "rahul" in res_query.lower()

    # Clear / Mark Read
    res_clear = await orchestrator.process_command("Voicemail clear karo")
    print(f"  -> Command: 'Voicemail clear karo' | Result: \"{res_clear}\"")
    assert len(call_screener.get_unread_voicemails()) == 0
    print("--> Test 5 Passed!")

    print("\n" + "=" * 65)
    print("ALL PHASE 5 AI CALL SCREENING TESTS PASSED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_phase5_tests())
