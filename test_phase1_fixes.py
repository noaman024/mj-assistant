import asyncio
from backend.tools.browser_controller import browser_control
from backend.tools.call_manager import call_manager
from backend.tools.messaging import message_automator

def test_phase1():
    print("=" * 60)
    print("      MJ ASSISTANT - PHASE 1 VERIFICATION TEST SUITE")
    print("       (Autoplay, Call Manager, Conversational WhatsApp)")
    print("=" * 60)

    # 1. YouTube Autoplay Test
    print("\n[Test 1] Testing YouTube Direct Autoplay...")
    res1 = browser_control.youtube_play("alfaaz")
    print(f"  -> Result: {res1}")
    assert "YouTube par 'alfaaz'" in res1, "YouTube playback string failed"
    print("--> Test 1 Passed (YouTube Autoplay verified)!")

    # 2. Call Manager Test (Phone Link & PWA dispatch)
    print("\n[Test 2] Testing Call Manager Dialing ('Rahul')...")
    res2 = asyncio.run(call_manager.dial_contact("Rahul"))
    print(f"  -> Result: {res2}")
    assert "Rahul" in res2 and "9876543210" in res2, "Call dispatch failed"
    print("--> Test 2 Passed (Call Manager verified)!")

    # 3. Two-Turn Conversational Messaging
    print("\n[Test 3] Testing Conversational WhatsApp (When message text is missing)...")
    success3, prompt3, payload3 = message_automator.prepare_whatsapp_message("Rahul", "")
    print(f"  -> Prompt: {prompt3}")
    assert success3 is False, "Should wait for message content"
    assert "Rahul ko kya WhatsApp message bhejna hai" in prompt3, "Did not prompt for missing message text"
    assert message_automator.awaiting_message_for == "Rahul", "Awaiting state not set"
    print("--> Test 3 Passed (Conversational Message Prompt verified)!")

    # 4. WhatsApp Message with Content
    print("\n[Test 4] Testing WhatsApp with Content ('Meeting me hu')...")
    success4, prompt4, payload4 = message_automator.prepare_whatsapp_message("Rahul", "Meeting me hu")
    print(f"  -> Prompt: {prompt4}")
    assert success4 is True, "Preparation should succeed"
    assert payload4["phone"] == "919876543210", f"Phone mismatch: {payload4['phone']}"
    assert payload4["message"] == "Meeting me hu", "Message mismatch"
    print("--> Test 4 Passed (Full WhatsApp payload verified)!")

    print("\n" + "=" * 60)
    print("ALL PHASE 1 FIXES (AUTOPLAY, CALL, CONVERSATIONAL MSG) PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase1()
