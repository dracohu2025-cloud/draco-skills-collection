#!/usr/bin/env python3
import argparse
import importlib.util
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"


def _load_module(filename: str, module_name: str):
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Unable to load script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BrowserUse 版微信公众号文章抓取与飞书文档发布统一入口"
    )
    subparsers = parser.add_subparsers(dest="command")

    fetch_parser = subparsers.add_parser("fetch", help="抓取公众号文章，输出 Markdown 或 JSON")
    fetch_parser.add_argument("url", help="微信公众号文章 URL")
    fetch_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    fetch_parser.add_argument("--include-images", action="store_true", default=False)
    fetch_parser.add_argument("--save", default=None, help="可选输出文件路径")
    fetch_parser.add_argument("--proxy-country", default=None, help="BrowserUse 代理国家码")
    fetch_parser.add_argument("--timeout-seconds", type=int, default=None)
    fetch_parser.add_argument("--wait-ms", type=int, default=None)

    publish_parser = subparsers.add_parser("publish-feishu", help="抓取公众号文章并发布为飞书原生文档")
    publish_parser.add_argument("url", help="微信公众号文章 URL")
    publish_parser.add_argument("--folder-token", default=None, help="目标飞书文件夹 token")
    publish_parser.add_argument("--json", action="store_true", default=False, help="输出完整 JSON 结果")
    publish_parser.add_argument("--proxy-country", default=None, help="BrowserUse 代理国家码")
    publish_parser.add_argument("--timeout-seconds", type=int, default=None)
    publish_parser.add_argument("--wait-ms", type=int, default=None)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    fetch_module = _load_module("fetch_wechat_article.py", "wechat_article_browseruse_fetch")

    if args.command == "fetch":
        result = fetch_module.fetch_article(
            args.url,
            include_images=args.include_images,
            proxy_country=args.proxy_country or fetch_module.DEFAULT_PROXY_COUNTRY,
            timeout_seconds=args.timeout_seconds or fetch_module.DEFAULT_TIMEOUT_SECONDS,
            wait_ms=args.wait_ms or fetch_module.DEFAULT_WAIT_MS,
        )
        rendered = result["content_markdown"] if args.format == "markdown" else json.dumps(result, ensure_ascii=False, indent=2)
        if args.save:
            out = Path(args.save).expanduser().resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(rendered, encoding="utf-8")
        print(rendered)
        return 0

    publish_module = _load_module("publish_wechat_article_to_feishu.py", "wechat_article_browseruse_publish")
    result = publish_module.publish_article(
        args.url,
        folder_token=args.folder_token,
        proxy_country=args.proxy_country or fetch_module.DEFAULT_PROXY_COUNTRY,
        timeout_seconds=args.timeout_seconds or fetch_module.DEFAULT_TIMEOUT_SECONDS,
        wait_ms=args.wait_ms or fetch_module.DEFAULT_WAIT_MS,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["doc_url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
