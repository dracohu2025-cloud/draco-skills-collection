from dataclasses import dataclass


@dataclass(slots=True)
class ArticleInput:
    title: str
    author: str
    digest: str
    cover_image: str | None
    content_markdown: str
    source_url: str | None = None


@dataclass(slots=True)
class RenderResult:
    html: str
    plain_digest: str
    used_images: list[str]
