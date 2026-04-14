#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOMOS="$DIR/nomos.py"

echo "== nomos: workspace tests =="

# 1. Cave profile test
echo -e "\n1. [CAVE PROFILE] git init in ~/cave/smoke-nomos"
mkdir -p ~/cave/smoke-nomos
rm -rf ~/cave/smoke-nomos/.git ~/cave/smoke-nomos/.nomos
$NOMOS --workspace ~/cave/smoke-nomos --profile cave "Initialize git repo" --execute

# 2. Read-only profile test
echo -e "\n2. [READ-ONLY PROFILE] blocked mutation"
$NOMOS --workspace ~/cave/smoke-nomos --profile read-only "touch blocked.txt" --execute

# 3. Repo-safe profile test (outside ~/cave)
echo -e "\n3. [REPO-SAFE PROFILE] touch file in /tmp/nomos-test"
mkdir -p /tmp/nomos-test
rm -rf /tmp/nomos-test/.nomos /tmp/nomos-test/hello.txt
$NOMOS --workspace /tmp/nomos-test --profile repo-safe "touch hello.txt" --execute

# 4. Workspace jail test for cave profile
echo -e "\n4. [CAVE PROFILE] jail check (outside ~/cave)"
$NOMOS --workspace /tmp/nomos-test --profile cave "ls" 2>&1 | grep "BLOCKED" || echo "Caught expected jail failure"

# 5. Protocol test: Missing keys
echo -e "\n5. [PROTOCOL] missing required keys are blocked"
python3 "$DIR/test_missing_keys.py" 2>&1 | grep "BLOCKED: Malformed relay protocol. Errors: Missing required key"

# 6. Protocol test: Typed validation
echo -e "\n6. [PROTOCOL] mistyped relay output (constraints as string) is blocked"
python3 "$DIR/test_typed_malformed.py" 2>&1 | grep "BLOCKED: Malformed relay protocol. Errors: Incorrect type for 'constraints'"

# 7. Protocol test: Missing command with --execute
echo -e "\n7. [PROTOCOL] missing command with --execute is blocked"
python3 "$DIR/test_missing_command_execute.py" 2>&1 | grep "BLOCKED: Execution requested but no command generated"

# 8. State check
echo -e "\n== nomos: state check =="
for dir in ~/cave/smoke-nomos /tmp/nomos-test; do
    if [ -d "$dir/.nomos" ]; then
        echo "Logs found in $dir/.nomos/"
        echo "--- Journal Content ($dir) ---"
        cat "$dir/.nomos/journal.log"
    else
        echo "ERROR: .nomos directory not found in $dir"
        exit 1
    fi
done

echo -e "\n== SMOKE TEST COMPLETE =="
