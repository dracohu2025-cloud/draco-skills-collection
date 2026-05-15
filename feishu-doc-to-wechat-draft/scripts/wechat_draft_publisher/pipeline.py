from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .draft import build_draft_payload
from .lark_docs import load_lark_doc_article
from .loader import load_article
from .renderer import render_markdown
from .validation import validate_publish_inputs
from .wechat_api import _download_lark_image, rewrite_html_assets

_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")


def build_draft_from_markdown_file(
    path: str,
    thumb_media_id: str,
    *,
    profile: str | None = None,
    theme: str | None = None,
    primary_color: str | None = None,
    font_family: str | None = None,
    font_size: int | None = None,
    line_height: float | None = None,
    justify: bool | None = None,
    indent_first_line: bool | None = None,
    code_theme: str | None = None,
    hr_style: str | None = None,
    heading_style: str | None = None,
    heading_styles: dict[str, str] | None = None,
    mac_code_block: bool | None = None,
    code_line_numbers: bool | None = None,
    caption_mode: str | None = None,
    footnote_links: bool | None = None,
) -> dict:
    article = load_article(path)
    rendered = render_markdown(
        article.content_markdown,
        profile=profile,
        theme=theme,
        primary_color=primary_color,
        font_family=font_family,
        font_size=font_size,
        line_height=line_height,
        justify=justify,
        indent_first_line=indent_first_line,
        code_theme=code_theme,
        hr_style=hr_style,
        heading_style=heading_style,
        heading_styles=heading_styles,
        mac_code_block=mac_code_block,
        code_line_numbers=code_line_numbers,
        caption_mode=caption_mode,
        footnote_links=footnote_links,
    )
    payload = build_draft_payload(article=article, rendered=rendered, thumb_media_id=thumb_media_id)
    return {
        "article": article,
        "rendered": rendered,
        "payload": payload,
    }


def _render_article(article, *, profile=None, theme=None, primary_color=None, font_family=None, font_size=None, line_height=None, justify=None, indent_first_line=None, code_theme=None, hr_style=None, heading_style=None, heading_styles=None, mac_code_block=None, code_line_numbers=None, caption_mode=None, footnote_links=None):
    return render_markdown(
        article.content_markdown,
        profile=profile,
        theme=theme,
        primary_color=primary_color,
        font_family=font_family,
        font_size=font_size,
        line_height=line_height,
        justify=justify,
        indent_first_line=indent_first_line,
        code_theme=code_theme,
        hr_style=hr_style,
        heading_style=heading_style,
        heading_styles=heading_styles,
        mac_code_block=mac_code_block,
        code_line_numbers=code_line_numbers,
        caption_mode=caption_mode,
        footnote_links=footnote_links,
    )


def _first_markdown_image_src(markdown: str) -> str | None:
    match = _MARKDOWN_IMAGE_RE.search(markdown or "")
    if not match:
        return None
    return match.group(1).strip().strip("<>").strip('"\'')


def _download_remote_cover_image(src: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(src)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
        suffix = ".jpg"
    output_path = output_dir / f"wechat_default_cover{suffix}"
    request = Request(src, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        output_path.write_bytes(response.read())
    return output_path


def _resolve_cover_image_path(article, article_dir: Path) -> Path:
    if article.cover_image:
        return (article_dir / article.cover_image).resolve()

    src = _first_markdown_image_src(article.content_markdown)
    if not src:
        raise ValueError("cover_image, thumb_media_id, or first article image is required for publish")

    if src.startswith("lark-image://"):
        return _download_lark_image(src.replace("lark-image://", "", 1), article_dir)
    if src.startswith("http://") or src.startswith("https://"):
        return _download_remote_cover_image(src, article_dir)
    return (article_dir / src).resolve()


def _finalize_publish(article, rendered, *, article_dir: Path, client, dry_run: bool, thumb_media_id: str | None) -> dict:
    if dry_run:
        if not thumb_media_id:
            raise ValueError("thumb_media_id is required in dry-run mode")
        payload = build_draft_payload(article=article, rendered=rendered, thumb_media_id=thumb_media_id)
        return {
            "article": article,
            "rendered": rendered,
            "payload": payload,
            "draft_media_id": None,
            "video_materials": [],
        }

    validate_publish_inputs(article=article, article_dir=article_dir, thumb_media_id=thumb_media_id)
    access_token = client.get_access_token()
    rendered_html, video_materials = rewrite_html_assets(
        html=rendered.html,
        article_dir=article_dir,
        client=client,
        access_token=access_token,
        source_url=article.source_url,
    )
    rendered = type(rendered)(
        html=rendered_html,
        plain_digest=rendered.plain_digest,
        used_images=rendered.used_images,
    )

    resolved_thumb_media_id = thumb_media_id
    if not resolved_thumb_media_id:
        cover_path = _resolve_cover_image_path(article, article_dir)
        resolved_thumb_media_id = client.upload_cover_image(str(cover_path), access_token)

    payload = build_draft_payload(article=article, rendered=rendered, thumb_media_id=resolved_thumb_media_id)
    draft_media_id = client.add_draft(payload, access_token)
    return {
        "article": article,
        "rendered": rendered,
        "payload": payload,
        "draft_media_id": draft_media_id,
        "video_materials": video_materials,
    }


def publish_markdown_file(
    path: str,
    *,
    client,
    dry_run: bool = False,
    thumb_media_id: str | None = None,
    profile: str | None = None,
    theme: str | None = None,
    primary_color: str | None = None,
    font_family: str | None = None,
    font_size: int | None = None,
    line_height: float | None = None,
    justify: bool | None = None,
    indent_first_line: bool | None = None,
    code_theme: str | None = None,
    hr_style: str | None = None,
    heading_style: str | None = None,
    heading_styles: dict[str, str] | None = None,
    mac_code_block: bool | None = None,
    code_line_numbers: bool | None = None,
    caption_mode: str | None = None,
    footnote_links: bool | None = None,
) -> dict:
    article = load_article(path)
    rendered = _render_article(
        article,
        profile=profile,
        theme=theme,
        primary_color=primary_color,
        font_family=font_family,
        font_size=font_size,
        line_height=line_height,
        justify=justify,
        indent_first_line=indent_first_line,
        code_theme=code_theme,
        hr_style=hr_style,
        heading_style=heading_style,
        heading_styles=heading_styles,
        mac_code_block=mac_code_block,
        code_line_numbers=code_line_numbers,
        caption_mode=caption_mode,
        footnote_links=footnote_links,
    )
    article_dir = Path(path).resolve().parent
    return _finalize_publish(
        article,
        rendered,
        article_dir=article_dir,
        client=client,
        dry_run=dry_run,
        thumb_media_id=thumb_media_id,
    )


def build_draft_from_lark_doc(
    doc: str,
    thumb_media_id: str,
    *,
    author: str,
    digest: str | None = None,
    cover_image: str | None = None,
    source_url: str | None = None,
    identity: str = "user",
    profile: str | None = None,
    theme: str | None = None,
    primary_color: str | None = None,
    font_family: str | None = None,
    font_size: int | None = None,
    line_height: float | None = None,
    justify: bool | None = None,
    indent_first_line: bool | None = None,
    code_theme: str | None = None,
    hr_style: str | None = None,
    heading_style: str | None = None,
    heading_styles: dict[str, str] | None = None,
    mac_code_block: bool | None = None,
    code_line_numbers: bool | None = None,
    caption_mode: str | None = None,
    footnote_links: bool | None = None,
) -> dict:
    article, doc_meta = load_lark_doc_article(
        doc,
        author=author,
        digest=digest,
        cover_image=cover_image,
        source_url=source_url,
        identity=identity,
    )
    rendered = _render_article(
        article,
        profile=profile,
        theme=theme,
        primary_color=primary_color,
        font_family=font_family,
        font_size=font_size,
        line_height=line_height,
        justify=justify,
        indent_first_line=indent_first_line,
        code_theme=code_theme,
        hr_style=hr_style,
        heading_style=heading_style,
        heading_styles=heading_styles,
        mac_code_block=mac_code_block,
        code_line_numbers=code_line_numbers,
        caption_mode=caption_mode,
        footnote_links=footnote_links,
    )
    payload = build_draft_payload(article=article, rendered=rendered, thumb_media_id=thumb_media_id)
    return {"article": article, "rendered": rendered, "payload": payload, "doc": doc_meta}


def publish_lark_doc(
    doc: str,
    *,
    author: str,
    client,
    dry_run: bool = False,
    thumb_media_id: str | None = None,
    cover_image: str | None = None,
    digest: str | None = None,
    source_url: str | None = None,
    identity: str = "user",
    assets_dir: str | None = None,
    profile: str | None = None,
    theme: str | None = None,
    primary_color: str | None = None,
    font_family: str | None = None,
    font_size: int | None = None,
    line_height: float | None = None,
    justify: bool | None = None,
    indent_first_line: bool | None = None,
    code_theme: str | None = None,
    hr_style: str | None = None,
    heading_style: str | None = None,
    heading_styles: dict[str, str] | None = None,
    mac_code_block: bool | None = None,
    code_line_numbers: bool | None = None,
    caption_mode: str | None = None,
    footnote_links: bool | None = None,
) -> dict:
    article, doc_meta = load_lark_doc_article(
        doc,
        author=author,
        digest=digest,
        cover_image=cover_image,
        source_url=source_url,
        identity=identity,
    )
    rendered = _render_article(
        article,
        profile=profile,
        theme=theme,
        primary_color=primary_color,
        font_family=font_family,
        font_size=font_size,
        line_height=line_height,
        justify=justify,
        indent_first_line=indent_first_line,
        code_theme=code_theme,
        hr_style=hr_style,
        heading_style=heading_style,
        heading_styles=heading_styles,
        mac_code_block=mac_code_block,
        code_line_numbers=code_line_numbers,
        caption_mode=caption_mode,
        footnote_links=footnote_links,
    )
    article_dir = Path(assets_dir or ".").resolve()
    result = _finalize_publish(
        article,
        rendered,
        article_dir=article_dir,
        client=client,
        dry_run=dry_run,
        thumb_media_id=thumb_media_id,
    )
    result["doc"] = doc_meta
    return result
