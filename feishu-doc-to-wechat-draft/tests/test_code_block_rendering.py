from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown


def test_code_block_does_not_double_escape_quotes_and_preserves_highlight_markup() -> None:
    md = '''```python\ndef hello(name):\n    print(f"hi {name}")\n```\n'''
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        font_size=14,
        code_theme="github",
        mac_code_block=True,
        code_line_numbers=False,
    ).html

    assert '&amp;quot;' not in html
    assert 'md-code-window-dots' in html
    assert '<br/>' in html
    assert 'style="color:' in html or 'style="font-weight:' in html
    assert 'print' in html


def test_code_block_line_numbers_match_nonempty_code_lines_without_trailing_blank() -> None:
    md = '''```python\ndef hello(name):\n    return name\n```\n'''
    html = render_markdown(
        md,
        profile="doocs",
        theme="default",
        code_theme="github",
        mac_code_block=False,
        code_line_numbers=True,
    ).html

    assert 'class="line-numbers"' in html
    assert '>1</section>' in html
    assert '>2</section>' in html
    assert '>3</section>' not in html
