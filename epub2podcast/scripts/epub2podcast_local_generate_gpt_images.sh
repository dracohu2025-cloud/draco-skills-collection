#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENTRY_SRC="$PROJECT_ROOT/src/generateGptImageSlides.ts"
ENTRY_DIST="$PROJECT_ROOT/dist/generateGptImageSlides.js"

cd "$PROJECT_ROOT"

if [[ ! -f "$ENTRY_DIST" || "$ENTRY_SRC" -nt "$ENTRY_DIST" ]]; then
  npm run build >/dev/null
fi

exec node "$ENTRY_DIST" "$@"
