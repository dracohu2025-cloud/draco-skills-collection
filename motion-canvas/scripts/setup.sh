#!/usr/bin/env bash
set -euo pipefail

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 1; }
}

need node
need npm

echo "node: $(node -v)"
echo "npm:  $(npm -v)"

if command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg: $(ffmpeg -version | head -n 1)"
else
  echo "ffmpeg: not found (preview/editor still fine; final video export may need it)"
fi

echo "npm package:"
npm view @motion-canvas/create version description --json

echo

echo "Bootstrap with:"
echo "  npx @motion-canvas/create@latest"
