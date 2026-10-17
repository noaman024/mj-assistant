import asyncio
from unittest.mock import AsyncMock
from backend.core.orchestrator import orchestrator
from backend.tools.contact_manager import contact_manager
from backend.tools.messaging import message_automator
from backend.voice.tts import tts

async def run_phase3_tests():
    # Mock TTS so test runs immediately without blocking audio playback
    tts.speak = AsyncMock()

    print("=" * 60)
    print("      MJ ASSISTANT - PHASE 3 VERIFICATION TEST SUITE")
    print("=" * 60)

    # 1. Contact Lookup Test
    print("\n[Test 1] Contact Lookup ('Rahul ka number batao')...")
    res1 = await orchestrator.process_command("Rahul ka number batao")
    print(f"Result: {res1}")
    assert "9876543210" in res1, f"Failed: Rahul's number not found in '{res1}'"
    print("--> Test 1 Passed!")

    # 2. Add / Save Contact Test
    print("\n[Test 2] Add New Contact ('Sameer ka number 9988776655 save karo')...")
    res2 = await orchestrator.process_command("Sameer ka number 9988776655 save karo")
    print(f"Result: {res2}")
    contact = contact_manager.find_contact("Sameer")
    assert contact is not None and "9988776655" in contact["phone"], "Failed: Sameer's contact not saved!"
    print("--> Test 2 Passed!")

    # 3. Message Preparation & Safety Confirmation
    print("\n[Test 3] Prepare Message ('Rahul ko WhatsApp par bolo ki meeting me hu')...")
    res3 = await orchestrator.process_command("Rahul ko WhatsApp par bolo ki meeting me hu")
    print(f"Result: {res3}")
    assert message_automator.pending_message is not None, "Failed: Pending message not set!"
    assert "meeting me hu" in message_automator.pending_message["message"]
    print("--> Test 3 Passed (Confirmation prompt ready)!")

    # 4. Message Cancellation
    print("\n[Test 4] Voice Safety Cancel ('Nahi, mat bhejo')...")
    res4 = await orchestrator.process_command("Nahi mat bhejo")
    print(f"Result: {res4}")
    assert message_automator.pending_message is None, "Failed: Message was not cancelled!"
    print("--> Test 4 Passed (Successfully cancelled)!")

    # 5. Message Re-preparation & Safety Payload Validation
    print("\n[Test 5] Prepare & Confirm Flow...")
    res5 = await orchestrator.process_command("Sameer ko message karo: Main 10 min me aa raha hu")
    print(f"Prompt: {res5}")
    assert message_automator.pending_message is not None
    
    # Check payload before confirm
    p = message_automator.pending_message
    print(f"Pending Payload: Recipient={p['recipient']}, Phone={p['phone']}, Text='{p['message']}'")
    assert p["recipient"] == "Sameer"
    assert "10 min me aa raha hu" in p["message"]

    # Clear payload so it doesn't leave state dirty
    message_automator.pending_message = None
    print("--> Test 5 Passed (Payload & workflow valid)!")

    print("\n" + "=" * 60)
    print("ALL PHASE 3 HANDS-FREE VOICE MESSAGING TESTS PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_phase3_tests())
