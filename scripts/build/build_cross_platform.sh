#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "${OSTYPE:-}" in
  darwin*)
    exec "${SCRIPT_DIR}/build_exe_macos.sh" "$@"
    ;;
  linux-gnu*)
    PYTHON_BIN="${PYTHON_BIN:-python3}"
    REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
    cd "${REPO_ROOT}"

    if [[ "${1:-}" == "--install-dependencies" ]]; then
      "${PYTHON_BIN}" -m pip install --upgrade pip
      "${PYTHON_BIN}" -m pip install -r requirements/requirements.txt
    fi

    echo "Building Cetamura Batch Ingest for Linux..."
    "${PYTHON_BIN}" -m PyInstaller src/main.py \
      --name "CetamuraBatchIngest" \
      --onefile \
      --clean \
      --noconfirm \
      --hidden-import="PIL" \
      --hidden-import="fitz" \
      --collect-all="fitz"

    chmod +x dist/CetamuraBatchIngest
    echo "Build successful: dist/CetamuraBatchIngest"
    ;;
  msys*|cygwin*)
    echo "Use PowerShell on Windows: .\\scripts\\build\\build_exe.ps1"
    exit 1
    ;;
  *)
    echo "Unsupported OS type: ${OSTYPE:-unknown}"
    exit 1
    ;;
esac
