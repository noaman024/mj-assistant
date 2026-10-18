"""
ReAct Autonomous Agent & Loop Guard for MJ Assistant.
Adapted from OpenJarvis native_react.py & loop_guard.py:
Provides multi-step Thought-Action-Observation execution
with loop detection, timeout prevention, and tool routing.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional

from backend.config.settings import USER_NAME, ASSISTANT_NAME
from backend.core.llm_engine import llm

logger = logging.getLogger("MJ.ReActAgent")


class LoopGuard:
    """Detects cycles, repetition, and runaway tool invocation."""
    def __init__(self, max_steps: int = 5):
        self.max_steps = max_steps
        self.step_history: List[str] = []

    def check_and_record(self, action_signature: str) -> bool:
        """Returns True if action is allowed, False if loop detected or limit reached."""
        if len(self.step_history) >= self.max_steps:
            logger.warning(f"LoopGuard: Max steps limit ({self.max_steps}) reached.")
            return False

        # Detect immediate duplicate actions (action called 2+ times with exact same arguments)
        if len(self.step_history) >= 2 and self.step_history[-1] == action_signature and self.step_history[-2] == action_signature:
            logger.warning(f"LoopGuard: Repetitive cycle detected for action '{action_signature}'.")
            return False

        self.step_history.append(action_signature)
        return True


class ReActAgent:
    def __init__(self, max_steps: int = 5):
        self.max_steps = max_steps

    async def execute_task(self, user_goal: str) -> str:
        """Runs the ReAct thought-action-observation cycle to solve complex tasks."""
        from backend.core.tool_registry import tool_registry

        guard = LoopGuard(max_steps=self.max_steps)
        history: List[str] = []

        tools_desc = tool_registry.get_tools_prompt_description()

        system_prompt = f"""
You are {ASSISTANT_NAME}, an autonomous ReAct reasoning agent for {USER_NAME}.
Solve the user's request step-by-step using available tools.

Available Tools:
{tools_desc}

Format your response at each step strictly as:
Thought: <what you need to do next>
Action: <tool_name>
Arguments: <json dictionary of arguments>

When you have the final answer, output:
Thought: I have the final answer.
Final Answer: <your final response to {USER_NAME} in warm feminine Hinglish>
"""
        current_state = f"Goal: {user_goal}"

        for step in range(self.max_steps):
            full_prompt = f"{system_prompt}\n\nContext:\n{current_state}\n\nStep {step + 1}:"
            response = await llm.ask(full_prompt)

            # Check for Final Answer
            if "Final Answer:" in response:
                ans = response.split("Final Answer:", 1)[1].strip()
                return ans

            # Parse Thought, Action, Arguments
            thought = ""
            action = ""
            arguments = {}

            for line in response.splitlines():
                if line.startswith("Thought:"):
                    thought = line.replace("Thought:", "").strip()
                elif line.startswith("Action:"):
                    action = line.replace("Action:", "").strip()
                elif line.startswith("Arguments:"):
                    raw_args = line.replace("Arguments:", "").strip()
                    try:
                        arguments = json.loads(raw_args)
                    except Exception:
                        arguments = {"query": raw_args}

            if not action:
                # LLM didn't choose a tool, return raw answer
                return response.strip()

            action_sig = f"{action}:{json.dumps(arguments, sort_keys=True)}"
            if not guard.check_and_record(action_sig):
                logger.info("Breaking ReAct loop via LoopGuard and synthesizing final response.")
                break

            # Execute tool action
            logger.info(f"ReAct Step {step + 1}: Executing {action} with args {arguments}")
            obs = await tool_registry.execute_tool(action, arguments)

            current_state += f"\nStep {step + 1}:\nThought: {thought}\nAction: {action}\nObservation: {obs}"

        # Final synthesis
        synthesis_prompt = f"""
Based on this multi-step task execution:
{current_state}

Provide a direct, friendly final response to {USER_NAME} explaining what was accomplished.
Feminine persona ("kar diya hai", "dekh liya"). Numbers strictly in English.
"""
        return await llm.ask(synthesis_prompt)


# Global instance
react_agent = ReActAgent()
