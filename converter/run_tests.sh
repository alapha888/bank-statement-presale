#!/usr/bin/env bash
# Single-command test entry point. Run from converter/:
#   ./run_tests.sh
# Regenerates fixtures, then runs the full validation (pytest + CLI smoke).
set -euo pipefail
cd "$(dirname "$0")"
VENV=.venv/bin/python
if [ ! -x "$VENV" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements-dev.txt
fi
"$VENV" fixtures/generate_fixtures.py
"$VENV" fixtures/generate_edge_fixtures.py
"$VENV" fixtures/make_scanned_fixture.py
"$VENV" -m pytest test_converter.py test_gui.py test_edge_cases.py test_update_check.py -v
