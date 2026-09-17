from pathlib import Path

import yaml

from .models import ArticleInput


FRONTMATTER_DELIMITER = "---"


def load_article(path: str) -> ArticleInput:
    raw = Path(path).read_text()
    metadata: dict = {}
    body = raw

    if raw.startswith(f"{FRONTMATTER_DELIMITER}\n"):
        _, frontmatter, body = raw.split(FRONTMATTER_DELIMITER, 2)
        metadata = yaml.safe_load(frontmatter) or {}
        body = body.lstrip("\n")

    return ArticleInput(
        title=metadata.get("title", ""),
        author=metadata.get("author", ""),
        digest=metadata.get("digest", ""),
        cover_image=metadata.get("cover_image"),
        content_markdown=body,
        source_url=metadata.get("source_url"),
    )
