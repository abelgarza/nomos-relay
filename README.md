# Nomos Relay

<p align="center">
  <img src="https://img.shields.io/github/actions/workflow/status/abelgarza/nomos-relay/ci.yml?branch=main&style=for-the-badge&logo=github" alt="CI Status">
  <img src="https://img.shields.io/github/license/abelgarza/nomos-relay?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Node.js-20+-339933?style=for-the-badge&logo=nodedotjs&logoColor=white" alt="Node Version">
  <img src="https://img.shields.io/badge/Ollama-Compatible-black?style=for-the-badge&logo=ollama" alt="Ollama">
</p>

---

**Nomos Relay** is a cybernetic orchestration framework for local AI agents. It provides a deterministic bridge between stochastic reasoning models and secure system execution.

Inspired by the concept of *Nomos* (the ordering of space and law) and the *Caveman* philosophy of linguistic compression, this tool ensures that local agents (like Gemma 4) operate within strict safety boundaries while maintaining perfect structural integrity in their output.

## Key Features

- **Cognitive Memory (RAG):** Deep codebase context using LanceDB and Ollama embeddings.
- **Fail-Closed Governance:** Strict security profiles (read-only, repo-safe, developer).
- **Universal Proxy:** OpenAI-compatible middleware for seamless integration with Cursor and OpenCode.
- **Cybernetic Regulation:** Deterministic Planning/Relay architecture.

## Tech Stack

<p align="left">
  <img src="https://img.shields.io/badge/Gemma_4-Model-blue?style=flat-square&logo=googlegemini" alt="Gemma 4">
  <img src="https://img.shields.io/badge/LanceDB-Vector_DB-orange?style=flat-square" alt="LanceDB">
  <img src="https://img.shields.io/badge/Ollama-Inference-black?style=flat-square" alt="Ollama">
  <img src="https://img.shields.io/badge/Pytest-Testing-white?style=flat-square&logo=pytest" alt="Pytest">
</p>

## Core Components

- **`nomos.py`**: The runtime engine. Manages the task lifecycle, enforces profile policies, and validates command safety.
- **`nomos_rag.py`**: Cognitive memory engine. Uses LanceDB and Ollama embeddings to provide deep codebase context.
- **`proxy.js`**: OpenAI-compatible middleware with integrated RAG support.
- **`Modelfiles`**: The "Constitutions" of the agent. Baked-in behavioral constraints.

## Getting Started

### 1. Install Dependencies
```bash
pip install lancedb pandas requests pytest
```

### 2. Build the Models
```bash
./build.sh
```

### 3. Index your Workspace (RAG)
```bash
python3 nomos.py index
```

### 4. Run a Task
```bash
python3 nomos.py --workspace ~/my-project --profile repo-safe "Initialize a git repository" --execute
```

## Testing
Nomos prioritizes reliability through formal verification.
```bash
PYTHONPATH=. pytest tests/
```

## State & Audit
Every workspace managed by Nomos contains a `.nomos/` directory:
- `vector_store/`: Persistent LanceDB database.
- `journal.log`: Chronological record of all intents and actions.
- `last_plan.txt`: The reasoning trace.
- `last_relay.json`: The structured command output.

## License
This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

---
*Created by Abel Garza Ramírez. A Cybernetic approach to AI Agency.*
