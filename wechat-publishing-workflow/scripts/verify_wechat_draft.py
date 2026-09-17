#!/usr/bin/env python3
"""Verify a WeChat Official Account draft using cached stable_token.

Usage:
  python scripts/verify_wechat_draft.py <draft_media_id>

Reads ~/.cache/wechat-draft-publisher/access_token_*.json, calls draft/get and
draft/batchget, then prints compact JSON metrics useful after Feishu-doc publish.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def _post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: verify_wechat_draft.py <draft_media_id>", file=sys.stderr)
        return 2
    media_id = sys.argv[1]
    token_files = sorted((Path.home() / ".cache/wechat-draft-publisher").glob("access_token_*.json"))
    if not token_files:
        raise SystemExit("No cached token found under ~/.cache/wechat-draft-publisher/")
    token = json.loads(token_files[-1].read_text())["access_token"]
    qtoken = urllib.parse.quote(token)

    got = _post_json(f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={qtoken}", {"media_id": media_id})
    batch = _post_json(
        f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={qtoken}",
        {"offset": 0, "count": 20, "no_content": 1},
    )
    item = (got.get("news_item") or [{}])[0]
    content = item.get("content") or ""
    summary = {
        "media_id": media_id,
        "errcode_get": got.get("errcode", 0),
        "title": item.get("title"),
        "author": item.get("author"),
        "thumb_media_id": item.get("thumb_media_id"),
        "thumb_present": bool(item.get("thumb_media_id")),
        "content_len": len(content),
        "img_count": content.count("<img"),
        "mmbiz_qpic_count": content.count("mmbiz.qpic.cn"),
        "lark_image_count": content.count("lark-image://"),
        "FA5151_count": content.count("#FA5151"),
        "15px_count": content.count("15px"),
        "nowrap_count": content.count("white-space: nowrap"),
        "webkit_box_count": content.count("display: -webkit-box"),
        "table_layout_fixed_count": content.count("table-layout: fixed"),
        "batch_errcode": batch.get("errcode", 0),
        "batch_total_count": batch.get("total_count"),
        "visible_in_batch": any(x.get("media_id") == media_id for x in batch.get("item", [])),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
