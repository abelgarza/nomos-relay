#!/usr/bin/env bash
set -euo pipefail

# Build new Nomos models
echo "--- Building Nomos Models ---"
ollama pull nomic-embed-text
ollama create gemma4-nomos -f gemma4-nomos.Modelfile
ollama create gemma4-nomos-relay -f gemma4-nomos-relay.Modelfile
ollama create gemma4-nomos-cloud -f gemma4-nomos-cloud.Modelfile

echo "Build complete."
