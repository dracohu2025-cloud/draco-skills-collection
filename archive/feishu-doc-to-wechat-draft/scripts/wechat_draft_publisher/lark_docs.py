from __future__ import annotations

import json
import html as html_lib
import re
import subprocess
from urllib.parse import urlparse

from .models import ArticleInput

_DOC_TOKEN_RE = re.compile(r"/(?:docx|wiki)/([a-zA-Z0-9]+)")
_TEXT_TAG_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", re.S)
_MENTION_DOC_RE = re.compile(r"<mention-doc\b[^>]*>(.*?)</mention-doc>", re.S)
_LARK_TABLE_RE = re.compile(r"<lark-table\b.*?</lark-table>", re.S)
_LARK_TR_RE = re.compile(r"<lark-tr\b[^>]*>(.*?)</lark-tr>", re.S)
_LARK_TD_RE = re.compile(r"<lark-td\b[^>]*>(.*?)</lark-td>", re.S)
_IMAGE_RE = re.compile(r'<image\b[^>]*token="([^"]+)"[^>]*>')
_QUOTE_RE = re.compile(r'<quote-container>(.*?)</quote-container>', re.S)
_VIDEO_VIEW_RE = re.compile(
    r'<view\b[^>]*type="2"[^>]*>\s*'
    r'<file\b(?=[^>]*token="(?P<token>[^"]+)")(?=[^>]*name="(?P<name>[^"]+)")[^>]*'
    r'(?:/>|>\s*</file>)\s*'
    r'</view>',
    re.S,
)
_WS_RE = re.compile(r"\s+")
# Match horizontal rules that could be mistaken for setext h2 underlines
# Matches: standalone --- on its own line, or --- preceded by text (to prevent setext h2)
_HR_RE = re.compile(r'(^|\n)(-{3,}|\*{3,}|_{3,})(\s*\n|$)', re.M)
_STRONG_NUMBERED_LINE_RE = re.compile(r'^\*\*(\d+)\.\s+(.+?)\*\*$')
_STANDALONE_STRONG_RE = re.compile(r'^\*\*[^\n]+\*\*$')
_ORDERED_LINE_RE = re.compile(r'^(?P<indent>\s*)(?P<num>\d+)\.\s+(?P<body>.+)$')


def extract_lark_doc_token(doc: str) -> str:
    text = doc.strip()
    if text.startswith("http://") or text.startswith("https://"):
        match = _DOC_TOKEN_RE.search(text)
        if not match:
            raise ValueError(f"unsupported Lark doc URL: {doc}")
        return match.group(1)
    return text


def _extract_image_captions(payload: dict) -> dict[str, str]:
    captions: dict[str, str] = {}
    for block in (payload.get("data") or {}).get("items") or []:
        if block.get("block_type") != 27:
            continue
        image = block.get("image") or {}
        token = (image.get("token") or "").strip()
        content = ((image.get("caption") or {}).get("content") or "").strip()
        if token and content:
            captions[token] = content
    return captions


def fetch_lark_image_captions(doc_id: str, *, identity: str = "user") -> dict[str, str]:
    captions: dict[str, str] = {}
    page_token: str | None = None
    while True:
        params: dict[str, object] = {"document_revision_id": -1, "page_size": 500}
        if page_token:
            params["page_token"] = page_token
        completed = subprocess.run(
            [
                "lark-cli",
                "api",
                "GET",
                f"/open-apis/docx/v1/documents/{doc_id}/blocks",
                "--as",
                identity,
                "--params",
                json.dumps(params, separators=(",", ":")),
            ],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                completed.stderr.strip()
                or completed.stdout.strip()
                or "failed to fetch Lark image captions"
            )
        payload = json.loads(completed.stdout)
        if payload.get("code") not in (None, 0):
            raise RuntimeError(payload.get("msg") or "failed to fetch Lark image captions")
        captions.update(_extract_image_captions(payload))
        data = payload.get("data") or {}
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
        if not page_token:
            raise RuntimeError("Lark block pagination indicated more data without page_token")
    return captions


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
    doc_id = data.get("doc_id") or extract_lark_doc_token(doc)
    return {
        "doc_id": doc_id,
        "title": data.get("title", ""),
        "markdown": data.get("markdown", ""),
        "image_captions": fetch_lark_image_captions(doc_id, identity=identity),
        "source_url": doc if doc.startswith(("http://", "https://")) else None,
        "raw": payload,
    }


def _collapse_ws(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _convert_text_tags(markdown: str) -> str:
    return _TEXT_TAG_RE.sub(lambda m: _collapse_ws(m.group(1)), markdown)


def _convert_mention_doc_tags(markdown: str) -> str:
    """Convert Feishu document mentions to their visible title text."""
    return _MENTION_DOC_RE.sub(lambda m: _collapse_ws(m.group(1)), markdown)


def _extract_image_tokens(markdown: str) -> list[str]:
    """Extract all image tokens from markdown for later processing."""
    return _IMAGE_RE.findall(markdown)


def _convert_image_tags(markdown: str, image_captions: dict[str, str] | None = None) -> str:
    """Convert <image token="..."> to placeholder markdown images.
    
    Note: These are placeholders. Actual image URLs need to be fetched via
    Lark API and uploaded to WeChat separately.
    """
    def replace_image(match):
        token = match.group(1)
        alt = (image_captions or {}).get(token) or "image"
        # Return a placeholder that will be processed later
        return f"![{alt}](lark-image://{token})"
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


def _convert_embedded_videos(markdown: str) -> str:
    """Convert Feishu video/file embeds into explicit placeholder tags."""

    def replace_video(match: re.Match[str]) -> str:
        token = match.group("token").strip()
        name = match.group("name").strip()
        if not name.lower().endswith(".mp4"):
            return match.group(0)
        return (
            f'<wechat-video token="{html_lib.escape(token, quote=True)}" '
            f'name="{html_lib.escape(name, quote=True)}" />'
        )

    return _VIDEO_VIEW_RE.sub(replace_video, markdown)


def _convert_lark_table(table_markup: str) -> str:
    rows: list[list[str]] = []
    for tr_match in _LARK_TR_RE.finditer(table_markup):
        cells = []
        for td_match in _LARK_TD_RE.finditer(tr_match.group(1)):
            cell_markup = td_match.group(1)
            # Do not parse the cell as XML: command docs often contain literal
            # placeholders like `<model>` / `<name>` inside code spans.
            cells.append(_collapse_ws(cell_markup))
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

    Preserve following block structure inside the numbered item until the next
    numbered strong heading, while stopping before standalone strong subheadings
    like "方法一：..." so they can remain separate top-level blocks.
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

        if out and out[-1].strip():
            out.append("")

        while i < len(lines):
            current = lines[i].strip()
            current_match = _STRONG_NUMBERED_LINE_RE.match(current)
            if not current_match:
                break

            number = int(current_match.group(1))
            label = current_match.group(2).strip()
            out.append(f"{number}. **{label}**")
            i += 1

            block_lines: list[str] = []
            while i < len(lines):
                candidate = lines[i]
                stripped = candidate.strip()
                if _STRONG_NUMBERED_LINE_RE.match(stripped):
                    break
                if stripped and _STANDALONE_STRONG_RE.match(stripped):
                    break
                if stripped.startswith(("#", "<hr")):
                    break
                block_lines.append(candidate)
                i += 1

            while block_lines and not block_lines[0].strip():
                block_lines.pop(0)
            while block_lines and not block_lines[-1].strip():
                block_lines.pop()

            if block_lines:
                out.append("")
                for block_line in block_lines:
                    out.append(f"   {block_line}" if block_line else "")
                out.append("")

            while i < len(lines) and not lines[i].strip():
                i += 1

        if out and out[-1] == "":
            out.pop()
        if i < len(lines) and lines[i].strip():
            out.append("")

    return "\n".join(out)


def _renumber_lark_lazy_ordered_lists(markdown: str) -> str:
    """Turn Feishu/Lark's repeated `1.` ordered-list export into real numbers.

    Lark often serializes every ordered item as `1.`. Markdown treats separated
    items (screenshots, quotes) as new lists, so WeChat preview becomes all `1.`.
    Keep counters alive across media/quote/blank/prose helper blocks; reset only
    on hard section boundaries such as headings, horizontal rules, or standalone
    strong section titles.
    """
    lines = markdown.replace("\r\n", "\n").split("\n")
    counters: dict[int, int] = {}
    out: list[str] = []
    in_fence = False

    def reset_from(indent: int) -> None:
        for level in list(counters):
            if level >= indent:
                counters.pop(level, None)

    def reset_all() -> None:
        counters.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue

        match = _ORDERED_LINE_RE.match(line)
        if match:
            indent_text = match.group("indent")
            indent = len(indent_text.replace("\t", "    "))
            current = int(match.group("num"))
            for level in list(counters):
                if level > indent:
                    counters.pop(level, None)
            if current != 1 or indent not in counters:
                counters[indent] = current
            else:
                counters[indent] += 1
            output_indent = indent_text if indent == 0 else " " * max(indent, 4)
            out.append(f'{output_indent}{counters[indent]}. {match.group("body")}')
            continue

        if not stripped:
            out.append(line)
            continue
        if stripped.startswith(("#", "<hr")):
            reset_all()
            out.append(line)
            continue
        if stripped and _STANDALONE_STRONG_RE.match(stripped):
            reset_all()
            out.append(line)
            continue
        if stripped.startswith(("![", "<figure", "<img", ">", "<blockquote", "<wechat-video", "- ", "* ")):
            out.append(line)
            continue

        # Feishu often exports a visual ordered list as loose blocks:
        # `1. item` + quote/image/prose + `1. next item`.  Do not reset the
        # counter on ordinary prose; only hard section boundaries reset it.
        out.append(line)

    return "\n".join(out)


def _unwrap_markdown_fences_with_inner_fences(markdown: str) -> str:
    """Unwrap Lark-exported ```markdown blocks that contain real fences.

    These blocks are usually pasted AI output. Keeping the outer markdown fence
    makes screenshots after the block easy to escape as code when nested fences
    are present. Unwrapping preserves the inner bash/plaintext fences.
    """
    lines = markdown.replace("\r\n", "\n").split("\n")
    remove: set[int] = set()
    i = 0
    while i < len(lines):
        if lines[i].strip().lower() != "```markdown":
            i += 1
            continue
        candidate_close = None
        saw_inner_fence = False
        j = i + 1
        while j < len(lines):
            stripped = lines[j].strip()
            if stripped.startswith("```"):
                if stripped != "```":
                    saw_inner_fence = True
                else:
                    next_nonempty = ""
                    for line in lines[j + 1 :]:
                        if line.strip():
                            next_nonempty = line.strip()
                            break
                    if next_nonempty.startswith(("<hr", "---", "#", "- ", "* ", "![", "<image", "<quote-container")):
                        candidate_close = j
                        break
            j += 1
        if candidate_close is not None and saw_inner_fence:
            remove.add(i)
            remove.add(candidate_close)
            i = candidate_close + 1
        else:
            i += 1
    if not remove:
        return markdown
    return "\n".join(line for idx, line in enumerate(lines) if idx not in remove)


def _remove_orphan_fence_before_block_boundary(markdown: str) -> str:
    """Drop a lone ``` that would incorrectly swallow the rest of the doc.

    Lark sometimes exports an extra standalone fence after prose such as an
    official docs URL. If that fence is followed by a section boundary and has
    no closing peer, markdown-it treats all later screenshots as code text.
    """
    lines = markdown.replace("\r\n", "\n").split("\n")
    fence_indices = [i for i, line in enumerate(lines) if line.strip() == "```"]
    if len(fence_indices) % 2 == 0:
        return markdown

    for idx in reversed(fence_indices):
        next_nonempty = ""
        for line in lines[idx + 1 :]:
            if line.strip():
                next_nonempty = line.strip()
                break
        if next_nonempty.startswith(("<hr", "#", "- ", "* ", "![", "<image", "<quote-container")):
            del lines[idx]
            return "\n".join(lines)
    return markdown


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


def normalize_lark_markdown(markdown: str, *, image_captions: dict[str, str] | None = None) -> str:
    normalized = _unwrap_markdown_fences_with_inner_fences(markdown)
    normalized = _convert_text_tags(normalized)
    normalized = _convert_mention_doc_tags(normalized)
    normalized = _convert_quote_containers(normalized)
    normalized = _convert_image_tags(normalized, image_captions=image_captions)
    normalized = _convert_embedded_videos(normalized)
    normalized = _LARK_TABLE_RE.sub(lambda m: _convert_lark_table(m.group(0)), normalized)
    normalized = _convert_horizontal_rules(normalized)
    normalized = _convert_strong_numbered_blocks(normalized)
    normalized = _renumber_lark_lazy_ordered_lists(normalized)
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
    markdown = normalize_lark_markdown(
        doc_data["markdown"],
        image_captions=doc_data.get("image_captions") or {},
    )
    article = ArticleInput(
        title=doc_data["title"],
        author=author,
        digest=digest or build_digest_from_markdown(markdown),
        cover_image=cover_image,
        content_markdown=markdown,
        source_url=source_url,  # explicit only; never default to the Feishu doc URL
    )
    return article, doc_data
