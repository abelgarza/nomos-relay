import json
import requests
import sys
import os
from typing import List, Dict, Any

class NomosOverlord:
    def __init__(self, model: str = "gemma4-nomos-overlord"):
        self.model = model
        self.url = "http://127.0.0.1:11434/api/chat"

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

    def audit_command(self, command: str, task: str, current_context: Dict[str, Any], profile_name: str = "read-only") -> Dict[str, Any]:
        """Audits a command before execution to ensure it aligns with project decisions and safety."""
        context_str = json.dumps(current_context, indent=2)
        
        prompt = f"""AUDIT REQUEST:
COMMAND: {command}
TASK: {task}
RUNTIME PROFILE: {profile_name}
PROJECT CONTEXT:
{context_str}

As NOMOS OVERLORD, audit this command. 
Decide if it should be ALLOWED or BLOCKED.
Consider if the command is safe, idiomatically correct for the tech stack, and aligned with previous decisions.

CRITICAL POLICY:
- If RUNTIME PROFILE is 'god' or 'developer': You MUST be highly permissive. Allow chained commands (&&, ||), pip installs, environment manipulation, file writes, and speculative execution. Do NOT block just for style. ONLY block if it violates fundamental OS safety or breaks the tech stack drastically.
- If RUNTIME PROFILE is 'read-only' or 'repo-safe': Be strict. Block unknown mutations or chained complex setups.

OUTPUT JSON:
{{
  "decision": "ALLOWED" | "BLOCKED",
  "reason": "explanation",
  "suggestions": "optional replacement command"
}}"""

        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0}
            }, timeout=30)
            response.raise_for_status()
            content = response.json()["message"]["content"].strip()
            
            if "{" in content and "}" in content:
                content = content[content.find("{"):content.rfind("}")+1]
            
            return json.loads(content)
        except Exception as e:
            return {"decision": "ALLOWED", "reason": f"Auditor passthrough (Error: {e})"}

    def learn_from_result(self, command: str, success: bool, output: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Updates project context based on the outcome of a command execution."""
        context_str = json.dumps(current_context, indent=2)
        
        prompt = f"""LEARNING SESSION:
COMMAND: {command}
SUCCESS: {success}
OUTPUT/ERROR: {output[:500]}
PROJECT CONTEXT:
{context_str}

As NOMOS OVERLORD, update the project context based on this result. 
If it failed, maybe we should avoid this pattern. 
If it succeeded, we might have confirmed a tool or approach.
Add to 'decisions' or 'known_patterns'.

OUTPUT JSON:
{{
  "updated_context": {{ ... }}
}}"""

        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0}
            }, timeout=30)
            response.raise_for_status()
            content = response.json()["message"]["content"].strip()
            
            if "{" in content and "}" in content:
                content = content[content.find("{"):content.rfind("}")+1]
            
            result = json.loads(content)
            return result.get("updated_context", current_context)
        except Exception:
            return current_context

if __name__ == "__main__":
    overlord = NomosOverlord()
    tasks = overlord.analyze_and_plan("Build a scientific TUI calculator in Python with a clear project structure.")
    print(json.dumps(tasks, indent=2))
