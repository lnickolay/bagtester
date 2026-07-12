#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${1:-.venv}"

python3 -m venv "$VENV_DIR"
"$VENV_DIR"/bin/pip install pip-tools
"$VENV_DIR"/bin/pip-compile requirements.in
"$VENV_DIR"/bin/pip-compile requirements-dev.in
"$VENV_DIR"/bin/pip install -r requirements.txt
"$VENV_DIR"/bin/pip install -r requirements-dev.txt
"$VENV_DIR"/bin/pip install -e .
