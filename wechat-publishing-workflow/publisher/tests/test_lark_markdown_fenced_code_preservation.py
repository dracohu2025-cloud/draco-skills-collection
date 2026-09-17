from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.lark_docs import normalize_lark_markdown


def test_strong_numbered_heading_before_fenced_code_keeps_opening_fence() -> None:
    source = """## 前置准备
使用之前需要准备三样东西：
**1. 飞书 CLI 工具**
```bash
npm install -g @larksuiteoapi/lark-cli
lark-cli login

```

登录一次后，工具就能访问你有权限的飞书文档。
"""
    normalized = normalize_lark_markdown(source)

    assert "```bash" in normalized
    assert "npm install -g @larksuiteoapi/lark-cli" in normalized
    assert normalized.count("```") >= 2
