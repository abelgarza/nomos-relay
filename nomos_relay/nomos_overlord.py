import json
import requests
import sys
import os
from typing import List, Dict, Any

class NomosOverlord:
    def __init__(self, model: str = "gemma4-nomos-overlord"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def analyze_and_plan(self, objective: str, journal_tail: str = "", current_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyzes objective and context to generate tasks and update project decisions."""
        
        context_str = json.dumps(current_context or {}, indent=2)
        
        prompt = f"""OBJECTIVE:
{objective}

EXISTING PROJECT CONTEXT:
{context_str}

RECENT LOGS:
{journal_tail}

Break down the objective into tasks and update context."""

        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0}
            }, timeout=60)
            response.raise_for_status()
            content = response.json()["message"]["content"].strip()
            
            # Extract JSON
            if "{" in content and "}" in content:
                content = content[content.find("{"):content.rfind("}")+1]
            
            result = json.loads(content)
            return {
                "tasks": result.get("tasks", []),
                "context": result.get("updated_context", current_context or {})
            }
        except Exception as e:
            print(f"Overlord Error: {e}", file=sys.stderr)
            return {"tasks": [], "context": current_context or {}}

if __name__ == "__main__":
    overlord = NomosOverlord()
    tasks = overlord.analyze_and_plan("Build a scientific TUI calculator in Python with a clear project structure.")
    print(json.dumps(tasks, indent=2))
