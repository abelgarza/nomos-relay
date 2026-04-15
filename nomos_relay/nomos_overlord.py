import json
import requests
import sys
import os
from typing import List, Dict, Any

class NomosOverlord:
    def __init__(self, model: str = "gemma4-nomos"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def analyze_and_plan(self, objective: str, journal_tail: str = "") -> List[str]:
        """Analyzes the objective and audit logs to generate a list of atomic technical tasks."""
        
        prompt = f"""You are the NOMOS OVERLORD. Your goal is to break down a high-level objective into a strict, sequential list of atomic, verifiable technical tasks for an agent.

OBJECTIVE:
{objective}

RECENT JOURNAL LOGS:
{journal_tail}

CONSTRAINTS:
- Tasks must be atomic (one action per task).
- Tasks must be technical (e.g., "Create directory X", "Write math logic in Y", "Run tests in Z").
- Output ONLY a JSON array of strings. No prose, no headings.

Output format:
["Task 1", "Task 2", "Task 3"]
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
            
            # Extract JSON if the model included extra text
            if "[" in content and "]" in content:
                content = content[content.find("["):content.rfind("]")+1]
            
            tasks = json.loads(content)
            if isinstance(tasks, list):
                return tasks
            return []
        except Exception as e:
            print(f"Overlord Error: {e}", file=sys.stderr)
            return []

if __name__ == "__main__":
    overlord = NomosOverlord()
    tasks = overlord.analyze_and_plan("Build a scientific TUI calculator in Python with a clear project structure.")
    print(json.dumps(tasks, indent=2))
