#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  install-template-pack.sh <open-slide-project-dir> [--all|--official|--od] [--overwrite]

Copies bundled Open Slide decks into <project>/slides/.
Default: --all, no overwrite.
EOF
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK="$ROOT/templates/open-slide-template-pack"
SRC="$PACK/slides"
MANIFEST="$PACK/manifest.json"

if [[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

TARGET="$1"
shift || true
MODE="all"
OVERWRITE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) MODE="all" ;;
    --official) MODE="open-slide-official" ;;
    --od) MODE="open-design-ported" ;;
    --overwrite) OVERWRITE=1 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

if [[ ! -d "$TARGET" ]]; then
  echo "Target directory does not exist: $TARGET" >&2
  exit 2
fi

mkdir -p "$TARGET/slides"

python3 - "$MANIFEST" "$SRC" "$TARGET/slides" "$MODE" "$OVERWRITE" <<'PY'
from pathlib import Path
import json, shutil, sys
manifest = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
src = Path(sys.argv[2])
dst = Path(sys.argv[3])
mode = sys.argv[4]
overwrite = sys.argv[5] == '1'
selected = [d for d in manifest['decks'] if mode == 'all' or d['category'] == mode]
copied = skipped = 0
for deck in selected:
    slug = deck['slug']
    s = src / slug
    t = dst / slug
    if not s.exists():
        raise SystemExit(f'missing bundled deck: {s}')
    if t.exists():
        if not overwrite:
            print(f'skip existing {slug}')
            skipped += 1
            continue
        shutil.rmtree(t)
    shutil.copytree(s, t)
    print(f'copied {slug}')
    copied += 1
print(json.dumps({'copied': copied, 'skipped': skipped, 'mode': mode}, ensure_ascii=False))
PY
