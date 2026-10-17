import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.diagnostics import diagnostics_engine
from backend.core.security import security_vault
from backend.core.skill_learner import skill_learner
from backend.tools.autonomous_executor import autonomous_executor
from backend.core.orchestrator import orchestrator

async def run_tests():
    print("=" * 65)
    print("   MJ ASSISTANT - JARVIS CAPABILITY VERIFICATION SUITE")
    print(" (Autonomous Executor, Dynamic Skills, Self-Healing, Privacy)")
    print("=" * 65)

    # 1. Diagnostics & Advisory Engine
    print("\n[Test 1] Diagnostics & Health Check...")
    diag_report = diagnostics_engine.run_full_diagnosis()
    print(f"  -> System Status: {diag_report['status']}")
    print(f"  -> CPU: {diag_report['cpu_percent']}%, RAM: {diag_report['ram_percent']}%")
    spoken_diag = diagnostics_engine.get_spoken_advisory_report()
    print(f"  -> Spoken Advisory Preview: {spoken_diag[:120]}...")
    assert "Noaman" in spoken_diag, "Advisory must address Noaman"
    print("--> Test 1 Passed (Diagnostics Engine Verified)!")

    # 2. Diagnostics Multi-Solution Application
    print("\n[Test 2] Diagnostics Multi-Solution Application...")
    fix_res = diagnostics_engine.apply_solution("low_disk_space", 1)
    print(f"  -> Fix Result: {fix_res}")
    assert "Noaman" in fix_res, "Fix response should address Noaman"
    print("--> Test 2 Passed (Solution Application Verified)!")

    # 3. Privacy Vault & Secret Word Authentication
    print("\n[Test 3] Security Vault & Secret Passcode...")
    # Lock vault
    lock_res = security_vault.lock_vault()
    print(f"  -> Lock: {lock_res}")
    assert security_vault.is_unlocked() is False, "Vault should be locked"

    # Challenge
    allowed, prompt = security_vault.challenge_action("open private documents")
    print(f"  -> Challenge: {prompt}")
    assert allowed is False, "Private action should be challenged"
    assert "Secret Word" in prompt or "secret" in prompt.lower()

    # Authenticate with correct passphrase ("jarvis")
    auth_ok, auth_msg = security_vault.authenticate("jarvis")
    print(f"  -> Auth Result: {auth_msg}")
    assert auth_ok is True, "Authentication should succeed with passcode"
    assert security_vault.is_unlocked() is True, "Vault should now be unlocked"
    print("--> Test 3 Passed (Security Vault Verified)!")

    # 4. Dynamic Skill Learner
    print("\n[Test 4] Dynamic Skill Learner (Registration & Execution)...")
    # Manually register a test skill
    test_skill_name = "test_greeting_skill"
    test_skill_file = Path("data/skills/test_greeting_skill.py")
    test_skill_file.parent.mkdir(parents=True, exist_ok=True)
    with open(test_skill_file, "w", encoding="utf-8") as f:
        f.write('print("Hello Noaman! Dynamic skill executed successfully.")\n')

    skill_learner.skills[test_skill_name] = {
        "name": test_skill_name,
        "description": "Prints a dynamic greeting test",
        "script_path": str(test_skill_file)
    }
    skill_learner._save_skills()

    # List skills
    skills_list = skill_learner.list_learned_skills()
    print(f"  -> Skills List Preview: {skills_list[:80]}...")
    assert test_skill_name in skills_list

    # Execute skill
    exec_res = skill_learner.execute_skill(test_skill_name)
    print(f"  -> Execution Output: {exec_res}")
    assert "Dynamic skill executed successfully" in exec_res
    print("--> Test 4 Passed (Dynamic Skills Verified)!")

    # 5. Autonomous Task Execution (Local script execution test)
    print("\n[Test 5] Autonomous Executor (Safe Code Run)...")
    task_res = await autonomous_executor.execute_task("calculate 25 * 40 and check python version")
    print(f"  -> Autonomous Task Result: {task_res}")
    assert len(task_res) > 0, "Autonomous task should return a non-empty status"
    print("--> Test 5 Passed (Autonomous Executor Verified)!")

    # 6. Orchestrator Integration Test on High-Level Commands
    print("\n[Test 6] Orchestrator Integration on Jarvis Commands...")
    
    # 6a. Diagnostics query
    cmd_res = await orchestrator.process_command("system check karo koi problem hai kya")
    print(f"  -> Command 'system check': {cmd_res[:80]}...")
    assert "Noaman" in cmd_res

    # 6b. Media Controls
    media_res = await orchestrator.process_command("pause gana")
    print(f"  -> Command 'pause gana': {media_res}")
    assert "Media play" in media_res

    # 6c. Skills listing
    skills_res = await orchestrator.process_command("kya seekha hai batao")
    print(f"  -> Command 'kya seekha hai': {skills_res[:80]}...")
    assert "skills" in skills_res.lower() or "Noaman" in skills_res

    # 6d. Direct Calling
    call_res = await orchestrator.process_command("Rahul ko call lagao")
    print(f"  -> Command 'call Rahul': {call_res}")
    assert "Rahul" in call_res

    print("\n" + "=" * 65)
    print("ALL JARVIS CAPABILITY TESTS PASSED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_tests())
