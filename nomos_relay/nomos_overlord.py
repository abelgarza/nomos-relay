import json
import requests
import sys
import os
from typing import List, Dict, Any

class NomosOverlord:
    def __init__(self, model: str = "gemma4-nomos"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def analyze_and_plan(self, objective: str, journal_tail: str = "", current_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyzes objective and context to generate tasks and update project decisions."""
        
        context_str = json.dumps(current_context or {}, indent=2)
        
        prompt = f"""You are the NOMOS OVERLORD. Break down the objective into sequential, atomic, technical tasks.
You MUST maintain consistency with existing project decisions.

OBJECTIVE:
{objective}

EXISTING PROJECT CONTEXT:
{context_str}

RECENT LOGS:
{journal_tail}

CONSTRAINTS:
- Tasks must be atomic and technical.
- Identify the Tech Stack (Language, Frameworks) and save it in 'updated_context'.
- Output ONLY valid JSON.

Output format:
{{
  "updated_context": {{
    "tech_stack": "e.g. Go (Bubble Tea)",
    "architecture": "e.g. MVC",
    "decisions": ["decision 1", "decision 2"]
  }},
  "tasks": ["Task 1", "Task 2"]
}}
"""
        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0}
            }, timeout=60)
            response.raise_for_status()
            content = response.json()["message"]["content"].strip()
            
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
