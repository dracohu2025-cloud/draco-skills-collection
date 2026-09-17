from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.draft import build_draft_payload
from wechat_draft_publisher.models import ArticleInput
from wechat_draft_publisher.renderer import render_markdown
from wechat_draft_publisher.wechat_api import rewrite_html_assets


class _FakeClientWithVid:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def upload_content_image(self, path: str, access_token: str) -> str:
        return "https://mmbiz.qpic.cn/mock/video-cover.jpg"

    def upload_video_material(self, path: str, access_token: str, *, title: str, introduction: str) -> str:
        return "mock_video_media_id"

    def get_video_material(self, media_id: str, access_token: str) -> dict:
        self.calls.append(("get_video_material", media_id))
        return {"vid": "apiv_1234567890", "cover_url": ""}


def test_successful_video_upload_embeds_playable_iframe(tmp_path, monkeypatch) -> None:
    html = (
        '<figure class="md-video-card" data-video-token="tok_video" data-video-name="demo.mp4">'
        '<section class="md-video-card-poster">▶</section>'
        '<figcaption>视频：demo.mp4</figcaption>'
        '</figure>'
    )
    video_path = tmp_path / "demo.mp4"
    video_path.write_bytes(b"video-bytes")
    poster_path = tmp_path / "demo-cover.jpg"
    poster_path.write_bytes(b"poster-bytes")
    monkeypatch.setattr("wechat_draft_publisher.wechat_api._download_lark_media",
                        lambda token, output_dir, filename=None: video_path)
    monkeypatch.setattr("wechat_draft_publisher.wechat_api._extract_video_poster",
                        lambda video_path_arg, output_dir: poster_path)

    rewritten, materials = rewrite_html_assets(
        html=html, article_dir=tmp_path, client=_FakeClientWithVid(), access_token="t")

    assert 'class="rich_pages video_iframe"' in rewritten
    assert 'data-mpvid="apiv_1234567890"' in rewritten
    assert 'vid=apiv_1234567890' in rewritten
    assert 'md-video-card' not in rewritten
    assert materials[0]["vid"] == "apiv_1234567890"


def test_failed_video_upload_neutral_card_has_no_failure_wording(tmp_path, monkeypatch) -> None:
    html = (
        '<figure class="md-video-card" data-video-token="tok_bad" data-video-name="bad.mp4">'
        '<section class="md-video-card-poster">▶</section>'
        '</figure>'
    )

    def fail_download(token, output_dir, filename=None):
        raise RuntimeError("download failed")

    monkeypatch.setattr("wechat_draft_publisher.wechat_api._download_lark_media", fail_download)

    rewritten, materials = rewrite_html_assets(
        html=html, article_dir=tmp_path, client=_FakeClientWithVid(), access_token="t")

    assert 'md-video-card-fallback' in rewritten
    assert '同步失败' not in rewritten
    assert '暂不支持' not in rewritten
    assert materials == []


def test_grid_two_images_become_fixed_table() -> None:
    md = (
        '<grid cols="2">\n'
        '  <column width="49">\n'
        '    <figure class="md-figure" style="margin: 1.5em 8px;"><img src="lark-image://t1"/></figure>\n'
        '  </column>\n'
        '  <column width="50">\n'
        '    <figure class="md-figure" style="margin: 1.5em 8px;"><img src="lark-image://t2"/></figure>\n'
        '  </column>\n'
        '</grid>\n'
    )
    html = render_markdown(md, profile="doocs", theme="grace", font_size=15).html
    assert '<table' in html and 'table-layout:fixed' in html
    assert 'width:49%' in html and 'width:50%' in html
    assert '<grid' not in html and '<column' not in html
    assert html.count('<figure') == 2
    # figure margins normalize to 0 inside grid cells
    table_html = html[html.find('<table'):html.find('</table>')]
    assert 'margin: 1.5em 8px' not in table_html


def test_grid_text_and_image_become_fixed_table() -> None:
    md = (
        '<grid cols="2">\n'
        '  <column width="50">\n'
        '    左侧说明文字\n'
        '  </column>\n'
        '  <column width="50">\n'
        '    <figure class="md-figure" style="margin: 1.5em 8px;"><img src="lark-image://t3"/></figure>\n'
        '  </column>\n'
        '</grid>\n'
    )
    html = render_markdown(md, profile="doocs", theme="grace", font_size=15).html
    assert 'table-layout:fixed' in html
    assert '左侧说明文字' in html
    assert '<grid' not in html


def test_long_mac_code_block_gets_height_cap() -> None:
    long_code = "\n".join(f"echo line-{i}" for i in range(120))
    md = f"```bash\n{long_code}\n```\n"
    html = render_markdown(
        md, profile="doocs", theme="grace", code_theme="github",
        mac_code_block=True, code_line_numbers=False,
    ).html
    assert 'max-height: 480px' in html
    assert 'overflow-y: auto' in html
    assert 'border-radius: 0 0 8px 8px' in html
    assert 'border-radius: 8px 8px 0 0' in html  # fixed dots header
    # short blocks stay uncapped
    short = render_markdown(
        "```bash\necho hi\n```\n", profile="doocs", theme="grace",
        code_theme="github", mac_code_block=True, code_line_numbers=False).html
    assert 'max-height' not in short


def test_draft_payload_ends_with_two_blank_paragraphs() -> None:
    article = ArticleInput(title="t", author="a", digest=None, cover_image=None, content_markdown="hello")
    rendered = render_markdown("hello", profile="doocs", theme="grace", font_size=15)
    payload = build_draft_payload(article=article, rendered=rendered, thumb_media_id="T")
    content = payload["articles"][0]["content"]
    assert content.endswith('<p><br></p><p><br></p>')
    assert "content_source_url" not in payload["articles"][0]
