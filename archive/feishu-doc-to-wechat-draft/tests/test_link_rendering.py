from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown


def test_bare_urls_become_blue_underlined_links() -> None:
    result = render_markdown("访问网址：https://maas.xfyun.cn/modelSquare?ch=maas-cg-kol-84")

    assert "https://maas.xfyun.cn/modelSquare?ch=maas-cg-kol-84</span>" in result.html
    assert 'href="https://maas.xfyun.cn/modelSquare?ch=maas-cg-kol-84"' not in result.html
    assert "color: #1e6bd6" in result.html
    assert "text-decoration: underline" in result.html


def test_fenced_urls_remain_plain_code() -> None:
    result = render_markdown("```yaml\nhttps://maas-api.cn-huabei-1.xf-yun.com/anthropic\n```")

    assert "maas-api.cn-huabei-1.xf-yun.com/anthropic" in result.html
    assert 'href="https://maas-api.cn-huabei-1.xf-yun.com/anthropic"' not in result.html
