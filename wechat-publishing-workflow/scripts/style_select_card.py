#!/usr/bin/env python3
"""Generate a Feishu interactive card for choosing WeChat draft (Doocs) style.

Reads `list-styles` ui_schema from the canonical feishu-doc-to-wechat-draft
publisher and emits a Feishu card JSON 2.0 with select_static controls inside
a form, plus a submit button whose callback carries a task token.

Usage:
    python style_select_card.py --token TASK123 --title "文章标题" \
        [--publisher /path/to/feishu-doc-to-wechat-draft] \
        [--output /tmp/card.json]

Then send with:
    feishu-card --as user --chat-id <oc_...> --json /tmp/card.json
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_PUBLISHER = Path(
    os.environ.get(
        "WECHAT_DRAFT_PUBLISHER_DIR",
        str(Path(__file__).resolve().parents[2] / "feishu-doc-to-wechat-draft"),
    )
)

# Curated subset of ui_schema sections, in display order. Keep the card
# mobile-friendly: 6 controls max.
CURATED = [
    ("theme_colors", "select"),      # color-grid -> select_static
    ("font_size", "select"),
    ("font", "select"),
    ("heading_style", "select"),
    ("code_theme", "select"),
    ("caption_mode", "select"),
    ("mac_code_block", "select"),
]


def load_ui_schema(publisher: Path) -> dict:
    out = subprocess.run(
        [sys.executable, "scripts/run.py", "list-styles"],
        cwd=publisher, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)["ui_schema"]


def pt(text: str) -> dict:
    return {"tag": "plain_text", "content": text}


def option_label(sec: dict, opt: dict) -> str:
    label = opt.get("label", str(opt["value"]))
    hexv = opt.get("hex")
    return f"{label} {hexv}" if hexv else label


def build_control(sec: dict) -> dict:
    options = [
        {"text": pt(option_label(sec, o)), "value": str(o["value"])}
        for o in sec["options"]
    ]
    default = sec.get("recommended", sec.get("default"))
    initial_index = 0
    for i, o in enumerate(sec["options"]):
        if str(o["value"]) == str(default):
            initial_index = i
            break
    select = {
        "tag": "select_static",
        "name": sec["bind"],
        "initial_index": initial_index,
        "options": options,
    }
    return {
        "tag": "column_set",
        "columns": [
            {
                "tag": "column",
                "width": "weighted",
                "weight": 1,
                "elements": [{"tag": "markdown", "content": f"**{sec['label']}**"}],
            },
            {
                "tag": "column",
                "width": "weighted",
                "weight": 2,
                "elements": [select],
            },
        ],
    }


def build_card(schema: dict, token: str, title: str, doc_url: str) -> dict:
    sections = {s["key"]: s for s in schema["sections"]}
    controls = []
    for key, _kind in CURATED:
        if key in sections:
            controls.append(build_control(sections[key]))

    form_elements = controls + [
        {
            "tag": "button",
            "name": "confirm",
            "text": pt("✅ 用这个风格发布"),
            "type": "primary",
            "form_action_type": "submit",
            "behaviors": [
                {"type": "callback", "value": {"action": "wechat_style_confirm", "token": token}}
            ],
        }
    ]

    return {
        "schema": "2.0",
        "config": {"update_multi": True},
        "header": {
            "title": pt(f"🎨 选择公众号排版风格 · {token}"),
            "template": "orange",
        },
        "body": {
            "elements": [
                {
                    "tag": "markdown",
                    "content": (
                        f"待发布：**{title}**\n"
                        f"文档：{doc_url}\n"
                        "选好风格后点底部按钮；不操作则 10 分钟后用默认风格（活力橙·grace·15px）。"
                    ),
                },
                {"tag": "form", "name": "style_form", "elements": form_elements},
            ]
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True, help="correlation token for this publish task")
    ap.add_argument("--title", required=True, help="article title shown on the card")
    ap.add_argument("--doc-url", default="", help="source Feishu doc URL")
    ap.add_argument("--publisher", default=str(DEFAULT_PUBLISHER))
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    schema = load_ui_schema(Path(args.publisher))
    card = build_card(schema, args.token, args.title, args.doc_url or "(未提供)")
    Path(args.output).write_text(
        json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"ok": True, "output": args.output, "token": args.token}, ensure_ascii=False))


if __name__ == "__main__":
    main()
