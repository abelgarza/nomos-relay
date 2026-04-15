#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
NOMOS="/home/abelg/dev/personal/.venv_py314/bin/nomos"

echo "== nomos: workspace tests =="

# 1. Read-only profile test
echo -e "\n1. [READ-ONLY PROFILE] blocked mutation"
mkdir -p /tmp/nomos-smoke-tests
$NOMOS --workspace /tmp/nomos-smoke-tests --profile read-only "touch blocked.txt" --execute

# 2. Repo-safe profile test
echo -e "\n2. [REPO-SAFE PROFILE] touch file in /tmp/nomos-test"
mkdir -p /tmp/nomos-test
rm -rf /tmp/nomos-test/.nomos /tmp/nomos-test/hello.txt
$NOMOS --workspace /tmp/nomos-test --profile repo-safe "touch hello.txt" --execute

# 3. Protocol tests via pytest
echo -e "\n3. [PROTOCOL] running schema validation tests"
pytest "$DIR/tests/protocol/test_schema.py"

# 4. State check
echo -e "\n== nomos: state check =="
for dir in /tmp/nomos-smoke-tests /tmp/nomos-test; do
    if [ -d "$dir/.nomos" ]; then
        echo "Logs found in $dir/.nomos/"
        # echo "--- Journal Content ($dir) ---"
        # cat "$dir/.nomos/journal.log"
    else
        echo "ERROR: .nomos directory not found in $dir"
        exit 1
    fi
done

echo -e "\n== SMOKE TEST COMPLETE =="
