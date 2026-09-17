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
    assert 'padding:10px 14px 0' in html
    assert 'padding-left: 14px;padding-top: 8px' in html
    assert 'background: #f6f8fa;' in html
    assert 'padding: 0 14px 14px' in html
    assert 'padding: 0 0 1.1em' in html
    assert 'md-code-window-title' not in html
    assert 'background: #24292f;' not in html


def test_mac_code_block_locks_width_and_wraps_long_lines() -> None:
    md = '```yaml\nstyle:\n  primary_color: "#FA5151"\n  font_family: "-apple-system, BlinkMacSystemFont, Helvetica Neue, PingFang SC, Microsoft YaHei"\n```\n'
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        code_theme="github",
        mac_code_block=True,
        code_line_numbers=False,
    ).html

    assert 'md-code-scroll-wrap' in html
    assert 'md-pre md-pre-mac' in html
    assert 'font-size: 12px' in html
    assert 'overflow-x: hidden;' in html
    assert 'overflow-x: auto' not in html
    assert '-webkit-overflow-scrolling' not in html
    assert 'display: block; min-width: 0; max-width: 100%; width: 100%;' in html
    assert 'white-space: pre-wrap' in html
    assert 'overflow-wrap: anywhere' in html
    assert 'max-width: none' not in html
    assert '</pre></section>' in html


def test_plain_prompt_code_block_wraps_instead_of_horizontal_clipping() -> None:
    md = '''```sql
生成一张专业电影角色设定表：CHARACTER REFERENCE SHEET。只画一只黑猫。
重点：底部必须清楚出现一个独立大区块，英文标题必须是 HAND/PAW GESTURE。
- Top row left: CHARACTER REFERENCE SHEET title + horizontal info block.
- Center largest section: MAIN IDENTITY + SCALE SHEET. Same subject.
```\n'''
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        code_theme="github",
        mac_code_block=True,
        code_line_numbers=False,
    ).html

    assert 'white-space: pre-wrap' in html
    assert 'overflow-wrap: anywhere' in html
    assert 'min-width: max-content' not in html
    assert 'CHARACTER REFERENCE SHEET title + horizontal info block' in html
    assert 'CHARACTER&nbsp;REFERENCE' not in html


def test_feishu_mislabeled_javascript_terminal_block_gets_shell_comments_not_red_errors() -> None:
    md = '''```javascript {wrap}
memos init --agent hermes    # ~/.hermes/skills/memos/
memos init --agent codex     # ~/.codex/skills/memos/
```\n'''
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        code_theme="github",
        mac_code_block=True,
        code_line_numbers=False,
    ).html

    assert 'class="language-bash"' in html
    assert 'border: 1px solid #F00' not in html
    assert '#&nbsp;~/.hermes/skills/memos/' in html
    assert 'color: #6A737D' in html
    assert 'hermes&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #6A737D; font-style: italic">#&nbsp;~/.hermes/skills/memos/</span>' in html
