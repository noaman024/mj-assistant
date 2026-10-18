"""
MJ Assistant Specialized Agents.
Inspired by OpenJarvis architecture:
- morning_digest: Daily briefing & status synthesis
- deep_research: Multi-hop knowledge search & citation reports
- react_agent: Autonomous ReAct loop execution with LoopGuard
"""

from backend.agents.morning_digest import morning_digest
from backend.agents.deep_research import deep_research
from backend.agents.react_agent import react_agent

__all__ = ["morning_digest", "deep_research", "react_agent"]
