#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
FETCH_SCRIPT = ROOT_DIR / "scripts" / "fetch_wechat_article.py"
DEFAULT_SEARCH_RETRIES = max(1, int(os.getenv("WECHAT_BROWSERUSE_SEARCH_RETRIES", "6")))
DEFAULT_SEARCH_DELAY_SECONDS = max(0, float(os.getenv("WECHAT_BROWSERUSE_SEARCH_DELAY", "3")))


def _progress(message: str) -> None:
    print(f"[wechat-article-browseruse] {message}", file=sys.stderr, flush=True)



def _load_fetch_module():
    spec = importlib.util.spec_from_file_location("wechat_article_browseruse_fetch", FETCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Unable to load fetch script: {FETCH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def _lark_cli_cmd() -> list[str]:
    cli = shutil.which("lark-cli") or str(Path.home() / ".hermes" / "node" / "bin" / "lark-cli")
    return [cli]



def _run_fetch(url: str, *, include_images: bool, proxy_country: str, timeout_seconds: int, wait_ms: int) -> dict:
    fetch_module = _load_fetch_module()
    return fetch_module.fetch_article(
        url,
        include_images=include_images,
        proxy_country=proxy_country,
        timeout_seconds=timeout_seconds,
        wait_ms=wait_ms,
    )



def _normalize_title(title: str) -> str:
    title = (title or "").strip()
    title = re.sub(r"\\+$", "", title).strip()
    return title or "微信公众号文章抓取结果"



def _clean_body(markdown: str, original_url: str) -> str:
    lines = (markdown or "").splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    body = "\n".join(lines).strip()
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = f"> 原文链接：{original_url}\n\n{body}".strip()
    return body + "\n"



def _run_json_command(args: list[str], *, cwd: str | None = None) -> dict:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or str(exc)
        raise SystemExit(detail) from exc
    return json.loads(proc.stdout)



def _create_doc(title: str, body: str, folder_token: str | None = None) -> dict:
    args = _lark_cli_cmd() + ["docs", "+create", "--as", "user", "--title", title, "--markdown", body]
    if folder_token:
        args.extend(["--folder-token", folder_token])
    return _run_json_command(args)



def _import_doc_file(markdown_file: Path, title: str, folder_token: str | None = None) -> dict:
    args = _lark_cli_cmd() + [
        "drive",
        "+import",
        "--as",
        "user",
        "--file",
        f"./{markdown_file.name}",
        "--type",
        "docx",
        "--name",
        title,
    ]
    if folder_token:
        args.extend(["--folder-token", folder_token])
    return _run_json_command(args, cwd=str(markdown_file.parent))



def _strip_highlight_markup(text: str) -> str:
    return re.sub(r"</?[^>]+>", "", text or "").strip()



def _doc_id_from_url(doc_url: str) -> str:
    match = re.search(r"/docx/([^/?#]+)", doc_url or "")
    return (match.group(1) if match else "").strip()



def _select_best_search_result(search_payload: dict, title: str, *, min_create_time: int | None = None) -> dict:
    results = ((search_payload or {}).get("data") or {}).get("results") or []
    normalized_title = _normalize_title(title)
    best = None
    best_score = None
    for item in results:
        meta = item.get("result_meta") or {}
        doc_url = (meta.get("url") or "").strip()
        doc_id = (meta.get("token") or "").strip()
        if not doc_id or set(doc_id) == {"*"}:
            doc_id = _doc_id_from_url(doc_url)
        if not doc_id and not doc_url:
            continue
        create_time = int(meta.get("create_time") or 0)
        if min_create_time is not None and create_time < min_create_time:
            continue
        candidate_title = _strip_highlight_markup(item.get("title_highlighted") or item.get("title") or "")
        exact = candidate_title == normalized_title
        score = (
            1 if exact else 0,
            int(meta.get("update_time") or 0),
            create_time,
        )
        if best is None or score > best_score:
            best = {"doc_id": doc_id, "doc_url": doc_url}
            best_score = score
    return best or {}



def _search_docs(title: str) -> dict:
    return _run_json_command(_lark_cli_cmd() + ["docs", "+search", "--as", "user", "--query", title])



def _resolve_doc_reference(
    create_payload: dict,
    title: str,
    search_fn,
    *,
    retries: int = DEFAULT_SEARCH_RETRIES,
    delay_seconds: float = DEFAULT_SEARCH_DELAY_SECONDS,
    min_create_time: int | None = None,
) -> dict:
    data = (create_payload or {}).get("data") or {}
    doc_id = (data.get("doc_id") or data.get("document_id") or "").strip()
    doc_url = (data.get("doc_url") or data.get("url") or "").strip()
    if doc_id or doc_url:
        return {"doc_id": doc_id, "doc_url": doc_url}

    for attempt in range(max(1, retries)):
        search_payload = search_fn(title)
        resolved = _select_best_search_result(search_payload, title, min_create_time=min_create_time)
        if resolved:
            return resolved
        if attempt < retries - 1 and delay_seconds:
            time.sleep(delay_seconds)

    status = (data.get("status") or "").strip()
    task_id = (data.get("task_id") or "").strip()
    raise SystemExit(
        f"Unable to resolve created doc for title '{title}'. create status={status or 'unknown'} task_id={task_id or 'n/a'}"
    )



def _fetch_doc(doc_ref: str) -> str:
    proc = subprocess.run(
        _lark_cli_cmd() + ["docs", "+fetch", "--as", "user", "--doc", doc_ref, "--format", "pretty"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout



def publish_article(
    url: str,
    *,
    folder_token: str | None = None,
    proxy_country: str = "hk",
    timeout_seconds: int = 240,
    wait_ms: int = 8000,
    search_retries: int = DEFAULT_SEARCH_RETRIES,
    search_delay_seconds: float = DEFAULT_SEARCH_DELAY_SECONDS,
) -> dict:
    _progress("Fetching article via BrowserUse")
    article = _run_fetch(
        url,
        include_images=True,
        proxy_country=proxy_country,
        timeout_seconds=timeout_seconds,
        wait_ms=wait_ms,
    )
    title = _normalize_title(article.get("title") or "")
    body = _clean_body(article.get("content_markdown") or "", url)

    _progress("Importing Markdown into Feishu doc")
    with tempfile.TemporaryDirectory(prefix="wechat-browseruse-") as tmp_dir:
        markdown_file = Path(tmp_dir) / "article.md"
        markdown_file.write_text(body, encoding="utf-8")
        created = _import_doc_file(markdown_file, title, folder_token=folder_token)

    data = created.get("data") or {}
    resolved = {
        "doc_id": (data.get("token") or data.get("doc_id") or "").strip(),
        "doc_url": (data.get("url") or data.get("doc_url") or "").strip(),
    }
    doc_ref = resolved.get("doc_url") or resolved.get("doc_id") or ""
    _progress("Fetching created doc for verification")
    preview = _fetch_doc(doc_ref) if doc_ref else ""

    return {
        "title": title,
        "doc_id": resolved.get("doc_id") or "",
        "doc_url": resolved.get("doc_url") or "",
        "source_url": url,
        "validated": bool(preview.strip()),
        "doc_preview": preview[:1200],
        "create_response": created,
    }



def main() -> int:
    fetch_module = _load_fetch_module()
    parser = argparse.ArgumentParser(description="Fetch a WeChat article via BrowserUse and publish it to a native Feishu doc")
    parser.add_argument("url", help="WeChat article URL")
    parser.add_argument("--folder-token", default=None, help="Optional target Feishu folder token")
    parser.add_argument("--json", action="store_true", default=False, help="Print JSON result")
    parser.add_argument("--proxy-country", default=fetch_module.DEFAULT_PROXY_COUNTRY)
    parser.add_argument("--timeout-seconds", type=int, default=fetch_module.DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--wait-ms", type=int, default=fetch_module.DEFAULT_WAIT_MS)
    parser.add_argument("--search-retries", type=int, default=DEFAULT_SEARCH_RETRIES)
    parser.add_argument("--search-delay-seconds", type=float, default=DEFAULT_SEARCH_DELAY_SECONDS)
    args = parser.parse_args()

    result = publish_article(
        args.url,
        folder_token=args.folder_token,
        proxy_country=args.proxy_country,
        timeout_seconds=args.timeout_seconds,
        wait_ms=args.wait_ms,
        search_retries=args.search_retries,
        search_delay_seconds=args.search_delay_seconds,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["doc_url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
