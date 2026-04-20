#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ "${1:-}" == "--install-dependencies" ]]; then
  "${PYTHON_BIN}" -m pip install --upgrade pip
  "${PYTHON_BIN}" -m pip install -r requirements/requirements.txt
fi

echo "Building Cetamura Batch Ingest for macOS..."
"${PYTHON_BIN}" -m PyInstaller src/main.py \
  --name "CetamuraBatchIngest" \
  --onefile \
  --windowed \
  --clean \
  --noconfirm \
  --hidden-import="PIL" \
  --hidden-import="fitz" \
  --collect-all="fitz"

chmod +x dist/CetamuraBatchIngest
echo "Build successful: dist/CetamuraBatchIngest"
