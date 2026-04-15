# Nomos Relay

<p align="center">
  <img src="https://img.shields.io/github/actions/workflow/status/abelgarza/nomos-relay/ci.yml?branch=main&style=for-the-badge&logo=github" alt="CI Status">
  <img src="https://img.shields.io/github/license/abelgarza/nomos-relay?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Ollama-Compatible-black?style=for-the-badge&logo=ollama" alt="Ollama">
</p>

---

**Nomos Relay** is a cybernetic orchestration framework for local AI agents. It provides a deterministic bridge between stochastic reasoning models and secure system execution. 

Inspired by the concept of *Nomos* (the ordering of space and law) and the *Caveman* philosophy of linguistic compression, this framework ensures that local agents (like Gemma 4) operate within strict safety boundaries while maintaining perfect structural integrity in their output.

## Multi-Agent Architecture

Nomos Relay operates through a collaborative loop where each agent has a specific, "constitutional" role defined in its Modelfile:

| Agent | Role | Responsibility |
| :--- | :--- | :--- |
| **Overlord** | Strategic | Decomposes high-level objectives into technical Kanban tasks. Maintains tech stack consistency. |
| **Planner** | Tactical | Analyzes codebase context (RAG) and the current task to generate a compressed plan. |
| **Relay** | Transducer | Converts plans into strict JSON/Bash commands. Enforces Fail-Closed safety. |
| **Git** | Versioning | Specialized in analyzing diffs and generating Conventional Commits. |
| **Cloud** | Observer | High-parameter model variant for remote/TPU-powered orchestration. |

---

## Installation

### 1. Install Python Package
```bash
# Clone the repo and install in editable mode
pip install -e .
```

### 2. Build the Model Constitutions
Ensure you have [Ollama](https://ollama.com/) installed and running.
```bash
nomos build
```

---

## The Nomos CLI

The `nomos` command is the primary entry point for both interactive and autonomous development.

### 1. Task Execution (One-Shot)
Run a single task in a specific security profile:
```bash
nomos "List all python files in src/" --profile read-only
nomos "Create a basic API with FastAPI" --profile developer --execute
```

### 2. Autonomous Architect Mode (`--auto`)
The most powerful mode. Nomos becomes an autonomous engineer that iterates until the goal is met.
```bash
nomos "Build a full TUI dashboard based on README.md" --auto --profile developer
```
**In this mode, Nomos will:**
1.  **Recon:** Scan the environment to detect the language (Go, Python, etc).
2.  **Plan:** Overlord creates a Kanban board in `.nomos/kanban.json`.
3.  **Branch:** If a Git repo is detected, it moves to a safe `nomos-auto` branch.
4.  **Execute:** Iterates through tasks, updating its memory (RAG) after each step.
5.  **Commit:** Automatically commits successful tasks using the Git Agent.

**Continuous Iteration (Sprints):**
If you run `--auto` with a new instruction after a mission is complete, Nomos will not start from scratch. Instead, it will use the existing project context and RAG memory to start a **New Sprint**, appending new tasks to the Kanban board. This allows for continuous development while maintaining architectural consistency.

### 3. General Utility
```bash
nomos ask "How do profiles work in this framework?"  # Quick Q&A with the Planner
nomos list                                           # List available Nomos models
nomos index --reset                                  # Wipe and rebuild RAG memory
```

---

## Cognitive Memory (RAG)

Nomos uses **LanceDB** to maintain a deep semantic understanding of your codebase.

- **Incremental Sync:** In `--auto` mode, Nomos automatically re-indexes changed files after each task, ensuring the next step is always context-aware.
- **Manual Indexing:** Run `nomos index` to update the memory after manual changes.
- **Hard Reset:** Use `nomos index --reset` to clear the vector store and start fresh.

Memory state lives in the `.nomos/` directory of your workspace.

---

## Integration Examples (Extending the Framework)

Nomos Relay is designed to be a "Cybernetic Core" that can be used by other tools:

### OpenAI-Compatible Proxy
Running `node proxy.js` starts a middleware that allows any OpenAI-compatible tool to use Nomos agents and RAG.

### Implementation Case Studies:
- **`oc-nomos.sh` (OpenCode):** Launches OpenCode using Nomos Relay as the backend, giving the editor full codebase awareness and execution safety.
- **`pi-nomos.sh` (Pi):** Integrates the Pi agent with Nomos to provide a terminal-based cybernetic assistant.

---

## Security Profiles

Nomos enforces strict "Fail-Closed" governance through profiles:

- **`read-only`**: (Default) Discovery only. No filesystem mutations allowed.
- **`repo-safe`**: Allows `git`, `mkdir`, and `touch`. Safe for repo management.
- **`developer`**: Full engineering access. Can use `pip`, `npm`, `python`, `go`, etc. Supports safe shell operators like `>` and `&&`.

Every command is validated against a global `DENYLIST` to prevent system-level damage.

---
*Created by **Abel Garza Ramírez**. A Cybernetic approach to AI Agency.*
