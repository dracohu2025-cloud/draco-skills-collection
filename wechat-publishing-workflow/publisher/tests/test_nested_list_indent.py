"""Nested list hierarchy must survive inline-list rendering."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown

NESTED_MD = """- 一级A
  - 二级A1
  - 二级A2
    - 三级A2x
- 一级B

1. 有序一
   - 有序下的二级
2. 有序二
"""


def _render():
    return render_markdown(
        NESTED_MD, profile="doocs", theme="grace", font_size=14
    ).html


def test_nested_items_keep_own_paragraphs() -> None:
    html = _render()
    # every nested item gets its own <p>, not <br>-joined spans
    assert html.count('class="md-bullet-item"') == 6  # 一级A/B + 二级x2 + 三级 + 有序下二级
    assert "<br/>" not in html.split('md-list-depth-1')[1].split('</section>')[0]


def test_nested_indent_deepens_per_level() -> None:
    html = _render()
    assert "padding-left: 1.6em" in html  # depth 0
    assert "padding-left: 3.2em" in html  # depth 1
    assert "padding-left: 4.8em" in html  # depth 2


def test_nested_sections_are_block_siblings_not_inline() -> None:
    html = _render()
    # nested list section must not live inside a text span
    assert '<span class="md-bullet-text" style="display: inline; text-align: left;">一级A\n<section' not in html
