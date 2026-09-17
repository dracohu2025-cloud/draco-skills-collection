from __future__ import annotations

from pathlib import Path

from .models import ArticleInput, RenderResult

TITLE_MAX_LENGTH = 64
AUTHOR_MAX_LENGTH = 16
DIGEST_MAX_LENGTH = 120


def validate_article_for_draft(*, article: ArticleInput, rendered: RenderResult, thumb_media_id: str) -> None:
    title = (article.title or "").strip()
    if not title:
        raise ValueError("title is required")
    if len(title) > TITLE_MAX_LENGTH:
        raise ValueError(f"title is too long: max {TITLE_MAX_LENGTH} chars")

    author = (article.author or "").strip()
    if author and len(author) > AUTHOR_MAX_LENGTH:
        raise ValueError(f"author is too long: max {AUTHOR_MAX_LENGTH} chars")

    digest = (article.digest or rendered.plain_digest or "").strip()
    if len(digest) > DIGEST_MAX_LENGTH:
        raise ValueError(f"digest is too long: max {DIGEST_MAX_LENGTH} chars")

    if not thumb_media_id.strip():
        raise ValueError("thumb_media_id is required")



def validate_publish_inputs(*, article: ArticleInput, article_dir: Path, thumb_media_id: str | None) -> None:
    if thumb_media_id:
        return
    if not article.cover_image:
        if "!" in (article.content_markdown or "") and "](" in (article.content_markdown or ""):
            return
        raise ValueError("cover_image, thumb_media_id, or first article image is required for publish")
    cover_path = (article_dir / article.cover_image).resolve()
    if not cover_path.exists():
        raise FileNotFoundError(str(cover_path))
