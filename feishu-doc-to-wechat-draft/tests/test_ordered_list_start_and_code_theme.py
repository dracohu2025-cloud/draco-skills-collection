from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown


def test_ordered_list_keeps_start_attribute_when_markdown_starts_at_two() -> None:
    md = "2. 第二项\n3. 第三项\n"
    html = render_markdown(md, profile="doocs", theme="grace", font_size=14).html
    assert '<ol start="2">' in html
    assert '>第二项</li>' in html
    assert '>第三项</li>' in html


def test_code_blocks_use_same_light_background_under_default_github_theme() -> None:
    md = '```bash\necho hello\n```\n\n```python\nprint("hi")\n```\n'
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        code_theme="github",
        mac_code_block=True,
        font_size=14,
    ).html
    assert html.count('background: #f6f8fa;') >= 2
    assert 'background: #24292f;' not in html
