#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" != "--global" ]; then
    python3.11 -m venv .venv
    source .venv/bin/activate
fi

pip install pip-tools
pip-compile requirements.in
pip-compile requirements-dev.in
pip install -r requirements.txt
pip install -r requirements-dev.txt
# pip install -e .
