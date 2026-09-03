#!/usr/bin/env bash
# Declared runner for Packages/Sentinel (PROCESS.md: declared-runner).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
python3 -m unittest discover -s tests -t . -v
