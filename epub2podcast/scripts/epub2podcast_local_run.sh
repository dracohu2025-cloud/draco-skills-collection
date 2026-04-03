#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${EPUB2PODCAST_PROJECT_ROOT:-}"
ENTRY_REL="dist/localPipeline.js"
SRC_REL="src/localPipeline.ts"

if [[ -z "$PROJECT_ROOT" ]]; then
  echo "Please set EPUB2PODCAST_PROJECT_ROOT to your epub2podcast-local/frontend/server path." >&2
  exit 1
fi

ENTRY_SRC="$PROJECT_ROOT/$SRC_REL"
ENTRY_DIST="$PROJECT_ROOT/$ENTRY_REL"

cd "$PROJECT_ROOT"

if [[ ! -f "$ENTRY_DIST" || "$ENTRY_SRC" -nt "$ENTRY_DIST" ]]; then
  npm run build
fi

exec node "$ENTRY_DIST" "$@"
