#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FETCH_SCRIPT = PROJECT_ROOT / 'scripts' / 'fetch_wechat_article.py'


def _run_fetch(url: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(FETCH_SCRIPT), url, '--format', 'json', '--include-images'],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def _normalize_title(title: str) -> str:
    title = (title or '').strip()
    title = re.sub(r'\\+$', '', title).strip()
    return title or '微信公众号文章抓取结果'


def _clean_body(markdown: str, original_url: str) -> str:
    lines = (markdown or '').splitlines()
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    body = '\n'.join(lines).strip()
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = f'> 原文链接：{original_url}\n\n' + body
    return body.strip() + '\n'


def _create_doc(title: str, body: str) -> dict:
    proc = subprocess.run(
        ['lark-cli', 'docs', '+create', '--as', 'user', '--title', title, '--markdown', body],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def _fetch_doc(doc_id: str) -> str:
    proc = subprocess.run(
        ['lark-cli', 'docs', '+fetch', '--as', 'user', '--doc', doc_id, '--format', 'pretty'],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description='Fetch a WeChat article and publish it to a native Feishu doc')
    parser.add_argument('url', help='WeChat article URL')
    parser.add_argument('--json', action='store_true', default=False, help='Print JSON result')
    args = parser.parse_args()

    article = _run_fetch(args.url)
    title = _normalize_title(article.get('title', ''))
    body = _clean_body(article.get('content_markdown', ''), args.url)
    created = _create_doc(title, body)
    data = created.get('data', {})
    doc_id = data.get('doc_id', '')
    preview = _fetch_doc(doc_id) if doc_id else ''

    result = {
        'title': title,
        'doc_id': doc_id,
        'doc_url': data.get('doc_url', ''),
        'source_url': args.url,
        'validated': bool(preview.strip()),
        'doc_preview': preview[:1200],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result['doc_url'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
