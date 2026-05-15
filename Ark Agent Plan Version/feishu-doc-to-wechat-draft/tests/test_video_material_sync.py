from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.lark_docs import normalize_lark_markdown
from wechat_draft_publisher.renderer import render_markdown
from wechat_draft_publisher.wechat_api import rewrite_html_assets


def test_lark_video_view_block_becomes_placeholder_tag() -> None:
    source = """## 示例

<view type="2">
  <file token="t1" name="seedance-rollercoaster-11s-480p.mp4"></file>
</view>
"""

    normalized = normalize_lark_markdown(source)

    assert '<wechat-video token="t1" name="seedance-rollercoaster-11s-480p.mp4" />' in normalized
    assert '<view type="2">' not in normalized
    assert '<file token=' not in normalized


def test_render_markdown_turns_video_placeholder_into_preview_card() -> None:
    html = render_markdown(
        '<wechat-video token="tok_123" name="demo-video.mp4" />',
        profile="doocs",
        theme="grace",
        font_size=14,
    ).html

    assert 'class="md-video-card"' in html
    assert 'data-video-token="tok_123"' in html
    assert 'data-video-name="demo-video.mp4"' in html
    assert '视频：demo-video.mp4' in html
    assert '<wechat-video' not in html
    assert '</wechat-video>' not in html


class _FakeWechatClient:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def upload_content_image(self, path: str, access_token: str) -> str:
        self.calls.append(("upload_content_image", Path(path).name, access_token))
        return "https://mmbiz.qpic.cn/mock/video-cover.jpg"

    def upload_video_material(self, path: str, access_token: str, *, title: str, introduction: str) -> str:
        self.calls.append(("upload_video_material", Path(path).name, access_token, title, introduction))
        return "mock_video_media_id"


def test_rewrite_html_assets_uploads_video_material_and_replaces_card(tmp_path, monkeypatch) -> None:
    html = (
        '<section class="wechat-article">'
        '<figure class="md-video-card" data-video-token="tok_video" data-video-name="demo-video.mp4">'
        '<section class="md-video-card-poster">▶</section>'
        '<figcaption class="md-video-card-caption">视频：demo-video.mp4</figcaption>'
        '</figure>'
        '</section>'
    )

    video_path = tmp_path / "demo-video.mp4"
    video_path.write_bytes(b"video-bytes")
    poster_path = tmp_path / "demo-video-cover.jpg"
    poster_path.write_bytes(b"poster-bytes")

    monkeypatch.setattr(
        "wechat_draft_publisher.wechat_api._download_lark_media",
        lambda token, output_dir, filename=None: video_path,
    )
    monkeypatch.setattr(
        "wechat_draft_publisher.wechat_api._extract_video_poster",
        lambda video_path_arg, output_dir: poster_path,
    )

    client = _FakeWechatClient()
    rewritten_html, video_materials = rewrite_html_assets(
        html=html,
        article_dir=tmp_path,
        client=client,
        access_token="token_123",
        source_url="https://example.com/source-doc",
    )

    assert "mock_video_media_id" not in rewritten_html
    assert "https://mmbiz.qpic.cn/mock/video-cover.jpg" in rewritten_html
    assert "已同步到公众号视频素材库" in rewritten_html
    assert "公众号正文暂不支持内嵌播放" in rewritten_html
    assert video_materials == [
        {
            "token": "tok_video",
            "name": "demo-video.mp4",
            "media_id": "mock_video_media_id",
            "cover_url": "https://mmbiz.qpic.cn/mock/video-cover.jpg",
            "source_url": "https://example.com/source-doc",
        }
    ]
    assert ("upload_video_material", "demo-video.mp4", "token_123", "demo-video", "来自飞书文档同步的视频素材：demo-video.mp4") in client.calls
    assert ("upload_content_image", "demo-video-cover.jpg", "token_123") in client.calls


def test_rewrite_html_assets_fails_when_lark_image_cannot_sync(tmp_path, monkeypatch) -> None:
    html = '<section><img src="lark-image://img_token_123" /></section>'

    def fail_download(token, output_dir):
        raise RuntimeError("lark-cli not configured")

    monkeypatch.setattr(
        "wechat_draft_publisher.wechat_api._download_lark_image",
        fail_download,
    )

    client = _FakeWechatClient()
    with pytest.raises(RuntimeError, match="Failed to sync Lark image img_token_123"):
        rewrite_html_assets(
            html=html,
            article_dir=tmp_path,
            client=client,
            access_token="token_123",
            source_url="https://example.com/source-doc",
        )

    assert client.calls == []
