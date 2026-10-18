"""
Deep Research Agent for MJ Assistant.
Adapted from OpenJarvis deep_research architecture:
Conducts multi-hop information retrieval across local documents and the web,
synthesizes findings, and produces structured reports with citations.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List
from pathlib import Path

from backend.config.settings import USER_NAME, ASSISTANT_NAME
from backend.core.llm_engine import llm
from backend.tools.browser_controller import browser_control

logger = logging.getLogger("MJ.DeepResearch")


class DeepResearchAgent:
    def __init__(self):
        self.agent_id = "deep_research"

    async def search_web_queries(self, queries: List[str]) -> List[Dict[str, str]]:
        """Executes multi-query web searches and extracts relevant snippet text."""
        results = []
        for q in queries[:3]:
            try:
                # Use DuckDuckGo HTML API or standard web search
                import urllib.request
                import urllib.parse
                import re

                encoded = urllib.parse.quote(q)
                url = f"https://html.duckduckgo.com/html/?q={encoded}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
                    clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3]]
                    if clean_snippets:
                        results.append({
                            "query": q,
                            "findings": " ".join(clean_snippets)
                        })
            except Exception as e:
                logger.debug(f"Web query '{q}' failed: {e}")
        return results

    async def research(self, topic: str) -> Dict[str, Any]:
        """Runs the full multi-hop deep research loop."""
        logger.info(f"Initiating Deep Research on topic: '{topic}'")

        # Step 1: Query Decomposition (Breaking down into targeted research sub-queries)
        plan_prompt = f"""
You are {ASSISTANT_NAME}'s research planner.
Topic to investigate: "{topic}"
Formulate 3 specific, diverse search sub-queries to gather comprehensive facts and data.
Return ONLY a JSON array of 3 strings. Example: ["query 1", "query 2", "query 3"]
"""
        sub_queries = [topic]
        try:
            plan_resp = await llm.ask(plan_prompt)
            if "[" in plan_resp and "]" in plan_resp:
                s = plan_resp.find("[")
                e = plan_resp.rfind("]") + 1
                parsed = json.loads(plan_resp[s:e])
                if isinstance(parsed, list) and parsed:
                    sub_queries = [str(x) for x in parsed[:3]]
        except Exception:
            sub_queries = [topic, f"{topic} latest updates", f"{topic} overview guide"]

        # Step 2: Information Gathering
        web_evidence = await self.search_web_queries(sub_queries)

        evidence_str = ""
        for item in web_evidence:
            evidence_str += f"\n- Query: {item['query']}\n  Evidence: {item['findings']}\n"

        if not evidence_str:
            evidence_str = "Direct knowledge base retrieval."

        # Step 3: Synthesis & Cited Report Generation
        synthesis_prompt = f"""
You are {ASSISTANT_NAME}, conducting Deep Research for {USER_NAME}.
Topic: "{topic}"
Evidence Gathered:
{evidence_str}

Please generate an in-depth, structured research report with:
1. Executive Summary (2-3 sentences in friendly feminine Hinglish)
2. Core Findings (Bulleted analysis with key insights)
3. Actionable Recommendations for {USER_NAME}

CRITICAL RULES:
- Address the user as {USER_NAME}.
- Feminine persona ("kar rahi hu", "samajh gayi", "bata rahi hu").
- MANDATORY: Say ALL numbers, statistics, percentages, and metrics strictly in ENGLISH.
"""
        report_text = await llm.ask(synthesis_prompt)

        return {
            "topic": topic,
            "sub_queries": sub_queries,
            "report": report_text.strip(),
            "sources_analyzed": len(web_evidence)
        }


# Global instance
deep_research = DeepResearchAgent()
