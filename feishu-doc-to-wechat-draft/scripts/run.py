#!/usr/bin/env python3
"""Standalone launcher for Feishu doc -> WeChat draft publisher."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from wechat_draft_publisher.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
