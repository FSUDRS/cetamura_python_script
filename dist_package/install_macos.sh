#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS="${SCRIPT_DIR}/requirements/requirements.txt"
MAIN_SCRIPT="${SCRIPT_DIR}/src/main.py"

if [[ ! -f "${REQUIREMENTS}" ]]; then
  REQUIREMENTS="$(cd "${SCRIPT_DIR}/.." && pwd)/requirements/requirements.txt"
fi

if [[ ! -f "${MAIN_SCRIPT}" ]]; then
  MAIN_SCRIPT="$(cd "${SCRIPT_DIR}/.." && pwd)/src/main.py"
fi

echo "macOS - Cetamura Batch Ingest Tool Installer"
echo "============================================"

if [[ "${OSTYPE:-}" != darwin* ]]; then
  echo "This installer is intended for macOS."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.9+ is not installed or not in PATH."
  echo "Install Python from https://www.python.org/downloads/ or Homebrew."
  exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install -r "${REQUIREMENTS}"

echo "Installation completed successfully."
echo "Run from source with:"
echo "python3 \"${MAIN_SCRIPT}\""
