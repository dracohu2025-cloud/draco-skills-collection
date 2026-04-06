from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown


def test_shell_code_block_uses_terminal_style_when_mac_mode_enabled() -> None:
    md = '```bash\necho "hello"\n```\n'
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        code_theme="github",
        mac_code_block=True,
    ).html

    assert 'md-code-window-title' in html
    assert '>terminal<' in html
    assert 'background: #24292f;' in html
    assert 'color: #e6edf3;' in html
