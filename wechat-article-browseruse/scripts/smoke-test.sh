#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[smoke] checking python3"
python3 --version

echo "[smoke] checking required commands"
git --version
node --version
npm --version

echo "[smoke] checking CLI help"
python3 scripts/run.py --help >/dev/null
python3 scripts/fetch_wechat_article.py --help >/dev/null
python3 scripts/publish_wechat_article_to_feishu.py --help >/dev/null

echo "[smoke] ok"
