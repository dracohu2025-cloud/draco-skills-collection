import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_wechat_article.py"
spec = importlib.util.spec_from_file_location("fetch_wechat_article_browseruse", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_resolve_api_key_accepts_browseruse_alias(monkeypatch):
    monkeypatch.delenv("BROWSER_USE_API_KEY", raising=False)
    monkeypatch.setenv("BROWSERUSE_API_KEY", "bu_demo")

    assert module._resolve_api_key() == "bu_demo"


def test_prepare_html_promotes_data_src_and_can_strip_images():
    html = """
    <div id="js_content">
      <img data-src="https://example.com/hero.jpg" src="data:image/png;base64,xxx" alt="hero">
      <p>第一段</p>
      <script>alert(1)</script>
    </div>
    """

    keep_images = module._prepare_html(html, include_images=True)
    drop_images = module._prepare_html(html, include_images=False)

    assert 'src="https://example.com/hero.jpg"' in keep_images
    assert "alert(1)" not in keep_images
    assert "<img" not in drop_images
    assert "第一段" in drop_images


def test_cleanup_markdown_collapses_adjacent_bold_and_blank_lines():
    raw = "段落A\n\n\n**与AI合著了一本名为****《催眠统治》**\n\n\n段落B\n"

    cleaned = module._cleanup_markdown(raw)

    assert cleaned == "段落A\n\n**与AI合著了一本名为《催眠统治》**\n\n段落B"


def test_to_markdown_wraps_meta_and_body():
    meta = {
        "title": "标题",
        "author": "作者甲",
        "published_at": "2026年1月26日 11:31",
        "content_markdown": "第一段\n\n第二段",
    }

    markdown = module._to_markdown(meta)

    assert markdown.startswith("# 标题\n")
    assert "_作者：作者甲 · 发布时间：2026年1月26日 11:31_" in markdown
    assert markdown.rstrip().endswith("第二段")


def test_normalize_images_dedupes_and_skips_placeholders():
    images = [
        {"src": "data:image/png;base64,abc", "alt": "inline"},
        {"src": "https://example.com/a.jpg", "alt": "A"},
        {"src": "https://example.com/a.jpg", "alt": "A again"},
        {"src": "https://res.wx.qq.com/op_res/placeholder.png", "alt": "placeholder"},
        {"src": "https://example.com/b.jpg", "alt": "B"},
    ]

    cleaned = module._normalize_images(images, article_url="https://mp.weixin.qq.com/s/demo")

    assert cleaned == [
        {"src": "https://example.com/a.jpg", "alt": "A"},
        {"src": "https://example.com/b.jpg", "alt": "B"},
    ]
