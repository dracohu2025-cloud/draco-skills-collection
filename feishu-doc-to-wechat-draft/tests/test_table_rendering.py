from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown


def test_doocs_grace_tables_use_fixed_balanced_columns_and_wrap_cell_text() -> None:
    md = """| 命令 | 用途 |
| --- | --- |
| `hermes chat` | 与 Agent 进行交互式或一次性聊天，描述比较长也不应该把第一列挤扁。 |
| `hermes gateway` | 运行或管理消息网关服务。 |
"""

    html = render_markdown(md, profile="doocs", theme="grace", font_size=14).html

    assert 'class="md-table"' in html
    assert 'table-layout: fixed' in html
    assert 'width: 100%' in html
    assert 'word-break: break-word' in html
    assert 'overflow-wrap: anywhere' in html
    assert 'box-sizing: border-box' in html
