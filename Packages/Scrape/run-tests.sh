#!/usr/bin/env bash
# Run the whole suite. No dependencies, no network, no fixtures to install.
#
#   ./run-tests.sh            # quiet
#   ./run-tests.sh -v         # per-test names
set -euo pipefail
cd "$(dirname "$0")"
exec python3 -m unittest discover -s tests -t tests "$@"
