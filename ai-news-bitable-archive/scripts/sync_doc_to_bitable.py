#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional


def run(args: List[str]) -> Any:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f'command failed: {args}')
    text = proc.stdout.strip()
    try:
        return json.loads(text)
    except Exception:
        return text


def fetch_doc(doc_url: str) -> str:
    proc = subprocess.run(
        ['lark-cli', 'docs', '+fetch', '--as', 'user', '--doc', doc_url, '--format', 'pretty'],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'fetch failed')
    return proc.stdout


def parse_doc(doc_text: str, explicit_date: Optional[str] = None) -> Dict[str, str]:
    lines = doc_text.splitlines()
    title = next((l[2:].strip() for l in lines if l.startswith('# ')), '')
    window = next((l.replace('统计窗口：', '').strip() for l in lines if l.startswith('统计窗口：')), '')

    section = re.search(r'## 最值得注意的 3 条\n(.*?)(?:\n## |\Z)', doc_text, re.S)
    tops: List[str] = []
    if section:
        tops = [m.strip() for m in re.findall(r'^###\s+\d+[\.）)]\s*(.+)$', section.group(1), re.M)]

    conclusion = ''
    m = re.search(r'## 一句话结论\n\n(.+)', doc_text, re.S)
    if m:
        conclusion = re.sub(r'\s+', ' ', m.group(1).strip())

    token_match = re.search(r'/docx/([A-Za-z0-9]+)', doc_text)
    inferred_date = explicit_date
    if not inferred_date:
        dm = re.search(r'(20\d{2}-\d{2}-\d{2})', title)
        if dm:
            inferred_date = dm.group(1)

    return {
        '标题': title,
        '日期': inferred_date or '',
        '统计窗口': window,
        'Top1': tops[0] if len(tops) > 0 else '',
        'Top2': tops[1] if len(tops) > 1 else '',
        'Top3': tops[2] if len(tops) > 2 else '',
        '一句话结论': conclusion,
        '摘要': '；'.join(tops[:3]),
    }


def list_records(base_token: str, table_id: str) -> List[Dict[str, Any]]:
    data = run([
        'lark-cli', 'api', 'GET', f'/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records?page_size=500', '--as', 'user'
    ])
    return data['data'].get('items', [])


def write_record(base_token: str, table_id: str, record_id: Optional[str], fields: Dict[str, str]) -> Dict[str, Any]:
    payload = json.dumps({'fields': fields}, ensure_ascii=False)
    if record_id:
        return run([
            'lark-cli', 'api', 'PUT', f'/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records/{record_id}',
            '--as', 'user', '--data', payload,
        ])
    return run([
        'lark-cli', 'api', 'POST', f'/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records',
        '--as', 'user', '--data', payload,
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--doc-url', required=True)
    ap.add_argument('--base-token', required=True)
    ap.add_argument('--table-id', required=True)
    ap.add_argument('--date', default='')
    ap.add_argument('--status', default='已归档')
    args = ap.parse_args()

    doc_text = fetch_doc(args.doc_url)
    token_match = re.search(r'/docx/([A-Za-z0-9]+)', args.doc_url)
    doc_token = token_match.group(1) if token_match else ''
    fields = parse_doc(doc_text, args.date or None)
    fields['文档链接'] = {
        'link': args.doc_url,
        'text': args.doc_url,
    }
    fields['文档Token'] = doc_token
    fields['状态'] = args.status

    existing = list_records(args.base_token, args.table_id)
    target = None
    for item in existing:
        f = item.get('fields', {}) or {}
        if doc_token and f.get('文档Token') == doc_token:
            target = item['record_id']
            break
    if not target:
        for item in existing:
            f = item.get('fields', {}) or {}
            if fields['日期'] and f.get('日期') == fields['日期']:
                target = item['record_id']
                break

    result = write_record(args.base_token, args.table_id, target, fields)
    out = {
        'mode': 'update' if target else 'create',
        'record_id': result['data']['record']['record_id'],
        'title': fields['标题'],
        'date': fields['日期'],
        'doc_url': args.doc_url,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
