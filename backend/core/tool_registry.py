import logging
import asyncio
from backend.tools.browser_controller import browser_control
from backend.tools.call_manager import call_manager
from backend.tools.messaging import message_automator
from backend.tools.system_control import system_control
from backend.tools.app_launcher import app_launcher
from backend.tools.autonomous_executor import autonomous_executor
from backend.core.skill_learner import skill_learner
from backend.core.diagnostics import diagnostics_engine
from backend.core.security import security_vault
from backend.tools.compression_manager import compression_manager
from backend.tools.code_interpreter import code_interpreter
from backend.agents.morning_digest import morning_digest
from backend.agents.deep_research import deep_research
from backend.agents.react_agent import react_agent

logger = logging.getLogger("MJ.ToolRegistry")

# Formal Tool Declarations (Compatible with Gemini, Claude, and OpenAI tool-calling)
TOOL_DEFINITIONS = [
    {
        "name": "play_youtube",
        "description": "Directly plays a song, music track, or video on YouTube with instant autoplay",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Name of the song, artist, video, or topic to play"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "make_phone_call",
        "description": "Dials a contact or phone number using Windows Phone Link, phone PWA, or WhatsApp call",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "recipient": {"type": "STRING", "description": "Contact name (e.g. 'Rahul', 'Papa') or 10-digit phone number"}
            },
            "required": ["recipient"]
        }
    },
    {
        "name": "send_whatsapp",
        "description": "Prepares and sends a WhatsApp message to a contact",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "recipient": {"type": "STRING", "description": "Contact name or phone number"},
                "message": {"type": "STRING", "description": "The message text to send"}
            },
            "required": ["recipient"]
        }
    },
    {
        "name": "system_control",
        "description": "Controls laptop OS features like volume, mute, lock, sleep, and window management",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "Action to perform: 'volume_up', 'volume_down', 'mute', 'lock', 'sleep', 'minimize_all', 'screenshot', 'media_play_pause', 'media_next', 'media_previous'"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "get_system_stats",
        "description": "Returns current laptop CPU usage, RAM utilization, and battery status",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "launch_app",
        "description": "Opens any Windows installed application or phone app",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {"type": "STRING", "description": "Name of app to launch (e.g. 'notepad', 'chrome', 'calculator', 'code')"},
                "target_device": {"type": "STRING", "description": "Target device: 'laptop' or 'phone'"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "run_self_diagnostics",
        "description": "Runs self-health check on MJ's components and PC, reporting problems with multi-solution options",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "apply_diagnostic_solution",
        "description": "Applies a specific diagnostic repair solution when instructed by user",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "issue_id": {"type": "STRING", "description": "ID of the issue to fix"},
                "option_number": {"type": "INTEGER", "description": "Selected option number (1, 2, or 3)"}
            },
            "required": ["issue_id"]
        }
    },
    {
        "name": "execute_autonomous_task",
        "description": "Synthesizes and runs dynamic code for any arbitrary computer task not covered by standard tools",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "task_description": {"type": "STRING", "description": "Detailed explanation of what computer action or script to execute"}
            },
            "required": ["task_description"]
        }
    },
    {
        "name": "learn_new_skill",
        "description": "Learns and permanently saves a new task or workflow taught or discovered by user",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "skill_name": {"type": "STRING", "description": "Short name for the skill"},
                "description": {"type": "STRING", "description": "What the skill does"},
                "steps_or_code": {"type": "STRING", "description": "Step-by-step instructions or logic"}
            },
            "required": ["skill_name", "description"]
        }
    },
    {
        "name": "unlock_privacy_vault",
        "description": "Validates the user's secret voice passcode to unlock private data and protected actions",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "passcode": {"type": "STRING", "description": "Spoken secret passcode"}
            },
            "required": ["passcode"]
        }
    },
    {
        "name": "create_zip_backup",
        "description": "Compresses active data, memories, and skills into a high-compression ZIP archive to save storage and RAM",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "custom_name": {"type": "STRING", "description": "Optional name for the backup archive"}
            }
        }
    },
    {
        "name": "list_zip_contents",
        "description": "Inspects and lists all files inside a ZIP archive without extracting it",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "zip_filename": {"type": "STRING", "description": "Name or path of ZIP archive"}
            }
        }
    },
    {
        "name": "extract_zip_archive",
        "description": "Extracts files from a ZIP archive safely into a folder",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "zip_filename": {"type": "STRING", "description": "Name of the archive to extract"},
                "destination_folder": {"type": "STRING", "description": "Destination subfolder name"}
            }
        }
    },
    {
        "name": "optimize_storage",
        "description": "Automatically moves old tasks and screenshots into compressed ZIP to free up host storage and memory",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "execute_python_code",
        "description": "Safely runs sandboxed Python code with AST security validation and returns output",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "code": {"type": "STRING", "description": "Python source code snippet to execute"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "deep_research",
        "description": "Performs multi-hop web and local research on a complex topic with cited reports",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "topic": {"type": "STRING", "description": "Subject or question to thoroughly investigate"}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "morning_digest",
        "description": "Synthesizes an energetic spoken morning briefing covering PC health, tasks, and calls",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "react_agent_task",
        "description": "Executes complex multi-step computer tasks via autonomous ReAct reasoning loop",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal": {"type": "STRING", "description": "Multi-step goal to solve"}
            },
            "required": ["goal"]
        }
    }
]

class ToolExecutor:
    """Executes tools by name with given parameters"""

    async def execute(self, tool_name: str, args: dict) -> str:
        logger.info(f"Executing tool '{tool_name}' with args: {args}")
        try:
            if tool_name == "play_youtube":
                return browser_control.youtube_play(args.get("query", ""))

            elif tool_name == "make_phone_call":
                return await call_manager.dial_contact(args.get("recipient", ""))

            elif tool_name == "send_whatsapp":
                recipient = args.get("recipient", "")
                message = args.get("message", "")
                success, prompt, _ = message_automator.prepare_whatsapp_message(recipient, message)
                return prompt

            elif tool_name == "system_control":
                action = args.get("action", "")
                if action == "volume_up":
                    return system_control.volume_up()
                elif action == "volume_down":
                    return system_control.volume_down()
                elif action == "mute":
                    return system_control.mute()
                elif action == "minimize_all":
                    return system_control.minimize_all()
                elif action == "lock":
                    return system_control.lock_pc()
                elif action == "sleep":
                    return system_control.sleep_pc()
                elif action == "screenshot":
                    _, res = system_control.take_screenshot()
                    return res
                elif action == "media_play_pause":
                    return browser_control.media_play_pause()
                elif action == "media_next":
                    return browser_control.media_next()
                elif action == "media_previous":
                    return browser_control.media_previous()
                return "Unknown system action"

            elif tool_name == "get_system_stats":
                return system_control.get_system_stats()

            elif tool_name == "launch_app":
                app_name = args.get("app_name", "")
                target = args.get("target_device", "laptop")
                return app_launcher.launch(app_name, target=target)

            elif tool_name == "run_self_diagnostics":
                return diagnostics_engine.get_spoken_advisory_report()

            elif tool_name == "apply_diagnostic_solution":
                issue_id = args.get("issue_id", "")
                opt = args.get("option_number", 1)
                return diagnostics_engine.apply_solution(issue_id, opt)

            elif tool_name == "execute_autonomous_task":
                return await autonomous_executor.execute_task(args.get("task_description", ""))

            elif tool_name == "learn_new_skill":
                return await skill_learner.learn_skill(
                    args.get("skill_name", ""),
                    args.get("description", ""),
                    args.get("steps_or_code", "")
                )

            elif tool_name == "unlock_privacy_vault":
                _, msg = security_vault.authenticate(args.get("passcode", ""))
                return msg

            elif tool_name == "create_zip_backup":
                name = args.get("custom_name")
                return compression_manager.create_data_backup(name)

            elif tool_name == "list_zip_contents":
                name = args.get("zip_filename")
                return compression_manager.list_archive_contents(name)

            elif tool_name == "extract_zip_archive":
                name = args.get("zip_filename")
                dest = args.get("destination_folder", "extracted_data")
                return compression_manager.extract_archive(name, dest)

            elif tool_name == "optimize_storage":
                return compression_manager.auto_optimize_storage()

            elif tool_name == "execute_python_code":
                res = code_interpreter.execute(args.get("code", ""))
                if res["success"]:
                    return f"Execution Successful (in {res['latency_ms']}ms):\n{res['output']}"
                else:
                    return f"Execution Error: {res['error']}"

            elif tool_name == "deep_research":
                topic = args.get("topic", "")
                res = await deep_research.research(topic)
                return res["report"]

            elif tool_name == "morning_digest":
                return await morning_digest.generate_briefing()

            elif tool_name == "react_agent_task":
                goal = args.get("goal", "")
                return await react_agent.execute_task(goal)

            return f"Tool '{tool_name}' mila nahi Noaman."
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return f"Action execute karte waqt error aaya: {e}"

# Global instance
tool_executor = ToolExecutor()
