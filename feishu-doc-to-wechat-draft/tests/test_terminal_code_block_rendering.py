from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown


def test_shell_code_block_uses_mac_dots_but_keeps_doocs_light_theme() -> None:
    md = '```bash\necho "hello"\n```\n'
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        code_theme="github",
        mac_code_block=True,
    ).html

    assert 'md-code-window-dots' in html
    assert 'background: #f6f8fa;' in html
    assert 'md-code-window-title' not in html
    assert 'background: #24292f;' not in html


def test_mac_code_block_keeps_pre_as_horizontal_scroll_container() -> None:
    md = '```yaml\nstyle:\n  primary_color: "#FA5151"\n  font_family: "-apple-system, BlinkMacSystemFont, Helvetica Neue, PingFang SC, Microsoft YaHei"\n```\n'
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        code_theme="github",
        mac_code_block=True,
        code_line_numbers=False,
    ).html

    assert 'md-pre md-pre-mac' in html
    assert 'overflow-x: auto; overflow-y: hidden;' in html
    assert '-webkit-overflow-scrolling: touch;' in html
    assert 'overflow: hidden;' not in html
