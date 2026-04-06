from __future__ import annotations

import html as html_lib
import re

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

from .models import RenderResult
from .rendering import RenderOptions, build_css_vars, css_var_style, resolve_render_options

_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_TAG_RE = re.compile(r"<[^>]+>")
_P_RE = re.compile(r"<p(?:\s+[^>]*)?>(.*?)</p>", re.S)
_WS_RE = re.compile(r"\s+")
_CALLOUT_BLOCK_RE = re.compile(r"(?m)^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION|INFO)\]\n((?:>.*\n?)*)")
_LINK_RE = re.compile(r'<a class="md-link"[^>]* href="([^"]+)"[^>]*>(.*?)</a>')
_IMAGE_WITH_TITLE_RE = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)(?:\s+"(?P<title>[^"]*)")?\)')


_MAC_CODE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" x="0px" y="0px" width="45px" height="13px" '
    'viewBox="0 0 450 130">'
    '<ellipse cx="50" cy="65" rx="50" ry="52" stroke="rgb(220,60,54)" stroke-width="2" fill="rgb(237,108,96)" />'
    '<ellipse cx="225" cy="65" rx="50" ry="52" stroke="rgb(218,151,33)" stroke-width="2" fill="rgb(247,193,81)" />'
    '<ellipse cx="400" cy="65" rx="50" ry="52" stroke="rgb(27,161,37)" stroke-width="2" fill="rgb(100,200,86)" />'
    '</svg>'
)


class WechatRenderer:
    def __init__(self, options: RenderOptions | None = None) -> None:
        self._md = MarkdownIt("commonmark", {"html": True, "breaks": False}).enable("table")
        self.options = options or resolve_render_options()

    def render(self, markdown: str) -> RenderResult:
        images = _IMAGE_RE.findall(markdown)
        html = self._md.render(_preprocess_markdown(markdown))
        html = _decorate_html(html, self.options)
        wrapped = (
            f'<section class="wechat-article wechat-profile-{self.options.profile} '
            f'wechat-theme-{self.options.theme}" style="{css_var_style(self.options)}; font-family: var(--md-font-family); '
            f'font-size: var(--md-font-size); line-height: var(--md-line-height); color: var(--md-text-color); text-align: left;">{html}</section>'
        )
        digest = _build_digest(html)
        return RenderResult(html=wrapped, plain_digest=digest, used_images=images)


def _build_digest(html: str, limit: int = 120) -> str:
    paragraphs = _P_RE.findall(html)
    source = paragraphs[0] if paragraphs else html
    text = _TAG_RE.sub(" ", source)
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


def _decorate_html(html: str, options: RenderOptions) -> str:
    vars_map = build_css_vars(options)
    primary = vars_map["--md-primary-color"]
    text = vars_map["--md-text-color"]
    muted = vars_map["--md-muted-color"]
    soft = vars_map["--md-soft-bg"]
    code_bg = vars_map["--md-code-bg"]
    code_fg = vars_map["--md-code-fg"]
    border = vars_map["--md-border-color"]
    code_border = vars_map["--md-code-border"]
    heading_bg = vars_map["--md-heading-bg"]
    font_family = vars_map["--md-font-family"]
    font_size = vars_map["--md-font-size"]
    line_height = vars_map["--md-line-height"]

    p_extra = []
    if options.justify:
        p_extra.append("text-align: justify")
    if options.indent_first_line:
        p_extra.append("text-indent: 2em")
    p_extra_style = "; ".join(p_extra)

    replacements = [
        (r"<h1>", _h1_open(options, primary, text)),
        (r"<h2>", _h2_open(options, heading_bg, primary, text)),
        (r"<h3>", _h3_open(options, primary, text)),
        (r"<h4>", _h4_open(options, primary)),
        (r"<h5>", _h5_open(options, primary)),
        (r"<h6>", _h6_open(options, primary)),
        (r'<section class="md-callout md-callout-note" data-callout="note">', f'<section class="md-callout md-callout-note" style="margin: 1.2em 0; padding: 1em 1.1em; border-radius: 12px; background: {soft}; border-left: 4px solid {primary}; box-shadow: 0 8px 24px rgba(15,23,42,.05);">'),
        (r'<section class="md-callout md-callout-tip" data-callout="tip">', f'<section class="md-callout md-callout-tip" style="margin: 1.2em 0; padding: 1em 1.1em; border-radius: 12px; background: #ecfdf5; border-left: 4px solid #10b981; box-shadow: 0 8px 24px rgba(16,185,129,.08);">'),
        (r'<section class="md-callout md-callout-important" data-callout="important">', f'<section class="md-callout md-callout-important" style="margin: 1.2em 0; padding: 1em 1.1em; border-radius: 12px; background: #eef2ff; border-left: 4px solid #6366f1; box-shadow: 0 8px 24px rgba(99,102,241,.08);">'),
        (r'<section class="md-callout md-callout-warning" data-callout="warning">', f'<section class="md-callout md-callout-warning" style="margin: 1.2em 0; padding: 1em 1.1em; border-radius: 12px; background: #fff7ed; border-left: 4px solid #f59e0b; box-shadow: 0 8px 24px rgba(245,158,11,.08);">'),
        (r'<section class="md-callout md-callout-caution" data-callout="caution">', f'<section class="md-callout md-callout-caution" style="margin: 1.2em 0; padding: 1em 1.1em; border-radius: 12px; background: #fef2f2; border-left: 4px solid #ef4444; box-shadow: 0 8px 24px rgba(239,68,68,.08);">'),
        (r'<section class="md-callout md-callout-info" data-callout="info">', f'<section class="md-callout md-callout-info" style="margin: 1.2em 0; padding: 1em 1.1em; border-radius: 12px; background: #eff6ff; border-left: 4px solid #3b82f6; box-shadow: 0 8px 24px rgba(59,130,246,.08);">'),
        (r'<p class="md-callout-title">', f'<p class="md-callout-title" style="margin: 0 0 .45em; font-size: .9em; font-weight: 700; letter-spacing: .08em; color: {muted}; text-transform: uppercase;">'),
        (r"<p>", f'<p class="md-p" style="margin: 1.5em 8px; color: {text}; font-family: inherit; font-size: {options.font_size}px; line-height: inherit; letter-spacing: 0.1em;{p_extra_style}">'),
        (r"<blockquote>", _blockquote_open(options, primary, muted, soft)),
        (r"<blockquote class=\"wechat-blockquote\">", _blockquote_open(options, primary, muted, soft)),
        (r"<ul>", _ul_open(options, text)),
        (r"<ol>", _ol_open(options, text)),
        (r"<li>", _li_open(options, text)),
        (r"<pre><code", _pre_open(options, code_bg, code_fg, code_border)),
        (r"<code>", '<code class="md-inline-code" style="font-size: 90%; color: #d14; background: rgba(27, 31, 35, 0.05); padding: 3px 5px; border-radius: 4px;">'),
        (r"<hr ?/?>", _hr_open(options, border, primary)),
        (r"<img ", _image_open(options)),
        (r"<a href=", '<a class="md-link" style="color: #576b95; text-decoration: none;" href='),
        (r"<strong>", f'<strong class="md-strong" style="color: {primary}; font-weight: 700; font-size: {options.font_size}px;">'),
        (r"<em>", f'<em class="md-em" style="color: {text}; font-style: italic; font-size: {options.font_size}px;">'),
        (r"<table>", _table_open(options, text)),
        (r"<thead>", _thead_open(options)),
        (r"<th>", _th_open(options, border, soft)),
        (r"<td>", _td_open(options, border)),
    ]
    for pattern, replacement in replacements:
        html = re.sub(pattern, replacement, html)
    html = re.sub(r'<figure class="md-figure"([^>]*)>', f'<figure class="md-figure"\\1 style="margin: 1.5em 8px; color: {text};">', html)
    html = _compact_nested_paragraphs(html, options)
    html = _enhance_code_blocks(html, options)
    html = _apply_caption_mode(html, options)
    html = _rewrite_external_links(html, options)
    return html


def _preprocess_markdown(markdown: str) -> str:
    markdown = _CALLOUT_BLOCK_RE.sub(_replace_callout_block, markdown)
    markdown = _IMAGE_WITH_TITLE_RE.sub(_replace_image_with_figure, markdown)
    return markdown


def _compact_nested_paragraphs(html: str, options: RenderOptions) -> str:
    def replace_blockquote_paragraph(match: re.Match[str]) -> str:
        prefix, style = match.groups()
        style = style.replace('color: #24292f;', 'color: inherit;').replace('font-size: inherit;', 'font-size: 1em;')
        return f'{prefix}<p class="md-p md-blockquote-p" style="display: block; {style}; margin: 0;">'

    def replace_list_paragraph(match: re.Match[str]) -> str:
        prefix, style = match.groups()
        return f'{prefix}<p class="md-p md-li-p" style="{style}; margin: 0;">'

    html = re.sub(
        r'(<blockquote[^>]*>\s*)<p class="md-p" style="([^"]*)">',
        replace_blockquote_paragraph,
        html,
    )
    html = re.sub(
        r'(<li[^>]*>\s*)<p class="md-p" style="([^"]*)">',
        replace_list_paragraph,
        html,
    )
    html = _rewrite_unordered_lists(html, options)
    html = _rewrite_ordered_lists(html, options)
    return html


def _rewrite_unordered_lists(html: str, options: RenderOptions) -> str:
    list_pattern = re.compile(r'<ul class="md-ul"[^>]*>(.*?)</ul>', re.S)
    item_pattern = re.compile(r'<li class="md-li"[^>]*>(.*?)</li>', re.S)

    def repl(match: re.Match[str]) -> str:
        body = match.group(1)
        items = item_pattern.findall(body)
        if not items:
            return match.group(0)
        margin = '0' if options.theme == 'default' else '.8em 0'
        item_margin = '0.2em 8px' if options.theme == 'default' else '0.5em 8px'
        parts = [f'<section class="md-list md-list-unordered" style="margin: {margin};">']
        for item in items:
            item = item.strip()
            parts.append(
                f'<p class="md-bullet-item" style="margin: {item_margin}; color: inherit; font-size: {options.font_size}px; line-height: inherit;">'
                '<span class="md-bullet-dot" style="display: inline-block; width: 1.1em; font-weight: 700;">•</span>'
                f'<span class="md-bullet-text">{item}</span>'
                '</p>'
            )
        parts.append('</section>')
        return ''.join(parts)

    return list_pattern.sub(repl, html)


def _rewrite_ordered_lists(html: str, options: RenderOptions) -> str:
    list_pattern = re.compile(r'<ol class="md-ol"[^>]*>(.*?)</ol>', re.S)
    item_pattern = re.compile(r'<li class="md-li"[^>]*>(.*?)</li>', re.S)

    def repl(match: re.Match[str]) -> str:
        body = match.group(1)
        items = item_pattern.findall(body)
        if not items:
            return match.group(0)
        margin = '0' if options.theme == 'default' else '.8em 0'
        item_margin = '0.2em 8px' if options.theme == 'default' else '0.5em 8px'
        parts = [f'<section class="md-list md-list-ordered" style="margin: {margin};">']
        for index, item in enumerate(items, start=1):
            item = item.strip()
            parts.append(
                f'<section class="md-ordered-item" style="margin: {item_margin}; color: inherit; font-size: {options.font_size}px; line-height: inherit; display: flex; align-items: flex-start;">'
                f'<span class="md-ordered-index" style="display: inline-block; min-width: 2.2em; font-weight: 700; flex: 0 0 auto;">{index}.</span>'
                f'<section class="md-ordered-text" style="flex: 1 1 auto; min-width: 0;">{item}</section>'
                '</section>'
            )
        parts.append('</section>')
        return ''.join(parts)

    return list_pattern.sub(repl, html)


def _replace_image_with_figure(match: re.Match[str]) -> str:
    alt = (match.group('alt') or '').strip()
    src = (match.group('src') or '').strip()
    title = (match.group('title') or '').strip()
    title_attr = f' title="{title}"' if title else ''
    caption_attr = f' data-caption-alt="{alt}" data-caption-title="{title}"' if (alt or title) else ''
    return (
        f'<figure class="md-figure"{caption_attr}>'
        f'<img src="{src}" alt="{alt}"{title_attr} />'
        f'<figcaption class="md-figure-caption"></figcaption>'
        f'</figure>'
    )


def _apply_caption_mode(html: str, options: RenderOptions) -> str:
    pattern = re.compile(r'<figure class="md-figure"([^>]*)>\s*(<img[^>]*>)\s*<figcaption class="md-figure-caption"></figcaption>\s*</figure>', re.S)

    def repl(match: re.Match[str]) -> str:
        attrs, img = match.groups()
        alt_match = re.search(r'data-caption-alt="([^"]*)"', attrs)
        title_match = re.search(r'data-caption-title="([^"]*)"', attrs)
        alt = alt_match.group(1) if alt_match else ''
        title = title_match.group(1) if title_match else ''
        caption = _resolve_caption_text(options.caption_mode, alt=alt, title=title)
        if not caption:
            return f'<figure class="md-figure" style="margin: 1.5em 8px; color: inherit;">{img}</figure>'
        caption_html = f'<figcaption class="md-figure-caption" style="text-align: center; color: #888; font-size: 0.8em;">{caption}</figcaption>'
        return f'<figure class="md-figure" style="margin: 1.5em 8px; color: inherit;">{img}{caption_html}</figure>'

    return pattern.sub(repl, html)


def _resolve_caption_text(mode: str, *, alt: str, title: str) -> str:
    if mode == 'title-first':
        return title or alt
    if mode == 'alt-first':
        return alt or title
    if mode == 'title-only':
        return title
    if mode == 'alt-only':
        return alt
    return ''


def _rewrite_external_links(html: str, options: RenderOptions) -> str:
    if not options.footnote_links:
        return html

    refs: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        href, text = match.groups()
        if href.startswith('#'):
            return match.group(0)
        refs.append((text, href))
        idx = len(refs)
        return f'<span class="md-link-ref">{text}<sup>[{idx}]</sup></span>'

    html = _LINK_RE.sub(repl, html)
    if not refs:
        return html
    items = []
    for idx, (text, href) in enumerate(refs, start=1):
        items.append(
            f'<p class="md-link-footnote-item" style="margin: .35em 0; color: #57606a; font-size: .92em; line-height: 1.7;"><strong>[{idx}]</strong> {text}: {href}</p>'
        )
    footnotes = '<section class="md-link-footnotes" style="margin-top: 1.6em; padding-top: .8em; border-top: 1px solid #d0d7de;">' \
        '<p style="margin: 0 0 .5em; font-size: .95em; font-weight: 700; color: #24292f;">参考链接</p>' + ''.join(items) + '</section>'
    return html + footnotes


def _replace_callout_block(match: re.Match[str]) -> str:
    callout_type = match.group(1).lower()
    body = match.group(2)
    lines: list[str] = []
    for raw_line in body.splitlines():
        if not raw_line.startswith(">"):
            continue
        stripped = raw_line[1:]
        if stripped.startswith(" "):
            stripped = stripped[1:]
        lines.append(stripped)
    content = "\n".join(lines).strip()
    title = {
        "note": "说明",
        "tip": "提示",
        "important": "重点",
        "warning": "注意",
        "caution": "警告",
        "info": "信息",
    }.get(callout_type, callout_type.upper())
    return (
        f'<section class="md-callout md-callout-{callout_type}" data-callout="{callout_type}">\n'
        f'<p class="md-callout-title">{title}</p>\n'
        f"<p>{content}</p>\n"
        "</section>\n"
    )


def _hex_to_rgba(color: str, alpha: float) -> str:
    value = color.lstrip("#")
    if len(value) != 6:
        return color
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _blockquote_open(options: RenderOptions, primary: str, muted: str, soft: str) -> str:
    if options.theme == "grace":
        return f'<blockquote class="wechat-blockquote md-blockquote" style="font-style: italic; margin-bottom: 1em; padding: 1em 1em 1em 2em; color: rgba(0, 0, 0, 0.6); background: {soft}; border-left: 4px solid {primary}; border-radius: 6px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">'
    if options.theme == "simple":
        return '<blockquote class="wechat-blockquote md-blockquote" style="font-style: italic; margin-bottom: 1em; padding: 1em 1em 1em 2em; color: rgba(0, 0, 0, 0.6); background: transparent; border-left: 4px solid var(--md-primary-color); border-top: 0.2px solid rgba(0, 0, 0, 0.04); border-right: 0.2px solid rgba(0, 0, 0, 0.04); border-bottom: 0.2px solid rgba(0, 0, 0, 0.04); border-radius: 0;">'
    return f'<blockquote class="wechat-blockquote md-blockquote" style="font-style: normal; margin-bottom: 1em; padding: 1em; color: {muted}; background: {soft}; border-left: 4px solid {primary}; border-radius: 6px;">'


def _ul_open(options: RenderOptions, text: str) -> str:
    if options.theme == "default":
        return f'<ul class="md-ul" style="list-style: circle; padding-left: 1em; margin-left: 0; color: {text};">'
    # grace and simple themes use list-style: none (aligned with Doocs)
    return f'<ul class="md-ul" style="list-style: none; padding-left: 1.5em; margin-left: 0; color: {text};">'


def _ol_open(options: RenderOptions, text: str) -> str:
    if options.theme == "default":
        return f'<ol class="md-ol" style="padding-left: 1em; margin-left: 0; color: {text};">'
    return f'<ol class="md-ol" style="padding-left: 1.5em; margin-left: 0; color: {text};">'


def _li_open(options: RenderOptions, text: str) -> str:
    margin = "0.2em 8px" if options.theme == "default" else "0.5em 8px"
    return f'<li class="md-li" style="display: block; margin: {margin}; color: {text}; font-size: {options.font_size}px; line-height: inherit;">'


def _hr_open(options: RenderOptions, border: str, primary: str) -> str:
    if options.hr_style == "star":
        return (
            f'<section class="md-hr md-hr-star" style="margin: 2em auto; width: 100%; text-align: center; color: {primary}; '
            f'letter-spacing: .35em; font-size: .95em;">✦ ✦ ✦</section>'
        )
    if options.hr_style == "underscore":
        return f'<section class="md-hr md-hr-underscore" style="margin: 2em auto; width: 72px; border-top: 3px solid {primary};"></section>'
    if options.theme in {"grace", "simple"}:
        return '<hr class="md-hr md-hr-dash" style="height: 1px; border: none; margin: 2em 0; background: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.1), rgba(0, 0, 0, 0));">'
    return '<hr class="md-hr md-hr-dash" style="border-style: solid; border-width: 2px 0 0; border-color: rgba(0, 0, 0, 0.1); -webkit-transform-origin: 0 0; -webkit-transform: scale(1, 0.5); transform-origin: 0 0; transform: scale(1, 0.5); height: 0.4em; margin: 1.5em 0;">'


def _pre_open(options: RenderOptions, code_bg: str, code_fg: str, code_border: str) -> str:
    classes = ["code-block", "md-pre"]
    margin = "10px 8px"
    border_radius = "8px"
    line_height = "1.5"
    box_shadow = "none"
    overflow_css = "overflow-x: auto; overflow-y: hidden;"
    if options.mac_code_block:
        classes.append("md-pre-mac")
    if options.theme == "grace":
        box_shadow = "inset 0 0 10px rgba(0, 0, 0, 0.05)"
    elif options.theme == "simple":
        box_shadow = "none"
        code_border = "rgba(0, 0, 0, 0.04)"
    class_str = " ".join(classes)
    border_css = 'none' if options.theme in {'default', 'grace'} else f'1px solid {code_border}'
    return (
        f'<pre class="{class_str}" style="font-size: 90%; margin: {margin}; padding: 0; {overflow_css} '
        f'-webkit-overflow-scrolling: touch; border-radius: {border_radius}; line-height: {line_height}; background: {code_bg}; color: {code_fg}; border: {border_css}; '
        f'box-shadow: {box_shadow}; position: relative;\"><code'
    )


def _image_open(options: RenderOptions) -> str:
    if options.theme == "grace":
        # Aligned with Doocs: no margin on img, figure handles spacing
        return '<img class="md-img" style="display: block; max-width: 100%; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);" '
    if options.theme == "simple":
        return '<img class="md-img" style="display: block; max-width: 100%; border-radius: 8px; border: 1px solid rgba(0, 0, 0, 0.04);" '
    return '<img class="md-img" style="display: block; max-width: 100%; margin: 0.1em auto 0.5em; border-radius: 4px;" '


def _table_open(options: RenderOptions, text: str) -> str:
    if options.theme == "grace":
        return f'<table class="md-table" style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 1em 8px; font-size: {options.font_size}px; border-radius: 8px; color: {text}; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">'
    return f'<table class="md-table" style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 1em 8px; font-size: {options.font_size}px;">'


def _thead_open(options: RenderOptions) -> str:
    if options.theme == "grace":
        return '<thead class="md-thead" style="color: #fff;">'
    return '<thead class="md-thead">'


def _th_open(options: RenderOptions, border: str, soft: str) -> str:
    if options.theme == "default":
        return f'<th class="md-th" style="border: 1px solid #dfdfdf; padding: 0.25em 0.5em; color: inherit; word-break: keep-all; background: rgba(0, 0, 0, 0.05); text-align: left; font-size: {options.font_size}px;">'
    return f'<th class="md-th" style="padding: 10px 12px; border: 1px solid {border}; background: {soft}; text-align: left; font-size: {options.font_size}px;">'


def _td_open(options: RenderOptions, border: str) -> str:
    if options.theme == "grace":
        return f'<td class="md-td" style="padding: 0.5em 1em; border: 1px solid {border}; text-align: left; font-size: {options.font_size}px;">'
    if options.theme == "default":
        return f'<td class="md-td" style="border: 1px solid #dfdfdf; padding: 0.25em 0.5em; color: inherit; word-break: keep-all; text-align: left; font-size: {options.font_size}px;">'
    return f'<td class="md-td" style="padding: 10px 12px; border: 1px solid {border}; text-align: left; font-size: {options.font_size}px;">'


def _enhance_code_blocks(html: str, options: RenderOptions) -> str:
    pattern = re.compile(r'(<pre class="[^"]*md-pre[^"]*"[^>]*>)(<code.*?</code></pre>)', re.S)

    def repl(match: re.Match[str]) -> str:
        pre_open, code_block = match.groups()
        prefix = ""
        language = 'text'
        code_open_match = re.match(r'(<code[^>]*>)', code_block)
        if code_open_match:
            language = _extract_code_language(code_open_match.group(1))

        if options.mac_code_block:
            prefix += (
                '<span class="md-code-window-dots md-code-window-mac" '
                'style="display:block;padding:10px 14px 0;line-height:0;user-select:none;">'
                f'{_MAC_CODE_SVG}'
                '</span>'
            )

        if code_open_match:
            code_open = code_open_match.group(1)
            content_match = re.match(r'<code[^>]*>(.*?)</code></pre>', code_block, re.S)
            if content_match:
                encoded_content = content_match.group(1)
                raw_code = html_lib.unescape(encoded_content)
                rendered_content = _render_code_block_content(raw_code, language, options)
                code_block = f'{code_open}{rendered_content}</code></pre>'

        code_style = _code_block_style(options)
        code_block = code_block.replace(
            '<code',
            f'<code style="{code_style}"',
            1,
        )
        return pre_open + prefix + code_block

    return pattern.sub(repl, html)


def _extract_code_language(code_open: str) -> str:
    match = re.search(r'class="[^"]*language-([^\s"]+)', code_open)
    if not match:
        return 'text'
    language = match.group(1).strip().lower()
    aliases = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'shell': 'bash',
        'sh': 'bash',
        'yml': 'yaml',
        'md': 'markdown',
        'text': 'text',
        'plaintext': 'text',
    }
    return aliases.get(language, language)


def _remap_pygments_colors_to_github_like(html: str) -> str:
    replacements = {
        '#008000': '#22863A',  # keywords / shell builtins
        '#00F': '#6F42C1',
        '#0000FF': '#6F42C1',
        '#19177C': '#005CC5',
        '#666': '#24292E',
        '#666666': '#24292E',
        '#BA2121': '#032F62',
        '#AA5D1F': '#032F62',
        '#3D7B7B': '#6A737D',
        '#BBB': '#24292E',
        '#bbbbbb': '#24292E',
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    return html


def _pygments_inline_html(code: str, language: str) -> str:
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        lexer = TextLexer()
    formatter = HtmlFormatter(nowrap=True, noclasses=True)
    highlighted = highlight(code, lexer, formatter)
    return _remap_pygments_colors_to_github_like(highlighted)


def _format_highlighted_html_preserve_spaces(highlighted_html: str, *, preserve_newlines: bool) -> str:
    formatted = highlighted_html
    formatted = re.sub(
        r'(<span[^>]*>[^<]*</span>)(\s+)(<span[^>]*>[^<]*</span>)',
        lambda m: m.group(1) + m.group(3).replace(m.group(3).split('>', 1)[0] + '>', m.group(3).split('>', 1)[0] + '>' + m.group(2), 1),
        formatted,
    )
    formatted = re.sub(
        r'(\s+)(<span[^>]*>)',
        lambda m: m.group(2).replace('>', '>' + m.group(1), 1),
        formatted,
    )
    formatted = formatted.replace('\t', '    ')
    if preserve_newlines:
        formatted = formatted.replace('\r\n', '<br/>').replace('\n', '<br/>')
    parts = re.split(r'(<[^>]+>)', formatted)
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith('<') and part.endswith('>'):
            out.append(part)
        else:
            out.append(part.replace(' ', '&nbsp;'))
    return ''.join(out)


def _render_code_block_content(raw_code: str, language: str, options: RenderOptions) -> str:
    if options.code_line_numbers:
        return _render_highlighted_code_lines(raw_code, language)
    highlighted = _pygments_inline_html(raw_code, language)
    return _format_highlighted_html_preserve_spaces(highlighted, preserve_newlines=True)


def _render_highlighted_code_lines(raw_code: str, language: str) -> str:
    raw_lines = raw_code.replace('\r\n', '\n').split('\n')
    if raw_lines and raw_lines[-1] == '':
        raw_lines = raw_lines[:-1]
    highlighted_lines: list[str] = []
    for line in raw_lines:
        highlighted = _pygments_inline_html(line, language)
        formatted = _format_highlighted_html_preserve_spaces(highlighted, preserve_newlines=False)
        highlighted_lines.append(formatted or '&nbsp;')
    line_numbers_html = ''.join(
        f'<section style="padding:0 10px 0 0;line-height:1.75">{idx}</section>'
        for idx in range(1, len(highlighted_lines) + 1)
    )
    code_inner_html = '<br/>'.join(highlighted_lines)
    code_lines_html = f'<div style="white-space:pre;min-width:max-content;line-height:1.75">{code_inner_html}</div>'
    line_number_column_styles = 'text-align:right;padding:8px 0;border-right:1px solid rgba(0,0,0,0.04);user-select:none;background:var(--code-bg,transparent);'
    return (
        '<section style="display:flex;align-items:flex-start;overflow-x:hidden;overflow-y:auto;width:100%;max-width:100%;padding:0;box-sizing:border-box">'
        f'<section class="line-numbers" style="{line_number_column_styles}">{line_numbers_html}</section>'
        f'<section class="code-scroll" style="flex:1 1 auto;overflow-x:auto;overflow-y:visible;padding:8px;min-width:0;box-sizing:border-box">{code_lines_html}</section>'
        '</section>'
    )


def _code_block_style(options: RenderOptions) -> str:
    top_padding = '0.5em'
    if options.mac_code_block:
        top_padding = '0.35em'
    return (
        f"display: block; padding: {top_padding} 1em 1em; text-indent: 0; "
        "color: inherit; background: none; white-space: pre; margin: 0; min-width: max-content; "
        "word-break: normal; overflow-wrap: normal; box-sizing: border-box; "
        "font-family: 'Fira Code', Menlo, Operator Mono, Consolas, Monaco, monospace;"
    )


def _font_px(options: RenderOptions, scale: float) -> str:
    return f"{round((options.font_size or 16) * scale, 2):g}px"


def _heading_style_for(options: RenderOptions, level: str) -> str:
    if options.heading_styles and level in options.heading_styles:
        return options.heading_styles[level]
    if options.heading_style in {"left-bar", "underline", "minimal"}:
        mapping = {
            "left-bar": "border-left",
            "underline": "border-bottom",
            "minimal": "color-only",
        }
        return mapping[options.heading_style]
    if level == "h2" and options.heading_style == "solid":
        return "solid"
    return "default"


def _h1_open(options: RenderOptions, primary: str, text: str) -> str:
    style_type = _heading_style_for(options, "h1")
    scale = 1.4 if options.theme in {"grace", "simple"} else 1.2
    # When justify is False, use left alignment for headings too
    align = "left" if not options.justify else "center"
    if style_type == "color-only":
        return f'<h1 class="md-h1 md-h1-color-only" style="display: block; margin: 2em 8px 1em; color: {primary}; font-size: {_font_px(options, scale)}; font-weight: 700; text-align: {align}; background: transparent;">'
    if style_type == "border-bottom":
        return f'<h1 class="md-h1 md-h1-border-bottom" style="display: block; margin: 2em 8px 1em; padding-bottom: .3em; color: {primary}; font-size: {_font_px(options, scale)}; font-weight: 700; text-align: {align}; background: transparent; border-bottom: 2px solid {primary};">'
    if style_type == "border-left":
        return f'<h1 class="md-h1 md-h1-border-left" style="display: block; margin: 2em 8px 1em; padding-left: 10px; color: {primary}; font-size: {_font_px(options, scale)}; font-weight: 700; text-align: {align}; background: transparent; border-left: 4px solid {primary};">'
    extra = ''
    if options.theme == "grace":
        extra = ' text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);'
    elif options.theme == "simple":
        extra = ' text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.05);'
    padding = '.5em 1em' if options.theme in {"grace", "simple"} else '0 1em'
    return f'<h1 class="md-h1" style="display: table; padding: {padding}; border-bottom: 2px solid {primary}; margin: 2em auto 1em; color: {text}; font-size: {_font_px(options, scale)}; font-weight: 700; text-align: {align};{extra}">'


def _h2_open(options: RenderOptions, heading_bg: str, primary: str, text: str) -> str:
    style_type = _heading_style_for(options, "h2")
    # When justify is False, use left alignment for headings too
    align = "left" if not options.justify else "center"
    if style_type in {"left-bar", "border-left"}:
        return f'<h2 class="md-h2 md-h2-left-bar md-h2-border-left" style="display: block; margin: 2em 8px 0.75em 0; padding-left: 10px; background: transparent; color: {primary}; font-size: {_font_px(options, 1.2)}; font-weight: 700; text-align: {align}; border-left: 4px solid {primary};">'
    if style_type in {"underline", "border-bottom"}:
        return f'<h2 class="md-h2 md-h2-border-bottom" style="display: block; margin: 2em 8px 0.75em 0; color: {primary}; font-size: {_font_px(options, 1.2)}; font-weight: 700; text-align: {align}; border-bottom: 2px solid {primary}; padding-bottom: .3em; background: transparent;">'
    if style_type in {"minimal", "color-only"}:
        return f'<h2 class="md-h2 md-h2-color-only" style="display: block; margin: 2em 8px 0.75em 0; color: {primary}; font-size: {_font_px(options, 1.2)}; font-weight: 700; text-align: {align}; background: transparent;">'
    scale = 1.3 if options.theme == "grace" else 1.2
    padding = "0.3em 1em"
    border_radius = "8px"
    box_shadow = "0 4px 6px rgba(0, 0, 0, 0.1)"
    if options.theme == "simple":
        padding = "0.3em 1.2em"
        border_radius = "8px 24px 8px 24px"
        box_shadow = "0 2px 6px rgba(0, 0, 0, 0.06)"
    return f'<h2 class="md-h2 md-h2-solid" style="display: table; padding: {padding}; margin: 4em auto 2em; border-radius: {border_radius}; font-size: {_font_px(options, scale)}; line-height: 1.5; color: #fff; background: {heading_bg}; box-shadow: {box_shadow}; text-align: {align}; font-weight: 700;">'


def _h3_open(options: RenderOptions, primary: str, text: str) -> str:
    style_type = _heading_style_for(options, "h3")
    scale = 1.2 if options.theme in {"grace", "simple"} else 1.1
    if style_type == "color-only":
        return f'<h3 class="md-h3 md-h3-color-only" style="margin: 2em 8px 0.75em 0; color: {primary}; font-size: {_font_px(options, scale)}; font-weight: 700; line-height: 1.2; background: transparent;">'
    if style_type == "border-bottom":
        return f'<h3 class="md-h3 md-h3-border-bottom" style="margin: 2em 8px 0.75em 0; padding-bottom: .3em; color: {primary}; font-size: {_font_px(options, scale)}; font-weight: 700; line-height: 1.2; background: transparent; border-bottom: 2px solid {primary};">'
    if style_type == "border-left":
        return f'<h3 class="md-h3 md-h3-border-left" style="padding-left: 12px; border-left: 4px solid {primary}; margin: 2em 8px 0.75em 0; color: {text}; font-size: {_font_px(options, scale)}; font-weight: 700; line-height: 1.2;">'
    if options.theme == "grace":
        return f'<h3 class="md-h3" style="padding-left: 12px; border-left: 4px solid {primary}; border-bottom: 1px dashed {primary}; margin: 2em 8px 0.75em 0; color: {text}; font-size: {_font_px(options, scale)}; font-weight: 700; line-height: 1.2;">'
    if options.theme == "simple":
        accent = _hex_to_rgba(primary, 0.1)
        return f'<h3 class="md-h3" style="padding-left: 12px; border-left: 4px solid {primary}; border-right: 1px solid {accent}; border-bottom: 1px solid {accent}; border-top: 1px solid {accent}; border-radius: 6px; margin: 2em 8px 0.75em 0; color: {text}; font-size: {_font_px(options, scale)}; font-weight: 700; line-height: 2.4em; background: {_hex_to_rgba(primary, 0.08)};">'
    return f'<h3 class="md-h3" style="padding-left: 8px; border-left: 3px solid {primary}; margin: 2em 8px 0.75em 0; color: {text}; font-size: {_font_px(options, scale)}; font-weight: 700; line-height: 1.2;">'


def _h4_open(options: RenderOptions, primary: str) -> str:
    scale = 1.1 if options.theme == "grace" else 1.0
    border_radius = ' border-radius: 6px;' if options.theme == 'simple' else ''
    return f'<h4 class="md-h4" style="margin: 2em 8px 0.5em; font-size: {_font_px(options, scale)}; line-height: 1.5; color: {primary}; font-weight: 700;{border_radius}">'


def _h5_open(options: RenderOptions, primary: str) -> str:
    border_radius = ' border-radius: 6px;' if options.theme == 'simple' else ''
    return f'<h5 class="md-h5" style="margin: 1.5em 8px 0.5em; font-size: {_font_px(options, 1.0)}; line-height: 1.5; color: {primary}; font-weight: 700;{border_radius}">'


def _h6_open(options: RenderOptions, primary: str) -> str:
    border_radius = ' border-radius: 6px;' if options.theme == 'simple' else ''
    return f'<h6 class="md-h6" style="margin: 1.5em 8px 0.5em; font-size: {_font_px(options, 1.0)}; line-height: 1.5; color: {primary}; font-weight: 700;{border_radius}">'


def render_markdown(
    markdown: str,
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
) -> RenderResult:
    options = resolve_render_options(
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
    return WechatRenderer(options).render(markdown)
