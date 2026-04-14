# Nomos Relay

**Nomos Relay** is a cybernetic orchestration framework for local AI agents. It provides a deterministic bridge between stochastic reasoning models and secure system execution.

Inspired by the concept of *Nomos* (the ordering of space and law) and the *Caveman* philosophy of linguistic compression, this tool ensures that local agents (like Gemma 4) operate within strict safety boundaries while maintaining perfect structural integrity in their output.

## Philosophy

In a world of verbose and unpredictable LLMs, **Nomos Relay** imposes cardinality. It treats agent communication as a control problem, filtering out the "prose" and "noise" of reasoning to leave only the discrete, actionable signal.

- **Planner-Relay Architecture:** Separates the "Brain" (Reasoning) from the "Transducer" (Formatting).
- **Fail-Closed Governance:** If a command or a data structure doesn't meet the contract, the system blocks execution immediately.
- **Cybernetic Regulation:** Profiles define the "Nomos" (the law of the workspace), restricting where and what the agent can execute.

## Core Components

- **`nomos.py`**: The runtime engine. Manages the task lifecycle, enforces profile policies, and validates command safety.
- **`proxy.js`**: An OpenAI-compatible middleware that allows tools like **OpenCode** or **Cursor** to speak to local Nomos models.
- **`Modelfiles`**: The "Constitutions" of the agent. They bake strict behavioral constraints directly into the Ollama inference engine.

## Getting Started

### 1. Build the Models
Ensure you have [Ollama](https://ollama.com/) installed and the `gemma4:latest` model pulled.
```bash
./build.sh
```

### 2. Run a Task
Execute a task within a specific security profile:
```bash
python3 nomos.py --workspace ~/my-project --profile repo-safe "Initialize a git repository" --execute
```

### 3. OpenCode Integration
Use the provided wrapper to launch OpenCode with the Nomos Relay proxy:
```bash
./oc-nomos.sh
```

## Security Profiles
- **`read-only`**: Default. No system mutations allowed.
- **`repo-safe`**: Allows common developer actions (`git`, `touch`, `mkdir`).
- **`cave`**: A sandbox profile restricted to `~/cave`.

## State & Audit
Every workspace managed by Nomos contains a `.nomos/` directory with a full audit trail:
- `journal.log`: A chronological record of all intents and actions.
- `last_plan.txt`: The reasoning trace.
- `last_relay.json`: The structured command output.

---
*Created by Abel Garza Ramírez. A Cybernetic approach to AI Agency.*
