#!/usr/bin/env bash
set -euo pipefail

# Resolve script directory
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$DIR"

# Build new Nomos models
echo "--- Building Nomos Models ---"
ollama pull nomic-embed-text
ollama create gemma4-nomos -f models/gemma4-nomos.Modelfile
ollama create gemma4-nomos-relay -f models/gemma4-nomos-relay.Modelfile
ollama create gemma4-nomos-cloud -f models/gemma4-nomos-cloud.Modelfile
ollama create gemma4-nomos-git -f models/gemma4-nomos-git.Modelfile
ollama create gemma4-nomos-overlord -f models/gemma4-nomos-overlord.Modelfile

echo "Build complete."
