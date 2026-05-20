#!/usr/bin/env bash
set -euo pipefail

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "[ok] $1"
  else
    echo "[missing] $1"
  fi
}

echo "== Runtime commands =="
check_cmd node
check_cmd npm
check_cmd ffmpeg
check_cmd ffprobe

echo
if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
  echo "[ok] OPENROUTER_API_KEY set"
else
  echo "[warn] OPENROUTER_API_KEY not set"
fi

if [[ -n "${VOLCENGINE_ACCESS_TOKEN:-}" ]]; then
  echo "[ok] VOLCENGINE_ACCESS_TOKEN set"
else
  echo "[warn] VOLCENGINE_ACCESS_TOKEN not set"
fi

if [[ -n "${VOLCENGINE_APP_ID:-}" ]]; then
  echo "[ok] VOLCENGINE_APP_ID set"
else
  echo "[warn] VOLCENGINE_APP_ID not set"
fi

echo
echo "== Build check =="
npm run build
