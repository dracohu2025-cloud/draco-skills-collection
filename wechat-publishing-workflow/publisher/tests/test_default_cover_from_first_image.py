from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from wechat_draft_publisher import pipeline
from wechat_draft_publisher.models import ArticleInput, RenderResult


class FakeWechatClient:
    def __init__(self) -> None:
        self.cover_paths: list[str] = []

    def get_access_token(self) -> str:
        return "token"

    def upload_cover_image(self, path: str, access_token: str) -> str:
        self.cover_paths.append(path)
        assert access_token == "token"
        return "thumb_from_first_image"

    def add_draft(self, payload: dict, access_token: str) -> str:
        assert payload["articles"][0]["thumb_media_id"] == "thumb_from_first_image"
        return "draft_media_id"


def test_publish_uses_first_lark_image_as_default_cover(tmp_path: Path, monkeypatch) -> None:
    first_image = tmp_path / "first.jpg"
    first_image.write_bytes(b"fake-image")

    def fake_download_lark_image(token: str, article_dir: Path) -> Path:
        assert token == "img_token_123"
        assert article_dir == tmp_path.resolve()
        return first_image

    monkeypatch.setattr(pipeline, "_download_lark_image", fake_download_lark_image)

    article = ArticleInput(
        title="测试文章",
        author="Draco",
        digest="摘要",
        cover_image=None,
        content_markdown="开头\n\n![hero](lark-image://img_token_123)\n\n正文",
        source_url=None,
    )
    rendered = RenderResult(html="<section>正文</section>", plain_digest="摘要", used_images=[])
    client = FakeWechatClient()

    result = pipeline._finalize_publish(
        article,
        rendered,
        article_dir=tmp_path.resolve(),
        client=client,
        dry_run=False,
        thumb_media_id=None,
    )

    assert result["draft_media_id"] == "draft_media_id"
    assert client.cover_paths == [str(first_image)]


def test_explicit_cover_still_wins_over_first_image(tmp_path: Path, monkeypatch) -> None:
    explicit_cover = tmp_path / "cover.jpg"
    explicit_cover.write_bytes(b"cover")
    monkeypatch.setattr(pipeline, "_download_lark_image", lambda *_: (_ for _ in ()).throw(AssertionError("should not download lark image")))

    article = ArticleInput(
        title="测试文章",
        author="Draco",
        digest="摘要",
        cover_image="cover.jpg",
        content_markdown="![hero](lark-image://img_token_123)",
        source_url=None,
    )
    rendered = RenderResult(html="<section>正文</section>", plain_digest="摘要", used_images=[])
    client = FakeWechatClient()

    pipeline._finalize_publish(
        article,
        rendered,
        article_dir=tmp_path.resolve(),
        client=client,
        dry_run=False,
        thumb_media_id=None,
    )

    assert client.cover_paths == [str(explicit_cover.resolve())]
