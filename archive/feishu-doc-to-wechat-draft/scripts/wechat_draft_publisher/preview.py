from __future__ import annotations

from pathlib import Path

from .lark_docs import load_lark_doc_article
from .loader import load_article
from .renderer import render_markdown
from .rendering import RenderOptions, build_css_vars, resolve_render_options

SHELL_STYLE = """
body {
  margin: 0;
  background: #f3f5f7;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: #1f2328;
}
.preview-shell {
  max-width: 920px;
  margin: 0 auto;
  padding: 32px 20px 64px;
}
.phone-frame {
  max-width: 440px;
  margin: 0 auto;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,.08);
  overflow: hidden;
  border: 1px solid rgba(0,0,0,.06);
}
.meta {
  padding: 24px 24px 8px;
}
.meta h1 {
  margin: 0 0 12px;
  font-size: 28px;
  line-height: 1.35;
}
.meta .sub {
  color: #57606a;
  font-size: 14px;
}
"""


def get_preview_style(options: RenderOptions) -> str:
    vars_map = build_css_vars(options)
    vars_block = "; ".join(f"{k}: {v}" for k, v in vars_map.items())
    align = "justify" if options.justify else "left"
    indent = "2em" if options.indent_first_line else "0"
    return f"""
{SHELL_STYLE}
.wechat-article.wechat-profile-{options.profile} {{
  padding: 0 24px 32px;
  font-family: var(--md-font-family);
  font-size: var(--md-font-size);
  line-height: var(--md-line-height);
  color: var(--md-text-color);
  {vars_block};
}}
.wechat-article.wechat-profile-{options.profile} p {{
  text-align: {align};
  text-indent: {indent};
}}
.wechat-article.wechat-profile-doocs h2 {{
  box-shadow: inset 0 -1px 0 rgba(255,255,255,.15);
}}
.wechat-article.wechat-theme-grace .md-pre {{
  box-shadow: 0 12px 28px rgba(91,33,182,.12);
}}
.wechat-article .md-callout {{
  position: relative;
}}
.wechat-article .md-callout-title {{
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(87,107,149,.08);
  text-indent: 0;
}}
.wechat-article .md-hr-star {{
  text-shadow: 0 6px 18px rgba(87,107,149,.12);
}}
.wechat-article img {{ max-width: 100%; }}
"""


def render_preview_document(
    path: str,
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
) -> tuple[dict, str]:
    article = load_article(path)
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
    rendered = render_markdown(
        article.content_markdown,
        profile=options.profile,
        theme=options.theme,
        primary_color=options.primary_color,
        font_family=options.font_family,
        font_size=options.font_size,
        line_height=options.line_height,
        justify=options.justify,
        indent_first_line=options.indent_first_line,
        code_theme=options.code_theme,
        hr_style=options.hr_style,
        heading_style=options.heading_style,
        heading_styles=options.heading_styles,
        mac_code_block=options.mac_code_block,
        code_line_numbers=options.code_line_numbers,
        caption_mode=options.caption_mode,
        footnote_links=options.footnote_links,
    )
    html = f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{article.title}</title>
  <style>{get_preview_style(options)}</style>
</head>
<body>
  <div class=\"preview-shell\">
    <div class=\"phone-frame\">
      <div class=\"meta\">
        <h1>{article.title}</h1>
        <div class=\"sub\">{article.author}</div>
      </div>
      {rendered.html}
    </div>
  </div>
</body>
</html>
"""
    return {
        "title": article.title,
        "author": article.author,
        "used_images": rendered.used_images,
        "profile": options.profile,
        "theme": options.theme,
    }, html


def write_preview_document(
    input_path: str,
    output_path: str,
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
    summary, html = render_preview_document(
        input_path,
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
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return {
        "output_path": str(out),
        "summary": summary,
    }


def write_lark_doc_preview_document(
    doc: str,
    output_path: str,
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
    rendered = render_markdown(
        article.content_markdown,
        profile=options.profile,
        theme=options.theme,
        primary_color=options.primary_color,
        font_family=options.font_family,
        font_size=options.font_size,
        line_height=options.line_height,
        justify=options.justify,
        indent_first_line=options.indent_first_line,
        code_theme=options.code_theme,
        hr_style=options.hr_style,
        heading_style=options.heading_style,
        heading_styles=options.heading_styles,
        mac_code_block=options.mac_code_block,
        code_line_numbers=options.code_line_numbers,
        caption_mode=options.caption_mode,
        footnote_links=options.footnote_links,
    )
    html = f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{article.title}</title>
  <style>{get_preview_style(options)}</style>
</head>
<body>
  <div class=\"preview-shell\">
    <div class=\"phone-frame\">
      <div class=\"meta\">
        <h1>{article.title}</h1>
        <div class=\"sub\">{article.author}</div>
      </div>
      {rendered.html}
    </div>
  </div>
</body>
</html>
"""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return {
        "output_path": str(out),
        "summary": {
            "title": article.title,
            "author": article.author,
            "used_images": rendered.used_images,
            "profile": options.profile,
            "theme": options.theme,
            "doc_id": doc_meta.get("doc_id"),
            "source_url": article.source_url,
        },
    }
