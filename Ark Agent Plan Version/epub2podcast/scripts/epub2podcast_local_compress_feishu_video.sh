#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

if [[ ! -d node_modules ]]; then
  echo "Dependencies not installed. Running npm install..."
  npm install
fi

npm run build >/dev/null
exec node dist/cli/compress-video.js "$@"
