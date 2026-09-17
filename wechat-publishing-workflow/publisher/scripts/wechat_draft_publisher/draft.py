from .models import ArticleInput, RenderResult
from .validation import validate_article_for_draft


def build_draft_payload(*, article: ArticleInput, rendered: RenderResult, thumb_media_id: str) -> dict:
    validate_article_for_draft(article=article, rendered=rendered, thumb_media_id=thumb_media_id)
    digest = article.digest or rendered.plain_digest
    content = rendered.html
    # Every draft ends with two trailing blank paragraphs so the last content
    # block is not glued to the editor bottom / 阅读原文 area (user rule).
    if not content.rstrip().endswith('<p><br></p><p><br></p>'):
        content = content + '<p><br></p><p><br></p>'
    payload = {
        "articles": [
            {
                "title": article.title,
                "author": article.author,
                "digest": digest,
                "content": content,
                "thumb_media_id": thumb_media_id,
            }
        ]
    }
    if article.source_url:
        payload["articles"][0]["content_source_url"] = article.source_url
    return payload
