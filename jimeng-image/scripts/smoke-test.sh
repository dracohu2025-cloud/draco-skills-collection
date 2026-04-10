#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/4] python3"
python3 --version

echo "[2/4] unified entrypoint help"
python3 scripts/run.py --help >/dev/null

echo "[3/4] single-image help"
python3 scripts/jimeng_image.py --help >/dev/null

echo "[4/4] env check"
if [ -n "${VOLCENGINE_API_KEY:-${SEEDREAM_API_KEY:-${JIMENG_API_KEY:-}}}" ]; then
  echo "VOLCENGINE_API_KEY=*** present"
else
  echo "VOLCENGINE_API_KEY=*** missing"
fi

echo "smoke_test=ok"
