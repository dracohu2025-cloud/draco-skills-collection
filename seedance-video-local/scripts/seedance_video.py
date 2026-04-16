#!/usr/bin/env python3
"""Seedance video generation helper for Volcengine Ark.

为了避免凭据误用，本脚本不主动读取 API Key 环境变量；
请显式传入 --api-key（可在 shell 里写 --api-key "$VOLCENGINE_API_KEY"）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request

DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedance-2-0-260128"
TERMINAL_SUCCESS = {"succeeded"}
TERMINAL_FAIL = {"failed", "expired", "cancelled"}


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def get_base_url() -> str:
    return (os.getenv("ARK_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt.strip()
    if args.prompt_file:
        text = Path(args.prompt_file).read_text(encoding="utf-8")
        return text.strip()
    raise ValueError("必须提供 --prompt 或 --prompt-file")


def _add_role_urls(content: list[dict[str, Any]], urls: list[str], *, media_type: str, role: str) -> None:
    key = f"{media_type}_url"
    for u in urls:
        content.append({"type": key, key: {"url": u}, "role": role})


def build_content(args: argparse.Namespace, prompt: str) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

    _add_role_urls(content, args.ref_image_url or [], media_type="image", role="reference_image")
    _add_role_urls(content, args.ref_video_url or [], media_type="video", role="reference_video")
    _add_role_urls(content, args.ref_audio_url or [], media_type="audio", role="reference_audio")

    _add_role_urls(content, args.first_frame_url or [], media_type="image", role="first_frame")
    _add_role_urls(content, args.last_frame_url or [], media_type="image", role="last_frame")

    return content


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    prompt = read_prompt(args)
    payload: dict[str, Any] = {
        "model": args.model,
        "content": build_content(args, prompt),
        "resolution": args.resolution,
        "ratio": args.ratio,
        "duration": args.duration,
        "watermark": args.watermark,
    }

    if args.generate_audio:
        payload["generate_audio"] = True

    if args.seed is not None:
        payload["seed"] = args.seed

    if args.extra_json:
        extra = json.loads(args.extra_json)
        if not isinstance(extra, dict):
            raise ValueError("--extra-json 必须是 JSON object")
        payload.update(extra)

    return payload


def http_json(method: str, url: str, *, api_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = request.Request(url=url, method=method.upper(), headers=headers, data=data)
    try:
        with request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {}
    except error.HTTPError as ex:
        body = ex.read().decode("utf-8", errors="replace") if ex.fp else ""
        try:
            detail = json.loads(body) if body else {"message": ex.reason}
        except Exception:
            detail = {"message": body or str(ex.reason)}
        raise RuntimeError(json.dumps({"status": ex.code, "error": detail}, ensure_ascii=False))
    except error.URLError as ex:
        raise RuntimeError(f"网络错误: {ex}")


def create_task(payload: dict[str, Any], *, api_key: str, base_url: str) -> dict[str, Any]:
    return http_json("POST", f"{base_url}/contents/generations/tasks", api_key=api_key, payload=payload)


def get_task(task_id: str, *, api_key: str, base_url: str) -> dict[str, Any]:
    return http_json("GET", f"{base_url}/contents/generations/tasks/{task_id}", api_key=api_key)


def cancel_task(task_id: str, *, api_key: str, base_url: str) -> dict[str, Any]:
    return http_json("DELETE", f"{base_url}/contents/generations/tasks/{task_id}", api_key=api_key)


def extract_task_id(resp: dict[str, Any]) -> str | None:
    return (
        resp.get("id")
        or resp.get("task_id")
        or (resp.get("data") or {}).get("id")
        or (resp.get("data") or {}).get("task_id")
    )


def extract_video_url(task: dict[str, Any]) -> str | None:
    content = task.get("content")
    if isinstance(content, dict):
        return content.get("video_url")
    return None


def poll_task(task_id: str, *, api_key: str, base_url: str, interval: int, timeout: int) -> dict[str, Any]:
    start = time.time()
    last_status = None
    while True:
        task = get_task(task_id, api_key=api_key, base_url=base_url)
        status = task.get("status")
        if status != last_status:
            print(json.dumps({"task_id": task_id, "status": status, "updated_at": task.get("updated_at")}, ensure_ascii=False))
            last_status = status

        if status in TERMINAL_SUCCESS | TERMINAL_FAIL:
            return task

        if time.time() - start > timeout:
            raise TimeoutError(f"轮询超时（>{timeout}s），当前状态: {status}")

        time.sleep(interval)


def download_file(url: str, path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    out.write_bytes(data)


def add_generation_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--prompt", help="文本提示词")
    p.add_argument("--prompt-file", help="从文件读取提示词")

    p.add_argument("--ref-image-url", action="append", default=[], help="参考图 URL，可重复")
    p.add_argument("--ref-video-url", action="append", default=[], help="参考视频 URL，可重复")
    p.add_argument("--ref-audio-url", action="append", default=[], help="参考音频 URL，可重复")

    p.add_argument("--first-frame-url", action="append", default=[], help="首帧图 URL，可重复")
    p.add_argument("--last-frame-url", action="append", default=[], help="尾帧图 URL，可重复")

    p.add_argument("--resolution", default="480p", choices=["480p", "720p"], help="默认 480p")
    p.add_argument("--ratio", default="16:9")
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--seed", type=int)

    p.add_argument("--generate-audio", action="store_true")
    p.add_argument("--watermark", action="store_true", default=False)
    p.add_argument("--extra-json", help="附加 JSON object，会 merge 到 payload")


def add_auth_args(p: argparse.ArgumentParser, *, required: bool = True) -> None:
    p.add_argument("--api-key", required=required, help="Ark API Key（建议通过 shell 变量传入）")
    p.add_argument("--base-url", default=get_base_url(), help=f"默认: {DEFAULT_BASE_URL}")


def command_check(args: argparse.Namespace) -> int:
    info = {
        "api_key_arg_passed": bool(args.api_key),
        "base_url": args.base_url,
        "default_model": DEFAULT_MODEL,
        "default_resolution": "480p",
        "tip": "提交任务时请显式传入 --api-key",
    }
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0 if args.api_key else 2


def command_preview(args: argparse.Namespace) -> int:
    payload = build_payload(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_submit(args: argparse.Namespace) -> int:
    payload = build_payload(args)
    resp = create_task(payload, api_key=args.api_key, base_url=args.base_url.rstrip("/"))
    task_id = extract_task_id(resp)
    out = {"task_id": task_id, "raw": resp}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def command_get(args: argparse.Namespace) -> int:
    task = get_task(args.task_id, api_key=args.api_key, base_url=args.base_url.rstrip("/"))
    print(json.dumps(task, ensure_ascii=False, indent=2))
    return 0


def command_cancel(args: argparse.Namespace) -> int:
    resp = cancel_task(args.task_id, api_key=args.api_key, base_url=args.base_url.rstrip("/"))
    print(json.dumps({"task_id": args.task_id, "result": resp}, ensure_ascii=False, indent=2))
    return 0


def command_run(args: argparse.Namespace) -> int:
    payload = build_payload(args)

    create_resp = create_task(payload, api_key=args.api_key, base_url=args.base_url.rstrip("/"))
    task_id = extract_task_id(create_resp)
    if not task_id:
        raise RuntimeError(f"创建任务成功但未解析到 task_id: {json.dumps(create_resp, ensure_ascii=False)}")

    print(json.dumps({"task_id": task_id, "stage": "submitted"}, ensure_ascii=False))
    task = poll_task(
        task_id,
        api_key=args.api_key,
        base_url=args.base_url.rstrip("/"),
        interval=args.poll_interval,
        timeout=args.poll_timeout,
    )

    status = task.get("status")
    video_url = extract_video_url(task)
    out = {"task_id": task_id, "status": status, "video_url": video_url, "task": task}

    if status == "succeeded" and video_url and args.download:
        download_file(video_url, args.download)
        out["downloaded_to"] = str(Path(args.download).resolve())

    print(json.dumps(out, ensure_ascii=False, indent=2))

    if status in TERMINAL_SUCCESS:
        return 0
    return 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Seedance video helper")
    sp = p.add_subparsers(dest="command", required=True)

    p_check = sp.add_parser("check", help="检查参数")
    add_auth_args(p_check, required=False)

    p_preview = sp.add_parser("preview", help="只打印请求 payload")
    add_generation_args(p_preview)

    p_submit = sp.add_parser("submit", help="创建任务")
    add_generation_args(p_submit)
    add_auth_args(p_submit, required=True)

    p_get = sp.add_parser("get", help="查询任务")
    p_get.add_argument("--task-id", required=True)
    add_auth_args(p_get, required=True)

    p_cancel = sp.add_parser("cancel", help="取消/删除任务")
    p_cancel.add_argument("--task-id", required=True)
    add_auth_args(p_cancel, required=True)

    p_run = sp.add_parser("run", help="创建并轮询任务")
    add_generation_args(p_run)
    add_auth_args(p_run, required=True)
    p_run.add_argument("--poll-interval", type=int, default=20)
    p_run.add_argument("--poll-timeout", type=int, default=1800)
    p_run.add_argument("--download", help="成功后下载 mp4 到该路径")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "check":
            return command_check(args)
        if args.command == "preview":
            return command_preview(args)
        if args.command == "submit":
            return command_submit(args)
        if args.command == "get":
            return command_get(args)
        if args.command == "cancel":
            return command_cancel(args)
        if args.command == "run":
            return command_run(args)
        parser.error(f"未知命令: {args.command}")
        return 2
    except Exception as ex:
        eprint(f"ERROR: {ex}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
