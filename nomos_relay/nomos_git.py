import subprocess
import os
import sys
import json
import requests
from typing import Optional, Tuple

class NomosGitController:
    def __init__(self, workspace: str, model: str = "gemma4-nomos-git"):
        self.workspace = workspace
        self.model = model
        self.url = "http://127.0.0.1:11434/api/chat"

    def is_git_repo(self) -> bool:
        return os.path.exists(os.path.join(self.workspace, ".git"))

    def _run_git(self, *args) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.workspace,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()

    def get_current_branch(self) -> str:
        success, out = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        return out if success else ""

    def ensure_safe_branch(self, target_branch: str = "nomos-auto") -> bool:
        """Ensures the agent operates on a dedicated branch."""
        if not self.is_git_repo():
            return False

        current = self.get_current_branch()
        if current == target_branch:
            return True

        # Check if branch exists locally
        success, out = self._run_git("branch", "--list", target_branch)
        if out and target_branch in out:
            # Switch to it
            success, msg = self._run_git("checkout", target_branch)
            if success:
                print(f"[Git] Switched to existing safe branch: {target_branch}", file=sys.stderr)
            else:
                print(f"[Git] Failed to switch to {target_branch}: {msg}", file=sys.stderr)
        else:
            # Create and switch
            success, msg = self._run_git("checkout", "-b", target_branch)
            if success:
                print(f"[Git] Created and switched to safe branch: {target_branch}", file=sys.stderr)
            else:
                print(f"[Git] Failed to create {target_branch}: {msg}", file=sys.stderr)
        
        return success

    def has_uncommitted_changes(self) -> bool:
        success, out = self._run_git("status", "--porcelain")
        return bool(out)

    def generate_commit_message(self, task_desc: str, diff_text: str) -> str:
        prompt = f"""Generate a concise Conventional Commit message for the following changes.
TASK CONTEXT: {task_desc}

GIT DIFF:
{diff_text}

Output ONLY the commit message string. Do not use quotes or explanations. Format: type(scope): description"""
        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0}
            }, timeout=30)
            response.raise_for_status()
            return response.json()["message"]["content"].strip()
        except Exception:
            return f"feat(nomos): completed task - {task_desc[:50]}"

    def commit_task(self, task_desc: str) -> bool:
        """Stages all changes and creates a commit using the AI model."""
        if not self.is_git_repo() or not self.has_uncommitted_changes():
            return False

        # Stage everything
        self._run_git("add", ".")
        
        # Get diff of staged changes
        success, diff_text = self._run_git("diff", "--staged", "--stat") # Use stat to save context window if huge, or full diff
        if not success or not diff_text:
            return False

        # Generate message
        print(f"[Git] Generating commit message for task...", file=sys.stderr)
        # We might want full diff for small changes, stat for big. Let's try a bounded full diff.
        _, full_diff = self._run_git("diff", "--staged")
        if len(full_diff) > 4000:
            full_diff = full_diff[:4000] + "\n...[truncated]"
            
        commit_msg = self.generate_commit_message(task_desc, full_diff)
        
        # Commit
        success, msg = self._run_git("commit", "-m", commit_msg)
        if success:
            print(f"[Git] Committed: {commit_msg}", file=sys.stderr)
        else:
            print(f"[Git] Commit failed: {msg}", file=sys.stderr)
            
        return success

if __name__ == "__main__":
    git = NomosGitController(".")
    print(f"Is repo: {git.is_git_repo()}")
    print(f"Branch: {git.get_current_branch()}")
