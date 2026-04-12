#!/usr/bin/env bash
set -euo pipefail

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 1; }
}

need node
need npm

echo "node: $(node -v)"
echo "npm:  $(npm -v)"

echo "create-video:"
npm view create-video version description --json

echo "remotion:"
npm view remotion version --json

if command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg: $(ffmpeg -version | head -n 1)"
else
  echo "ffmpeg: not found"
fi

echo
echo "Scaffold with: npx create-video@latest --yes --blank --no-tailwind my-video"
