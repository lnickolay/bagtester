#!/usr/bin/env bash
set -euo pipefail

# TODO: validate Python version (python3 may point to the wrong interpreter)
if [ "${1:-}" != "--global" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
fi

pip install pip-tools
pip-compile requirements.in
pip-compile requirements-dev.in
pip install -r requirements.txt
pip install -r requirements-dev.txt
# pip install -e .
