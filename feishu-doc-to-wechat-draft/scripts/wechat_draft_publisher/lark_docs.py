from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from .models import ArticleInput

_DOC_TOKEN_RE = re.compile(r"/(?:docx|wiki)/([a-zA-Z0-9]+)")
_TEXT_TAG_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", re.S)
_LARK_TABLE_RE = re.compile(r"<lark-table\b.*?</lark-table>", re.S)
_IMAGE_RE = re.compile(r'<image\b[^>]*token="([^"]+)"[^>]*>')
_QUOTE_RE = re.compile(r'<quote-container>(.*?)</quote-container>', re.S)
_WS_RE = re.compile(r"\s+")
# Match horizontal rules that could be mistaken for setext h2 underlines
# Matches: standalone --- on its own line, or --- preceded by text (to prevent setext h2)
_HR_RE = re.compile(r'(^|\n)(-{3,}|\*{3,}|_{3,})(\s*\n|$)', re.M)
_STRONG_NUMBERED_LINE_RE = re.compile(r'^\*\*(\d+)\.\s+(.+?)\*\*$')
_STANDALONE_STRONG_RE = re.compile(r'^\*\*[^\n]+\*\*$')


def extract_lark_doc_token(doc: str) -> str:
    text = doc.strip()
    if text.startswith("http://") or text.startswith("https://"):
        match = _DOC_TOKEN_RE.search(text)
        if not match:
            raise ValueError(f"unsupported Lark doc URL: {doc}")
        return match.group(1)
    return text


def fetch_lark_doc(doc: str, *, identity: str = "user") -> dict:
    completed = subprocess.run(
        ["lark-cli", "docs", "+fetch", "--as", identity, "--doc", doc, "--format", "json"],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "failed to fetch Lark doc")

    payload = json.loads(completed.stdout)
    data = payload.get("data") or {}
    return {
        "doc_id": data.get("doc_id") or extract_lark_doc_token(doc),
        "title": data.get("title", ""),
        "markdown": data.get("markdown", ""),
        "source_url": doc if doc.startswith(("http://", "https://")) else None,
        "raw": payload,
    }


def _collapse_ws(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _convert_text_tags(markdown: str) -> str:
    return _TEXT_TAG_RE.sub(lambda m: _collapse_ws(m.group(1)), markdown)


def _extract_image_tokens(markdown: str) -> list[str]:
    """Extract all image tokens from markdown for later processing."""
    return _IMAGE_RE.findall(markdown)


def _convert_image_tags(markdown: str) -> str:
    """Convert <image token="..."> to placeholder markdown images.
    
    Note: These are placeholders. Actual image URLs need to be fetched via
    Lark API and uploaded to WeChat separately.
    """
    def replace_image(match):
        token = match.group(1)
        # Return a placeholder that will be processed later
        return f"![image](lark-image://{token})"
    return _IMAGE_RE.sub(replace_image, markdown)


def _convert_quote_containers(markdown: str) -> str:
    """Convert <quote-container>...</quote-container> to markdown blockquotes."""
    def replace_quote(match):
        content = match.group(1).strip()
        # Convert each line to a blockquote line
        lines = content.split('\n')
        quoted_lines = [f"> {line}" if line.strip() else ">" for line in lines]
        return '\n'.join(quoted_lines)
    return _QUOTE_RE.sub(replace_quote, markdown)


def _convert_lark_table(table_markup: str) -> str:
    root = ET.fromstring(f"<root>{table_markup}</root>")
    table = root.find("lark-table")
    if table is None:
        return table_markup

    rows: list[list[str]] = []
    for tr in table.findall("lark-tr"):
        cells = []
        for td in tr.findall("lark-td"):
            cells.append(_collapse_ws("".join(td.itertext())))
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    width = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (width - len(row)) for row in rows]

    def escape_cell(text: str) -> str:
        return text.replace("|", "\\|")

    lines = ["| " + " | ".join(escape_cell(cell) for cell in normalized_rows[0]) + " |"]
    lines.append("| " + " | ".join(["---"] * width) + " |")
    for row in normalized_rows[1:]:
        lines.append("| " + " | ".join(escape_cell(cell) for cell in row) + " |")
    return "\n".join(lines)


def _convert_horizontal_rules(markdown: str) -> str:
    """Convert ---/___/*** horizontal rules to HTML <hr> to avoid setext h2 confusion."""
    def replace_hr(match):
        return f"\n\n<hr />\n\n"
    return _HR_RE.sub(replace_hr, markdown)


def _convert_strong_numbered_blocks(markdown: str) -> str:
    """Convert Feishu's line-broken numbered highlights into real ordered lists.

    Example input:
      简单说，它解决三个核心问题：
      **1. 图片自动处理**
      飞书文档里的图片会自动下载...
      **2. 格式完整保留**
      表格、引用块...

    becomes:
      简单说，它解决三个核心问题：

      1. **图片自动处理** 飞书文档里的图片会自动下载...
      2. **格式完整保留** 表格、引用块...
    """
    lines = markdown.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = _STRONG_NUMBERED_LINE_RE.match(line.strip())
        if not match:
            out.append(line)
            i += 1
            continue

        start_i = i
        items: list[tuple[int, str, str]] = []
        while i < len(lines):
            current = lines[i].strip()
            current_match = _STRONG_NUMBERED_LINE_RE.match(current)
            if not current_match:
                break
            number = int(current_match.group(1))
            label = current_match.group(2).strip()
            i += 1

            body_lines: list[str] = []
            while i < len(lines):
                candidate = lines[i]
                stripped = candidate.strip()
                if not stripped:
                    break
                if _STRONG_NUMBERED_LINE_RE.match(stripped):
                    break
                if stripped.startswith(("#", "- ", "* ", "> ", "```", "<hr")):
                    break
                body_lines.append(stripped)
                i += 1

            body = _collapse_ws(" ".join(body_lines))
            if not body:
                i = start_i
                items = []
                break
            items.append((number, label, body))

        if items:
            if out and out[-1].strip():
                out.append("")
            for number, label, body in items:
                out.append(f"{number}. **{label}** {body}")
            if i < len(lines) and lines[i].strip():
                out.append("")
            continue

        out.append(line)
        i += 1

    return "\n".join(out)


def _normalize_block_boundaries(markdown: str) -> str:
    """Insert missing blank lines around standalone strong titles and list boundaries."""
    lines = markdown.replace("\r\n", "\n").split("\n")
    out: list[str] = []

    def prev_nonempty() -> str | None:
        for item in reversed(out):
            if item.strip():
                return item.strip()
        return None

    for i, line in enumerate(lines):
        stripped = line.strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        prev = prev_nonempty() or ""

        if stripped and _STANDALONE_STRONG_RE.match(stripped):
            if out and out[-1].strip():
                out.append("")
            out.append(line)
            if nxt and not nxt.startswith("```"):
                out.append("")
            continue

        if stripped and not stripped.startswith(("- ", "* ", "```", ">", "#", "<hr")) and not re.match(r'^\d+\.\s', stripped):
            if prev.startswith(("-", "*")) or re.match(r'^\d+\.', prev):
                if out and out[-1] != "":
                    out.append("")

        out.append(line)

    return "\n".join(out)


def normalize_lark_markdown(markdown: str) -> str:
    normalized = _convert_text_tags(markdown)
    normalized = _convert_quote_containers(normalized)
    normalized = _convert_image_tags(normalized)
    normalized = _LARK_TABLE_RE.sub(lambda m: _convert_lark_table(m.group(0)), normalized)
    normalized = _convert_horizontal_rules(normalized)
    normalized = _convert_strong_numbered_blocks(normalized)
    normalized = _normalize_block_boundaries(normalized)
    normalized = normalized.replace("\r\n", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip() + "\n"


def build_digest_from_markdown(markdown: str, limit: int = 120) -> str:
    text = markdown
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\(([^)]+)\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"^>+\s*", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.M)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _collapse_ws(text)
    return text[:limit]


def load_lark_doc_article(
    doc: str,
    *,
    author: str,
    digest: str | None = None,
    cover_image: str | None = None,
    source_url: str | None = None,
    identity: str = "user",
) -> tuple[ArticleInput, dict]:
    doc_data = fetch_lark_doc(doc, identity=identity)
    markdown = normalize_lark_markdown(doc_data["markdown"])
    article = ArticleInput(
        title=doc_data["title"],
        author=author,
        digest=digest or build_digest_from_markdown(markdown),
        cover_image=cover_image,
        content_markdown=markdown,
        source_url=source_url or doc_data.get("source_url"),
    )
    return article, doc_data
