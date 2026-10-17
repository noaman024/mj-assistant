import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from backend.config.settings import DATA_DIR, USER_NAME

logger = logging.getLogger("MJ.AutonomousExecutor")

TASKS_DIR = DATA_DIR / "autonomous_tasks"
TASKS_DIR.mkdir(parents=True, exist_ok=True)

class AutonomousExecutor:
    """Dynamically synthesizes and runs Python/PowerShell solutions for any arbitrary task requested by Noaman"""

    def __init__(self):
        pass

    async def execute_task(self, task_description: str) -> str:
        """Solves an arbitrary desktop task by synthesizing and executing safe code on the fly"""
        from backend.core.llm_engine import llm

        logger.info(f"Synthesizing autonomous solution for: '{task_description}'")

        system_prompt = f"""
You are {llm._get_active_system_instruction()}
You are an expert Python and Windows OS automation engineer.
{USER_NAME} asked you to perform this task on his computer:
"{task_description}"

Write a self-contained, safe, and efficient Python 3 script to perform this task directly on Windows.
Guidelines:
1. Use standard library or preinstalled packages (os, sys, pathlib, shutil, subprocess, json, urllib, etc.).
2. Always print a clear, concise final status message in Hinglish or English summarizing what was done.
3. Handle exceptions gracefully.
4. Do NOT include destructive system format commands or delete OS root directories.
5. Return ONLY executable Python code inside a ```python ``` block. No markdown chatter outside the block.
"""

        try:
            raw_code = await llm.generate_response(system_prompt)
            # Extract code inside ```python ``` block
            code = raw_code
            if "```" in raw_code:
                parts = raw_code.split("```")
                for part in parts:
                    if part.startswith("python"):
                        code = part[6:].strip()
                        break
                    elif "\n" in part:
                        code = part.strip()
                        break

            # Save generated script to tasks directory
            task_id = f"task_{int(time.time())}"
            script_path = TASKS_DIR / f"{task_id}.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            logger.info(f"Executing synthesized task script: {script_path}")

            # Run with subprocess
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=45,
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if not output:
                    output = "Task successfully complete ho gaya Noaman!"
                return output
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.warning(f"Script execution error: {error_msg}. Attempting self-correction...")
                # Self-correction attempt
                return await self._self_correct_and_retry(task_description, code, error_msg, script_path)

        except subprocess.TimeoutExpired:
            return "Task execute hone me 45 second se zyada samay lag gaya Noaman, isliye maine safety ke liye cancel kar diya."
        except Exception as e:
            logger.error(f"Autonomous task execution failed: {e}")
            return f"Task execute karte waqt dikkat aayi: {e}"

    async def _self_correct_and_retry(self, task_description: str, original_code: str, error: str, script_path: Path) -> str:
        """Self-corrects failed script and retries execution once"""
        from backend.core.llm_engine import llm
        prompt = f"""
The Python script you generated for: "{task_description}" failed with this error:
--- ERROR ---
{error[:1000]}
-------------

Original Code:
{original_code}

Fix the bug and return the corrected, complete executable Python script inside ```python ``` block.
"""
        try:
            corrected_raw = await llm.generate_response(prompt)
            code = corrected_raw
            if "```" in corrected_raw:
                parts = corrected_raw.split("```")
                for part in parts:
                    if part.startswith("python"):
                        code = part[6:].strip()
                        break
                    elif "\n" in part:
                        code = part.strip()
                        break

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=45,
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode == 0:
                return result.stdout.strip() or "Task successfully solve kar diya gaya hai Noaman!"
            else:
                return f"Task solve karne ki koshish ki par error aaya: {result.stderr.strip()[:150]}"
        except Exception as e:
            return f"Self-correction me issue aayi: {e}"

# Global instance
autonomous_executor = AutonomousExecutor()
