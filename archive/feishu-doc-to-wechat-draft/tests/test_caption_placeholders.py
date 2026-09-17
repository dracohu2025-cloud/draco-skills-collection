from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown


def test_generic_image_alt_does_not_become_caption() -> None:
    html = render_markdown(
        "![image](x.png)\n",
        profile="doocs",
        theme="grace",
        caption_mode="alt-first",
    ).html

    assert '<img src="x.png" alt="image"' in html
    assert "md-figure-caption" not in html
    assert ">image</figcaption>" not in html


def test_real_caption_is_preserved_when_alt_is_generic() -> None:
    html = render_markdown(
        '![image](x.png "准确的图片说明")\n',
        profile="doocs",
        theme="grace",
        caption_mode="alt-first",
    ).html

    assert "md-figure-caption" in html
    assert ">准确的图片说明</figcaption>" in html


def test_real_alt_caption_is_preserved() -> None:
    html = render_markdown(
        "![策略回测结果](x.png)\n",
        profile="doocs",
        theme="grace",
        caption_mode="alt-first",
    ).html

    assert ">策略回测结果</figcaption>" in html
