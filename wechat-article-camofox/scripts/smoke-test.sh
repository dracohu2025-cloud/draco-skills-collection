#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

check_cmd() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "[FAIL] missing command: $name" >&2
    exit 1
  fi
  echo "[OK] command available: $name"
}

echo "[INFO] project root: $ROOT"
check_cmd python3
check_cmd git
check_cmd node
check_cmd npm

echo "[INFO] python: $(python3 --version 2>&1)"
echo "[INFO] git: $(git --version 2>&1)"
echo "[INFO] node: $(node --version 2>&1)"
echo "[INFO] npm: $(npm --version 2>&1)"

echo "[INFO] checking CLI help"
python3 "$ROOT/scripts/run.py" --help >/dev/null
python3 "$ROOT/scripts/run.py" fetch --help >/dev/null
python3 "$ROOT/scripts/run.py" publish-feishu --help >/dev/null

echo "[PASS] smoke test passed"
