#!/usr/bin/env python3
import json
import requests
import json
import sys
import argparse
import os
import subprocess
import shlex
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/chat"
STATE_DIR_NAME = ".nomos"
# BASE_DIR should be the project root, not the package subdir
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(BASE_DIR, "nomos_relay", "api", "relay.schema.json")

# Default security settings
DEFAULT_DANGEROUS_OPS = [">", ">>", "|", "&", ";", "`", "$("]
DEFAULT_DENYLIST = [
    "rm", "mv", "chmod", "chown", "sudo", "curl", "wget", 
    "ssh", "scp", "dd", "mkfs", "reboot", "shutdown"
]

class Profile:
    def __init__(self, name, allow_mutation=False, mutating_allowlist=None, read_only_allowlist=None, workspace_root=None):
        self.name = name
        self.allow_mutation = allow_mutation
        self.mutating_allowlist = mutating_allowlist or []
        self.read_only_allowlist = read_only_allowlist or ["pwd", "ls", "find", "cat", "grep", "git"]
        self.workspace_root = workspace_root

PROFILES = {
    "read-only": Profile(
        "read-only",
        allow_mutation=False,
        read_only_allowlist=["pwd", "ls", "find", "cat", "grep", "git"]
    ),
    "repo-safe": Profile(
        "repo-safe",
        allow_mutation=True,
        mutating_allowlist=["mkdir", "touch", "git"],
        read_only_allowlist=["pwd", "ls", "find", "cat", "grep", "git"]
    ),
    "developer": Profile(
        "developer",
        allow_mutation=True,
        mutating_allowlist=["mkdir", "touch", "git", "python3", "python", "node", "npm", "pip"],
        read_only_allowlist=["pwd", "ls", "find", "cat", "grep", "git", "ls -R"]
    )
}

def query_ollama(model, messages, format_schema=None, stream=False, temperature=0):
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
        
    if format_schema:
        payload["format"] = format_schema

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error querying Ollama: {e}", file=sys.stderr)
        sys.exit(1)

def is_within_path(target, base):
    if not base:
        return True
    target = os.path.abspath(os.path.expanduser(os.path.expandvars(target)))
    base = os.path.abspath(os.path.expanduser(base))
    return target == base or target.startswith(base + os.sep)

class Runtime:
    def __init__(self, workspace, profile_name="read-only", execute=False):
        self.workspace = os.path.abspath(os.path.expanduser(workspace))
        if profile_name not in PROFILES:
            print(f"Error: Unknown profile '{profile_name}'", file=sys.stderr)
            sys.exit(1)
        self.profile = PROFILES[profile_name]
        self.execute = execute
        
        # Ensure workspace exists
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace, exist_ok=True)

    def run_autonomous_loop(self, objective, max_iterations=10):
        """Orchestrates the autonomous engineering loop using Overlord and Kanban."""
        from nomos_relay.nomos_kanban import NomosKanban
        from nomos_relay.nomos_overlord import NomosOverlord
        from nomos_relay.nomos_rag import RAGManager, OllamaEmbeddingProvider, LanceDBProvider
        import signal
        
        # Flag to track if user requested shutdown
        shutdown_requested = False
        
        def signal_handler(sig, frame):
            nonlocal shutdown_requested
            if not shutdown_requested:
                print(f"\n[!] Shutdown requested by user (Ctrl+C). Finishing current task before exiting...", file=sys.stderr)
                shutdown_requested = True
            else:
                print(f"\n[!] Forcing immediate exit.", file=sys.stderr)
                sys.exit(1)
                
        # Register the signal handler for SIGINT
        original_sigint_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, signal_handler)
        
        db_path = os.path.join(self.workspace, STATE_DIR_NAME, "vector_store")
        os.makedirs(db_path, exist_ok=True)
        
        kanban = NomosKanban(db_path)
        overlord = NomosOverlord()
        
        # Incremental RAG Setup
        embedder = OllamaEmbeddingProvider()
        store = LanceDBProvider(db_path)
        rag = RAGManager(self.workspace, embedder, store)

        try:
            # 0. Reconnaissance: Capture basic workspace structure
            env_context = ""
            try:
                ls_output = subprocess.check_output(
                    "find . -maxdepth 2 -not -path '*/.*' | sort", 
                    shell=True, cwd=self.workspace, text=True
                )
                env_context = f"\nWORKSPACE ENVIRONMENT (Files/Dirs):\n{ls_output.strip()}\n"
            except:
                pass

            # 1. Initialize or Resume Board
            board = kanban.get_full_board()
            project_context = kanban.load_context()

            if not board or project_context == {}:
                print(f"--- Overlord Initializing Project ---", file=sys.stderr)
                result = overlord.analyze_and_plan(objective + env_context, current_context=project_context)
                kanban.init_board(objective, result["tasks"])
                kanban.save_context(result["context"])
                project_context = result["context"]
                print(f"Project context saved: {project_context.get('tech_stack', 'Unknown')}")
                print(f"Backlog created: {len(result['tasks'])} tasks.")
            else:
                print(f"--- Overlord Resuming Project: {project_context.get('tech_stack', 'Unknown')} ---", file=sys.stderr)

            # 2. Loop until complete or limit reached
            iteration = 0
            while iteration < max_iterations:
                if shutdown_requested:
                    print(f"\n--- AUTOPILOT PAUSED (State saved in Kanban) ---", file=sys.stderr)
                    break
                    
                iteration += 1
                # Sync RAG before every task
                rag.index_workspace()
                
                # Fetch task
                task = kanban.get_next_task()
                
                if not task:
                    if kanban.is_complete():
                        print(f"\n--- MISSION COMPLETE ---", file=sys.stderr)
                    else:
                        print(f"\n--- PROJECT BLOCKED ---", file=sys.stderr)
                    break
                
                print(f"\n[Iteration {iteration}] Executing Task: {task['description']}", file=sys.stderr)
                
                # Build context-aware prompt
                full_task_context = f"OBJECTIVE: {objective}\nPROJECT CONTEXT: {json.dumps(project_context)}\nCURRENT TASK: {task['description']}\nGOAL: Complete the task staying true to the project stack and decisions."
                
                # Execute one step
                self.execute = True 
                success, result_msg = self.run_task(full_task_context)
                
                if success:
                    kanban.update_task_state(task['id'], "done", "Success")
                else:
                    attempts = task.get('attempts', 0) + 1
                    if attempts >= 3:
                        print(f"[!] Task failed 3 times. Blocking.", file=sys.stderr)
                        kanban.update_task_state(task['id'], "blocked", result_msg, increment_attempts=True)
                    else:
                        print(f"[!] Task failed (Attempt {attempts}). Re-evaluating strategy...", file=sys.stderr)
                        kanban.update_task_state(task['id'], "doing", result_msg, increment_attempts=True)

        finally:
            # Restore original handler when exiting loop
            signal.signal(signal.SIGINT, original_sigint_handler)

    def log(self, log_type, content):
        nomos_dir = os.path.join(self.workspace, STATE_DIR_NAME)
        if not os.path.exists(nomos_dir):
            try:
                os.makedirs(nomos_dir, exist_ok=True)
                # Add to .gitignore if in git repo
                if os.path.exists(os.path.join(self.workspace, ".git")):
                    gitignore_path = os.path.join(self.workspace, ".gitignore")
                    ignore_entry = f"{STATE_DIR_NAME}/"
                    needs_entry = True
                    if os.path.exists(gitignore_path):
                        with open(gitignore_path, "r") as f:
                            if ignore_entry in f.read():
                                needs_entry = False
                    if needs_entry:
                        with open(gitignore_path, "a") as f:
                            f.write(f"\n{ignore_entry}\n")
            except:
                return
        
        try:
            if log_type == "journal":
                with open(os.path.join(nomos_dir, "journal.log"), "a") as f:
                    f.write(f"[{datetime.now().isoformat()}] {content}\n")
            elif log_type == "plan":
                with open(os.path.join(nomos_dir, "last_plan.txt"), "w") as f:
                    f.write(content + "\n")
            elif log_type == "relay":
                with open(os.path.join(nomos_dir, "last_relay.json"), "w") as f:
                    f.write(content + "\n")
        except Exception as e:
            print(f"Logging error: {e}", file=sys.stderr)

    def command_is_allowed(self, cmd):
        if not cmd:
            return True, "", False

        # 1. Shell Operator Check
        if any(op in cmd for op in DEFAULT_DANGEROUS_OPS):
            return False, "Contains dangerous shell operators", False

        # 2. Parse Check
        try:
            cmd_parts = shlex.split(cmd)
        except ValueError:
            return False, "Shell parse error", False

        if not cmd_parts:
            return True, "", False

        primary_cmd = cmd_parts[0]

        # 3. Denylist Check
        if primary_cmd in DEFAULT_DENYLIST:
            return False, f"Command '{primary_cmd}' is in denylist", False

        # 4. Workspace Root Check (Profile-based Jail)
        if self.profile.workspace_root:
            if not is_within_path(self.workspace, self.profile.workspace_root):
                return False, f"Workspace {self.workspace} is not within profile root {self.profile.workspace_root}", False

        # 5. Mutation Policy
        is_mutation = False
        
        # If it's in mutating allowlist but NOT in read-only, it's definitely a mutation
        if primary_cmd in self.profile.mutating_allowlist and primary_cmd not in self.profile.read_only_allowlist:
            is_mutation = True

        # git is special
        if primary_cmd == "git":
            mutating_git = ["init", "add", "commit", "branch", "checkout", "tag", "rm", "mv"]
            if any(arg in cmd_parts for arg in mutating_git):
                is_mutation = True

        if is_mutation:
            if not self.profile.allow_mutation:
                return False, f"Mutations are not allowed in profile '{self.profile.name}'", True
            
            if primary_cmd not in self.profile.mutating_allowlist:
                return False, f"Command '{primary_cmd}' is not in mutation allowlist for profile '{self.profile.name}'", True
        else:
            if primary_cmd not in self.profile.read_only_allowlist:
                return False, f"Command '{primary_cmd}' is not in read-only allowlist for profile '{self.profile.name}'", False

        # 6. Deep Flag Check
        if primary_cmd == "find":
            forbidden_find = ["-delete", "-exec", "-ok"]
            if any(arg in cmd_parts for arg in forbidden_find):
                return False, "Forbidden 'find' flags detected", is_mutation

        return True, "", is_mutation

    def run_task(self, task):
        # 0. RAG Context
        rag_context = ""
        try:
            from nomos_relay.nomos_rag import RAGManager, OllamaEmbeddingProvider, LanceDBProvider
            db_path = os.path.join(self.workspace, STATE_DIR_NAME, "vector_store")
            if os.path.exists(db_path):
                embedder = OllamaEmbeddingProvider()
                store = LanceDBProvider(db_path)
                manager = RAGManager(self.workspace, embedder, store)
                rag_context = manager.query(task)
                if rag_context:
                    print(f"--- RAG Context Injected ---", file=sys.stderr)
        except Exception:
            # Silent fallback if RAG is not initialized or dependencies missing
            pass

        # 1. Plan
        print(f"--- Planning [gemma4-nomos] ---", file=sys.stderr)
        
        plan_prompt = f"Task: {task}"
        if rag_context:
            plan_prompt = f"Context from workspace:\n{rag_context}\n\nTask: {task}"
            
        plan_messages = [{"role": "user", "content": plan_prompt}]
        plan_res = query_ollama("gemma4-nomos", plan_messages, temperature=0)
        plan_content = plan_res["message"]["content"]
        print(plan_content)
        self.log("plan", plan_content)

        # 2. Relay
        print(f"\n--- Structuring [gemma4-nomos-relay] ---", file=sys.stderr)
        if not os.path.exists(SCHEMA_PATH):
            print(f"Error: Schema not found at {SCHEMA_PATH}", file=sys.stderr)
            return

        with open(SCHEMA_PATH, 'r') as f:
            schema = json.load(f)
        
        relay_prompt = f"Task: {task}. Plan: {plan_content}. Constraints: ultra-compressed, match schema. IMPORTANT: The 'command' field must contain the EXACT shell command to achieve the goal. DO NOT use shell operators like &&, |, or >. provide a single direct command."
        relay_messages = [{"role": "user", "content": relay_prompt}]
        relay_res = query_ollama("gemma4-nomos-relay", relay_messages, format_schema=schema, temperature=0)
        relay_content = relay_res["message"]["content"]
        self.log("relay", relay_content)
        
        try:
            structured = json.loads(relay_content)
            
            # Strict Typed Validation
            validation_errors = []
            
            # 1. Basic type checks for all expected fields
            expected_types = {
                "goal": str,
                "constraints": list,
                "result": str,
                "uncertainty": str,
                "next": str,
                "command": str
            }
            
            required_keys = ["goal", "constraints", "result", "uncertainty", "next"]
            
            for key in required_keys:
                if key not in structured:
                    validation_errors.append(f"Missing required key: '{key}'")
            
            for key, expected_type in expected_types.items():
                if key in structured:
                    val = structured[key]
                    if not isinstance(val, expected_type):
                        validation_errors.append(f"Incorrect type for '{key}': expected {expected_type.__name__}, got {type(val).__name__}")
                    elif key == "constraints":
                        # Deep check for list of strings
                        if not all(isinstance(item, str) for item in val):
                            validation_errors.append("All items in 'constraints' must be strings")

            if validation_errors:
                msg = f"BLOCKED: Malformed relay protocol. Errors: {'; '.join(validation_errors)}"
                print(f"\n--- {msg} ---", file=sys.stderr)
                self.log("journal", f"Task: {task} | Result: {msg}")
                return

            print(json.dumps(structured, indent=2))
            
            cmd = structured.get("command", "")

            if self.execute and not cmd:
                msg = "BLOCKED: Execution requested but no command generated by relay"
                print(f"\n--- {msg} ---", file=sys.stderr)
                self.log("journal", f"Task: {task} | Result: {msg}")
                return

            if cmd:
                allowed, reason, is_mutation = self.command_is_allowed(cmd)

                if not allowed:
                    msg = f"BLOCKED: {reason}"
                    print(f"\n--- {msg} ---", file=sys.stderr)
                    self.log("journal", f"Task: {task} | Command: {cmd} | Result: {msg}")
                    return False, msg

                if is_mutation and not self.execute:
                    msg = "DRY RUN: Mutation blocked. Use --execute to run."
                    print(f"\n--- {msg} ---", file=sys.stderr)
                    self.log("journal", f"Task: {task} | Command: {cmd} | Result: {msg}")
                    return False, msg

                print(f"\n--- Executing: {cmd} ---", file=sys.stderr)
                try:
                    cmd_parts = shlex.split(cmd)
                    expanded_parts = [os.path.expanduser(os.path.expandvars(p)) for p in cmd_parts]
                    
                    # Execute in workspace
                    result = subprocess.run(
                        expanded_parts, 
                        shell=False, 
                        capture_output=True, 
                        text=True, 
                        cwd=self.workspace
                    )
                    
                    if result.returncode == 0:
                        if result.stdout:
                            print(result.stdout)
                        self.log("journal", f"Task: {task} | Command: {cmd} | Status: Success")
                        return True, result.stdout
                    else:
                        print(result.stderr, file=sys.stderr)
                        self.log("journal", f"Task: {task} | Command: {cmd} | Status: Failed (code {result.returncode}) | Error: {result.stderr}")
                        return False, result.stderr
                except Exception as e:
                    print(f"Execution error: {e}", file=sys.stderr)
                    self.log("journal", f"Task: {task} | Command: {cmd} | Status: Error ({e})")
                    return False, str(e)
            else:
                msg = "No command generated"
                self.log("journal", f"Task: {task} | {msg}")
                return False, msg

        except json.JSONDecodeError:
            msg = f"Failed to parse relay JSON: {relay_content}"
            print(msg, file=sys.stderr)
            return False, msg

def main():
    parser = argparse.ArgumentParser(description="Nomos: Profile-based Workspace Agent Runtime")
    
    # Check if we should use the new task-centric CLI or compatibility mode
    if len(sys.argv) > 1 and sys.argv[1] not in ["ask", "list", "build", "index", "-h", "--help"]:
        # New task-centric CLI (but also used for legacy if no flags)
        parser.add_argument("task", help="Task to execute")
        parser.add_argument("--workspace", default=os.getcwd(), help="Workspace directory")
        parser.add_argument("--profile", default="read-only", help="Profile name (read-only, repo-safe)")
        parser.add_argument("--execute", action="store_true", help="Execute mutating actions")
        parser.add_argument("--auto", action="store_true", help="Run in autonomous architect mode (Kanban/Overlord)")
        args = parser.parse_args()
        
        runtime = Runtime(args.workspace, profile_name=args.profile, execute=args.execute)
        
        if args.auto:
            runtime.run_autonomous_loop(args.task)
        else:
            runtime.run_task(args.task)
    else:
        subparsers = parser.add_subparsers(dest="command")

        # Compatibility commands
        ask_parser = subparsers.add_parser("ask")
        ask_parser.add_argument("prompt")
        
        subparsers.add_parser("list")
        subparsers.add_parser("build")
        
        index_parser = subparsers.add_parser("index")
        index_parser.add_argument("--workspace", default=os.getcwd(), help="Workspace directory")
        index_parser.add_argument("--reset", action="store_true", help="Clear existing index and start fresh")

        args = parser.parse_args()

        if args.command == "ask":
            messages = [{"role": "user", "content": args.prompt}]
            res = query_ollama("gemma4-nomos", messages, temperature=None)
            print(res["message"]["content"])
        elif args.command == "list":
            try:
                res = requests.get("http://localhost:11434/api/tags").json()
                for model in res["models"]:
                    if "nomos" in model["name"]:
                        print(f"- {model['name']}")
            except:
                print("Error connecting to Ollama", file=sys.stderr)
        elif args.command == "build":
            print("--- Building Models ---", file=sys.stderr)
            subprocess.run([os.path.join(BASE_DIR, "build.sh")], shell=False, check=True)
        elif args.command == "index":
            try:
                from nomos_relay.nomos_rag import RAGManager, OllamaEmbeddingProvider, LanceDBProvider
                workspace = os.path.abspath(os.path.expanduser(args.workspace))
                db_path = os.path.join(workspace, STATE_DIR_NAME, "vector_store")
                
                if args.reset and os.path.exists(db_path):
                    print(f"--- Resetting Index: {db_path} ---", file=sys.stderr)
                    import shutil
                    shutil.rmtree(db_path, ignore_errors=True)
                
                os.makedirs(db_path, exist_ok=True)
                
                print(f"--- Indexing Workspace: {workspace} ---", file=sys.stderr)
                embedder = OllamaEmbeddingProvider()
                store = LanceDBProvider(db_path)
                manager = RAGManager(workspace, embedder, store)
                manager.index_workspace()
                print("Index complete.")
            except ImportError:
                print("Error: lancedb or dependencies not installed. RAG indexing failed.", file=sys.stderr)
        else:
            parser.print_help()

if __name__ == "__main__":
    main()
