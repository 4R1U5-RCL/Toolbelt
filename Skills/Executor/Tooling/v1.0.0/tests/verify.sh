#!/usr/bin/env bash
# Executor — declared runner. Runs the process-gate self-test suite.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Executor v1.0.0 — process-gate self-test"
echo "python3: $(python3 --version 2>&1)"
echo
python3 "$HERE/selftest.py" "$@"
