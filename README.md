# Caveman: Workspace Orchestration Library

`caveman` is a general orchestration library and agent runtime that operates over arbitrary workspaces using policy-driven profiles. It uses Ollama-backed `*-caveman*` models internally to plan, structure, and execute actions safely.

## Core Concepts
- **Runtime**: The core engine that handles the `planner -> relay -> execute` flow.
- **Profiles**: Policy configurations that define allowed operations, commands, and workspace boundaries.
- **Workspace**: A local directory where the agent operates and maintains state in `.caveman/`.

## Profiles
- **`cave`**: The classic sandbox profile. Allows mutations but restricts operations to `~/cave`.
- **`read-only`**: Default safe profile. No mutations allowed anywhere.
- **`repo-safe`**: Allows common repository mutations (`git`, `touch`, `mkdir`) in any workspace.

## Usage
```bash
# General task execution
caveman --workspace <path> --profile <name> "<task>" --execute

# Examples:
# 1. Sandbox style
caveman --workspace ~/cave/project1 --profile cave "Initialize git repo" --execute

# 2. Existing repo inspection
caveman --workspace ~/.dotfiles --profile read-only "Show git status"

# 3. Repo safe mutation
caveman --workspace ~/my-project --profile repo-safe "Create README.md" --execute
```

## OpenCode Integration (Proxy)

To use `caveman`'s logic within the OpenCode UI/CLI while using the `gemma4` model, a local proxy is provided. This proxy intercepts OpenCode's tool calls and translates them into the strict JSON schema expected by the `gemma4-caveman-relay` model. The proxy is built with Node.js to properly handle the strict Server-Sent Events (SSE) formatting required by the Vercel AI SDK.

**Usage (On-Demand Wrapper):**
Instead of manually managing the proxy process, use the provided wrapper script. It automatically starts the proxy before launching OpenCode and gracefully shuts it down when you exit.

1. Configure OpenCode (`~/.config/opencode/opencode.json`) to register Caveman as a provider pointing to the local proxy:
   ```json
   "provider": {
     "caveman": {
       "name": "Caveman",
       "npm": "@ai-sdk/openai-compatible",
       "options": {
         "baseURL": "http://127.0.0.1:11435/v1",
         "apiKey": "caveman"
       },
       "models": {
         "gemma4:latest": {
           "name": "gemma4:latest"
         }
       }
     }
   }
   ```

2. Run the wrapper script:
   ```bash
   ./oc-caveman.sh
   # Or pass arguments directly to OpenCode:
   ./oc-caveman.sh run "list files"
   ```

**Recommended Alias:**
Add this to your `.bashrc` or `.zshrc` for quick access:
```bash
alias occ='/home/abelg/.dotfiles/ollama/oc-caveman.sh'
```
Now you can simply type `occ` to start your fully agentic environment. Proxy logs are kept in `/tmp/caveman_proxy.log`.

## CLI Reference
- `caveman "<task>"`: Run a task in CWD with `read-only` profile.
- `--workspace <path>`: Set the target workspace (default: CWD).
- `--profile <name>`: Set the policy profile (default: `read-only`).
- `--execute`: Enable execution of mutating actions.
- `--dry-run`: (Implicit) Mutating actions are blocked without `--execute`.

## Safety & Governance
- **Workspace Jail**: Profiles can enforce path-based boundaries (e.g., `cave` profile restricted to `~/cave`).
- **Host-Side Enforcement**: All commands are parsed (`shlex.split`) and validated against profile allowlists and global denylists before execution.
- **Fail-Closed Protocol**: The relay JSON must strictly match the schema (types and required fields). Mistyped output or missing fields result in an immediate block with no silent repair.
- **Strict Execution**: If `--execute` is requested but the relay produces no command or an empty command, execution is blocked.
- **Safe Execution**: Uses `shell=False` and explicit token expansion.

## Workspace State
Every workspace contains a `.caveman/` directory:
- `journal.log`: Append-only record of all activities and results.
- `last_plan.txt`: The full text of the last planning step.
- `last_relay.json`: The structured JSON relay for the last action.

## Smoke Test
Run `./smoke.sh` to verify profiles and workspace-local state.
