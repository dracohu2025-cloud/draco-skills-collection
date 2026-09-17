#!/usr/bin/env python3
"""Wait for a Feishu card.action.trigger callback via long-connection (lark-oapi WS).

Connects with the lark-cli app's credentials (decrypted from the local
file keychain), waits for the card callback carrying our task token, maps
the form select values back to the publisher's label-based style config,
writes it to --output, and exits.

Usage:
    python wait_style_choice.py --token TASK123 --output /tmp/style.json [--timeout 600]

Exit codes: 0 = choice captured; 2 = timeout (caller should use defaults).
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import lark_oapi as lark
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from lark_oapi.event.callback.model.p2_card_action_trigger import (
    CallBackToast,
    P2CardActionTrigger,
    P2CardActionTriggerResponse,
)

DEFAULT_PUBLISHER = Path(
    os.environ.get(
        "WECHAT_DRAFT_PUBLISHER_DIR",
        str(Path(__file__).resolve().parents[1] / "publisher"),
    )
)
KEYCHAIN_DIR = Path.home() / ".local/share/lark-cli"
LARK_CONFIG = Path.home() / ".lark-cli/config.json"

STYLE_KEY_MAP = {
    "primary_color": "theme_colors",
    "font_size": "font_size",
    "font_family": "font",
    "heading_style": "heading_style",
    "code_theme": "code_theme",
    "caption_mode": "caption_mode",
    "mac_code_block": "mac_code_block",
}
BOOL_TRUE = {"true", "1", "yes", "on", "开启"}


def load_app_credentials() -> tuple[str, str]:
    cfg = json.loads(LARK_CONFIG.read_text(encoding="utf-8"))
    app_id = cfg["apps"][0]["appId"]
    master = (KEYCHAIN_DIR / "master.key").read_bytes()
    enc = (KEYCHAIN_DIR / f"appsecret_{app_id}.enc").read_bytes()
    app_cred = AESGCM(master).decrypt(enc[:12], enc[12:], None).decode()
    return app_id, app_cred


def load_value_label_map(publisher: Path) -> dict:
    out = subprocess.run(
        [sys.executable, "scripts/run.py", "list-styles"],
        cwd=publisher, capture_output=True, text=True, check=True,
    )
    schema = json.loads(out.stdout)["ui_schema"]
    mapping = {}
    for sec in schema["sections"]:
        bind = sec["bind"]
        for o in sec.get("options", []):
            if "value" not in o:
                continue
            mapping[(bind, str(o["value"]))] = o.get("label", str(o["value"]))
    return mapping


def to_style_config(form: dict, labels: dict) -> dict:
    style = {"profile": "doocs", "theme": "优雅"}
    for bind, style_key in STYLE_KEY_MAP.items():
        raw = form.get(bind)
        if raw is None:
            continue
        raw = str(raw)
        if style_key == "mac_code_block":
            style[style_key] = "开启" if raw.lower() in BOOL_TRUE else "关闭"
            continue
        style[style_key] = labels.get((bind, raw), raw)
    return {"style": style}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--publisher", default=str(DEFAULT_PUBLISHER))
    args = ap.parse_args()

    labels = load_value_label_map(Path(args.publisher))
    app_id, app_secret = load_app_credentials()

    done = threading.Event()

    def on_card_action(data: P2CardActionTrigger) -> P2CardActionTriggerResponse:
        resp = P2CardActionTriggerResponse()
        action = data.event.action
        value = action.value or {}
        if value.get("token") != args.token:
            return resp
        form = dict(action.form_value or {})
        config = to_style_config(form, labels)
        Path(args.output).write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(
            {"ok": True, "token": args.token, "output": args.output,
             "form": form, "style": config["style"]},
            ensure_ascii=False), flush=True)
        done.set()
        resp.toast = CallBackToast()
        resp.toast.type = "success"
        resp.toast.content = "风格已收到，开始发布 ✅"
        return resp

    event_handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_card_action_trigger(on_card_action)
        .build()
    )
    ws_client = lark.ws.Client(
        app_id, app_secret,
        log_level=lark.LogLevel.WARNING,
        event_handler=event_handler,
    )
    t = threading.Thread(target=ws_client.start, daemon=True)
    t.start()

    if done.wait(timeout=args.timeout):
        sys.exit(0)
    print(json.dumps({"ok": False, "reason": "timeout"}), flush=True)
    sys.exit(2)


if __name__ == "__main__":
    main()
