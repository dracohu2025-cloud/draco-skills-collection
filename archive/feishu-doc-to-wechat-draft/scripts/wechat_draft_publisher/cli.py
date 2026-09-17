from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from .draft import build_draft_payload
from .loader import load_article
from .pipeline import publish_lark_doc, publish_markdown_file
from .preview import write_lark_doc_preview_document, write_preview_document
from .rendering import CAPTION_MODE_LABELS, COLOR_PRESET_LABELS, COLOR_PRESETS, FONT_FAMILY_LABELS, HEADING_LEVEL_LABELS, HEADING_LEVEL_STYLE_LABELS, HEADING_STYLE_LABELS, VALID_CAPTION_MODES, VALID_CODE_THEMES, VALID_HEADING_LEVEL_STYLES, VALID_HEADING_STYLES, VALID_HEADING_LEVELS, VALID_HR_STYLES, VALID_PROFILES, VALID_THEMES, load_style_config_file, load_style_json, resolve_render_options
from .renderer import render_markdown
from .wechat_api import WechatClient


DEFAULT_PUBLISH_STYLE_CONFIG = Path(__file__).resolve().parents[2] / "examples" / "default-publish-style.yaml"


def add_style_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--style-config", help="JSON/YAML style config file")
    parser.add_argument("--style-json", help="inline JSON style config")
    parser.add_argument("--profile", default=None, choices=sorted(VALID_PROFILES))
    parser.add_argument("--theme", default=None, choices=sorted(VALID_THEMES))
    parser.add_argument("--primary-color")
    parser.add_argument("--font-family")
    parser.add_argument("--font-size", type=int)
    parser.add_argument("--line-height", type=float)
    parser.add_argument("--justify", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--indent-first-line", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--code-theme", default=None, choices=sorted(VALID_CODE_THEMES))
    parser.add_argument("--hr-style", default=None, choices=sorted(VALID_HR_STYLES))
    parser.add_argument("--heading-style", default=None, choices=sorted(VALID_HEADING_STYLES))
    for level in sorted(VALID_HEADING_LEVELS):
        parser.add_argument(f"--{level}-style", default=None, choices=sorted(VALID_HEADING_LEVEL_STYLES))
    parser.add_argument("--mac-code-block", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--code-line-numbers", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--caption-mode", default=None, choices=sorted(VALID_CAPTION_MODES))
    parser.add_argument("--footnote-links", action=argparse.BooleanOptionalAction, default=None)


def _style_overrides_from_args(args) -> dict:
    heading_styles = {
        level: getattr(args, f"{level}_style")
        for level in sorted(VALID_HEADING_LEVELS)
        if getattr(args, f"{level}_style") is not None
    }
    return {
        "profile": args.profile,
        "theme": args.theme,
        "primary_color": args.primary_color,
        "font_family": args.font_family,
        "font_size": args.font_size,
        "line_height": args.line_height,
        "justify": args.justify,
        "indent_first_line": args.indent_first_line,
        "code_theme": args.code_theme,
        "hr_style": args.hr_style,
        "heading_style": args.heading_style,
        "heading_styles": heading_styles or None,
        "mac_code_block": args.mac_code_block,
        "code_line_numbers": args.code_line_numbers,
        "caption_mode": args.caption_mode,
        "footnote_links": args.footnote_links,
    }


def add_lark_doc_args(parser: argparse.ArgumentParser, *, require_output: bool = False, publish_mode: bool = False) -> None:
    parser.add_argument("--doc", required=True, help="Feishu/Lark doc URL or token")
    parser.add_argument("--author", default="DracoVibeCoding")
    parser.add_argument("--digest")
    parser.add_argument("--cover-image")
    parser.add_argument("--source-url")
    parser.add_argument("--identity", default="user", choices=["user", "bot"])
    parser.add_argument("--assets-dir", default=".")
    if require_output:
        parser.add_argument("--output", required=True)
    if publish_mode:
        parser.add_argument("--thumb-media-id")
        parser.add_argument("--appid", default=os.getenv("WECHAT_APP_ID"))
        parser.add_argument("--appsecret", default=os.getenv("WECHAT_APP_SECRET"))
        parser.add_argument("--dry-run", action="store_true")
    add_style_args(parser)


def _use_default_style_mode(args) -> bool:
    return getattr(args, "command", None) in {"publish", "publish-default", "render-preview-default", "publish-feishu-doc-default", "render-preview-feishu-doc-default"}


def style_kwargs(args) -> dict:
    merged: dict = {}
    if _use_default_style_mode(args):
        merged.update(load_style_config_file(str(DEFAULT_PUBLISH_STYLE_CONFIG)))
    if getattr(args, "style_config", None):
        merged.update(load_style_config_file(args.style_config))
    if getattr(args, "style_json", None):
        merged.update(load_style_json(args.style_json))
    merged.update({key: value for key, value in _style_overrides_from_args(args).items() if value is not None})
    return asdict(resolve_render_options(**merged))


def available_style_payload() -> dict:
    color_order = list(COLOR_PRESETS.keys())
    heading_style_order = ["solid", "left-bar", "underline", "minimal"]
    heading_level_style_order = ["default", "color-only", "border-bottom", "border-left", "custom"]
    caption_mode_order = ["title-first", "alt-first", "title-only", "alt-only", "hidden"]

    colors_ui = {
        key: {"label": COLOR_PRESET_LABELS.get(key, key), "hex": COLOR_PRESETS[key]}
        for key in color_order
    }
    heading_styles_ui = {
        key: {"label": HEADING_STYLE_LABELS.get(key, key)}
        for key in heading_style_order
    }
    heading_level_styles_ui = {
        key: {"label": HEADING_LEVEL_STYLE_LABELS.get(key, key)}
        for key in heading_level_style_order
    }
    caption_modes_ui = {
        key: {"label": CAPTION_MODE_LABELS.get(key, key)}
        for key in caption_mode_order
    }
    toggles_ui = {
        "mac_code_block": {"label": "Mac 代码块", "default": False},
        "code_line_numbers": {"label": "代码块行号", "default": False},
        "footnote_links": {"label": "微信外链转底部引用", "default": False},
        "indent_first_line": {"label": "段落首行缩进", "default": False},
        "justify": {"label": "段落两端对齐", "default": False},
    }
    fonts_ui = {
        key: {"label": label}
        for key, label in FONT_FAMILY_LABELS.items()
    }
    return {
        "ok": True,
        "profiles": sorted(VALID_PROFILES),
        "themes": sorted(VALID_THEMES),
        "code_themes": sorted(VALID_CODE_THEMES),
        "hr_styles": sorted(VALID_HR_STYLES),
        "heading_styles": heading_style_order,
        "color_presets": color_order,
        "caption_modes": caption_mode_order,
        "footnote_links": True,
        "callouts": ["note", "tip", "important", "warning", "caution", "info"],
        "ui": {
            "fonts": fonts_ui,
            "colors": colors_ui,
            "heading_styles": heading_styles_ui,
            "heading_level_styles": heading_level_styles_ui,
            "caption_modes": caption_modes_ui,
            "toggles": toggles_ui,
        },
        "style_config_support": {
            "file_formats": ["json", "yaml", "yml"],
            "cli_flags": ["--style-config", "--style-json", "--h1-style", "--h2-style", "--h3-style", "--h4-style", "--h5-style", "--h6-style"],
            "default_publish_style_config": str(DEFAULT_PUBLISH_STYLE_CONFIG),
            "default_commands": ["publish", "publish-default", "render-preview-default"],
            "doocs_aligned_defaults": {
                "doocs_code_theme": "github",
                "per_heading_styles": True,
            },
            "wrappers": ["style", "styles", "render", "rendering", "config", "values", "wechat_style"],
            "accepts_labels": True,
            "example": {
                "style": {
                    "profile": "doocs",
                    "theme": "grace",
                    "theme_colors": "活力橘",
                    "font": "无衬线",
                    "font_size": "稍小",
                    "heading_styles": {"h1": "默认", "h2": "默认", "h3": "左边框"},
                    "code_theme": "github-dark",
                    "caption_mode": "title 优先",
                    "mac_code_block": "开启",
                    "code_line_numbers": "关闭",
                    "footnote_links": "开启"
                }
            }
        },
        "ui_schema": {
            "version": 2,
            "sections": [
                {
                    "key": "font",
                    "label": "字体",
                    "control": "segmented",
                    "bind": "font_family",
                    "default": "sans",
                    "recommended": "sans",
                    "options": [
                        {"value": "sans", "label": "无衬线", "aliases": ["sans-serif"]},
                        {"value": "serif", "label": "衬线", "aliases": []},
                        {"value": "mono", "label": "等宽", "aliases": ["monospace"]},
                    ],
                },
                {
                    "key": "font_size",
                    "label": "字号",
                    "control": "segmented",
                    "bind": "font_size",
                    "default": 15,
                    "recommended": 15,
                    "options": [
                        {"value": 14, "label": "更小"},
                        {"value": 15, "label": "稍小"},
                        {"value": 16, "label": "推荐"},
                        {"value": 17, "label": "稍大"},
                        {"value": 18, "label": "更大"},
                    ],
                },
                {
                    "key": "theme_colors",
                    "label": "主题色",
                    "control": "color-grid",
                    "bind": "primary_color",
                    "default": "vitality-orange",
                    "recommended": "vitality-orange",
                    "options": [
                        {"value": key, "label": meta["label"], "hex": meta["hex"]}
                        for key, meta in colors_ui.items()
                    ],
                },
                {
                    "key": "heading_style",
                    "label": "标题样式（兼容旧入口）",
                    "control": "select",
                    "bind": "heading_style",
                    "default": "solid",
                    "recommended": "solid",
                    "options": [
                        {"value": key, "label": meta["label"]}
                        for key, meta in heading_styles_ui.items()
                    ],
                },
                {
                    "key": "code_theme",
                    "label": "代码块主题",
                    "control": "select",
                    "bind": "code_theme",
                    "default": "github",
                    "recommended": "github",
                    "options": [
                        {"value": key, "label": key}
                        for key in sorted(VALID_CODE_THEMES)
                    ],
                },
                {
                    "key": "heading_levels",
                    "label": "各级标题样式",
                    "control": "group",
                    "bind": "heading_styles",
                    "default": {level: "default" for level in sorted(VALID_HEADING_LEVELS)},
                    "recommended": {level: "default" for level in sorted(VALID_HEADING_LEVELS)},
                    "options": [
                        {
                            "key": level,
                            "label": HEADING_LEVEL_LABELS[level],
                            "bind": f"heading_styles.{level}",
                            "default": "default",
                            "options": [
                                {"value": key, "label": meta["label"]}
                                for key, meta in heading_level_styles_ui.items()
                            ],
                        }
                        for level in sorted(VALID_HEADING_LEVELS)
                    ],
                },
                {
                    "key": "caption_mode",
                    "label": "图注格式",
                    "control": "segmented",
                    "bind": "caption_mode",
                    "default": "hidden",
                    "recommended": "hidden",
                    "options": [
                        {"value": key, "label": meta["label"]}
                        for key, meta in caption_modes_ui.items()
                    ],
                },
                {
                    "key": "mac_code_block",
                    "label": "Mac 代码块",
                    "control": "toggle",
                    "bind": "mac_code_block",
                    "default": False,
                    "options": [
                        {"value": True, "label": "开启"},
                        {"value": False, "label": "关闭"},
                    ],
                },
                {
                    "key": "code_line_numbers",
                    "label": "代码块行号",
                    "control": "toggle",
                    "bind": "code_line_numbers",
                    "default": False,
                    "options": [
                        {"value": True, "label": "开启"},
                        {"value": False, "label": "关闭"},
                    ],
                },
                {
                    "key": "footnote_links",
                    "label": "微信外链转底部引用",
                    "control": "toggle",
                    "bind": "footnote_links",
                    "default": False,
                    "options": [
                        {"value": True, "label": "开启"},
                        {"value": False, "label": "关闭"},
                    ],
                },
                {
                    "key": "indent_first_line",
                    "label": "段落首行缩进",
                    "control": "toggle",
                    "bind": "indent_first_line",
                    "default": False,
                    "options": [
                        {"value": True, "label": "开启"},
                        {"value": False, "label": "关闭"},
                    ],
                },
                {
                    "key": "justify",
                    "label": "段落两端对齐",
                    "control": "toggle",
                    "bind": "justify",
                    "default": False,
                    "options": [
                        {"value": True, "label": "开启"},
                        {"value": False, "label": "关闭"},
                    ],
                },
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="wechat-draft-publisher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--input", required=True)
    validate.add_argument("--thumb-media-id", required=True)
    add_style_args(validate)

    preview = subparsers.add_parser("render-preview")
    preview.add_argument("--input", required=True)
    preview.add_argument("--output", required=True)
    add_style_args(preview)

    preview_default = subparsers.add_parser("render-preview-default")
    preview_default.add_argument("--input", required=True)
    preview_default.add_argument("--output", required=True)
    add_style_args(preview_default)

    preview_lark = subparsers.add_parser("render-preview-feishu-doc")
    add_lark_doc_args(preview_lark, require_output=True)

    preview_lark_default = subparsers.add_parser("render-preview-feishu-doc-default")
    add_lark_doc_args(preview_lark_default, require_output=True)

    subparsers.add_parser("list-styles")

    publish = subparsers.add_parser("publish")
    publish.add_argument("--input", required=True)
    publish.add_argument("--thumb-media-id")
    publish.add_argument("--appid", default=os.getenv("WECHAT_APP_ID"))
    publish.add_argument("--appsecret", default=os.getenv("WECHAT_APP_SECRET"))
    publish.add_argument("--dry-run", action="store_true")
    add_style_args(publish)

    publish_default = subparsers.add_parser("publish-default")
    publish_default.add_argument("--input", required=True)
    publish_default.add_argument("--thumb-media-id")
    publish_default.add_argument("--appid", default=os.getenv("WECHAT_APP_ID"))
    publish_default.add_argument("--appsecret", default=os.getenv("WECHAT_APP_SECRET"))
    publish_default.add_argument("--dry-run", action="store_true")
    add_style_args(publish_default)

    publish_lark = subparsers.add_parser("publish-feishu-doc")
    add_lark_doc_args(publish_lark, publish_mode=True)

    publish_lark_default = subparsers.add_parser("publish-feishu-doc-default")
    add_lark_doc_args(publish_lark_default, publish_mode=True)

    args = parser.parse_args()

    if args.command == "validate":
        article = load_article(args.input)
        rendered = render_markdown(article.content_markdown, **style_kwargs(args))
        build_draft_payload(article=article, rendered=rendered, thumb_media_id=args.thumb_media_id)
        print(json.dumps({
            "ok": True,
            "command": "validate",
            "article": asdict(article),
            "used_images": rendered.used_images,
            "style": style_kwargs(args),
        }, ensure_ascii=False))
        return 0

    if args.command in {"render-preview", "render-preview-default"}:
        resolved_style = style_kwargs(args)
        result = write_preview_document(args.input, args.output, **resolved_style)
        print(json.dumps({
            "ok": True,
            "command": args.command,
            "output_path": result["output_path"],
            "summary": result["summary"],
            "style": resolved_style,
        }, ensure_ascii=False))
        return 0

    if args.command in {"render-preview-feishu-doc", "render-preview-feishu-doc-default"}:
        resolved_style = style_kwargs(args)
        result = write_lark_doc_preview_document(
            args.doc,
            args.output,
            author=args.author,
            digest=args.digest,
            cover_image=args.cover_image,
            source_url=args.source_url,
            identity=args.identity,
            **resolved_style,
        )
        print(json.dumps({
            "ok": True,
            "command": args.command,
            "output_path": result["output_path"],
            "summary": result["summary"],
            "style": resolved_style,
        }, ensure_ascii=False))
        return 0

    if args.command == "list-styles":
        print(json.dumps(available_style_payload(), ensure_ascii=False))
        return 0

    if args.command in {"publish", "publish-default", "publish-feishu-doc", "publish-feishu-doc-default"}:
        if args.dry_run:
            client = None
        else:
            if not args.appid or not args.appsecret:
                parser.error("missing WeChat credentials: provide --appid/--appsecret or env WECHAT_APP_ID/WECHAT_APP_SECRET")
            client = WechatClient(appid=args.appid, appsecret=args.appsecret)
        resolved_style = style_kwargs(args)
        if args.command in {"publish", "publish-default"}:
            result = publish_markdown_file(
                args.input,
                client=client,
                dry_run=bool(args.dry_run),
                thumb_media_id=args.thumb_media_id,
                **resolved_style,
            )
        else:
            result = publish_lark_doc(
                args.doc,
                author=args.author,
                client=client,
                dry_run=bool(args.dry_run),
                thumb_media_id=args.thumb_media_id,
                cover_image=args.cover_image,
                digest=args.digest,
                source_url=args.source_url,
                identity=args.identity,
                assets_dir=args.assets_dir,
                **resolved_style,
            )
        output = {
            "ok": True,
            "command": args.command,
            "dry_run": bool(args.dry_run),
            "draft_media_id": result["draft_media_id"],
            "payload": result["payload"],
            "video_materials": result.get("video_materials", []),
            "style": resolved_style,
        }
        if "doc" in result:
            output["doc"] = result["doc"]
        print(json.dumps(output, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
