#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$REPO_DIR/src/frontend"

PYTHON_BIN="${MARK_PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
    if [ -x /opt/jarvis/venv/bin/python ]; then
        PYTHON_BIN=/opt/jarvis/venv/bin/python
    else
        PYTHON_BIN=python3
    fi
fi

cd "$FRONTEND_DIR"
export PYTHONPATH="$FRONTEND_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON_BIN" app.py
