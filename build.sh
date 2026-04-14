#!/usr/bin/env bash
set -euo pipefail

# Build new Nomos models
echo "--- Building Nomos Models ---"
ollama create gemma4-nomos -f gemma4-nomos.Modelfile
ollama create gemma4-nomos-relay -f gemma4-nomos-relay.Modelfile
ollama create gemma4-nomos-cloud -f gemma4-nomos-cloud.Modelfile

# Cleanup old Caveman models
echo "--- Cleaning up old Caveman models ---"
ollama rm gemma4-caveman:latest || true
ollama rm gemma4-caveman-relay:latest || true
ollama rm gemma4-caveman-cloud:latest || true

echo "Build and cleanup complete."
