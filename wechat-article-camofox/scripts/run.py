#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FETCH_SCRIPT = ROOT / "scripts" / "fetch_wechat_article.py"
PUBLISH_SCRIPT = ROOT / "scripts" / "publish_wechat_article_to_feishu.py"


def _run(script: Path, extra_args: list[str]) -> int:
    proc = subprocess.run([sys.executable, str(script), *extra_args])
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="微信公众号文章抓取与飞书发布统一入口",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="抓取公众号文章为 Markdown 或 JSON")
    fetch_parser.add_argument("url", help="公众号文章链接，例如 https://mp.weixin.qq.com/s/xxxx")
    fetch_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    fetch_parser.add_argument("--include-images", action="store_true", default=False)
    fetch_parser.add_argument("--save", default=None, help="可选：保存到本地文件")

    publish_parser = subparsers.add_parser("publish-feishu", help="抓取公众号文章并发布到飞书原生文档")
    publish_parser.add_argument("url", help="公众号文章链接，例如 https://mp.weixin.qq.com/s/xxxx")
    publish_parser.add_argument("--json", action="store_true", default=False, help="输出 JSON 结果而不是只打印 doc_url")

    args = parser.parse_args()

    if args.command == "fetch":
        extra = [args.url, "--format", args.format]
        if args.include_images:
            extra.append("--include-images")
        if args.save:
            extra.extend(["--save", args.save])
        return _run(FETCH_SCRIPT, extra)

    if args.command == "publish-feishu":
        extra = [args.url]
        if args.json:
            extra.append("--json")
        return _run(PUBLISH_SCRIPT, extra)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
