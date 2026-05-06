#!/usr/bin/env python3
"""DingTalk 版日报归档脚本：解析钉钉文档 → 写入钉钉多维表。

用法:
    python3 sync_doc_to_dingtable.py \
      --doc-url 'https://alidocs.dingtalk.com/i/nodes/<NODE_ID>' \
      --base-id '<DINGTALK_BASE_ID>' \
      --table-id '<DINGTALK_TABLE_ID>' \
      --date 'YYYY-MM-DD' \
      --status '已归档'
"""
import argparse
import json
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional


def run(args: List[str]) -> Any:
    """执行 dws 命令并返回 JSON 解析结果。"""
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.strip() or proc.stdout.strip() or f'命令失败: {args}'
        )
    text = proc.stdout.strip()
    try:
        return json.loads(text)
    except Exception:
        return text


def extract_node_id(doc_url: str) -> str:
    """从钉钉文档 URL 中提取 nodeId。"""
    m = re.search(r'/i/nodes/([A-Za-z0-9]+)', doc_url)
    if not m:
        raise ValueError(f'无法从 URL 提取 nodeId: {doc_url}')
    return m.group(1)


def fetch_doc(doc_url: str) -> str:
    """读取钉钉文档内容。"""
    node_id = extract_node_id(doc_url)
    result = run(['dws', 'doc', 'read', '--node', node_id, '--format', 'json'])
    if isinstance(result, dict):
        return result.get('markdown', result.get('content', ''))
    return str(result)


def get_table_schema(base_id: str, table_id: str) -> Dict[str, str]:
    """获取多维表字段映射：fieldName → fieldId。"""
    result = run([
        'dws', 'aitable', 'table', 'get',
        '--base-id', base_id,
        '--table-id', table_id,
        '--format', 'json',
    ])
    # fields 在 data.tables[0].fields 层级
    tables = result.get('data', {}).get('tables', [])
    fields = tables[0].get('fields', []) if tables else result.get('fields', [])
    return {f['fieldName']: f['fieldId'] for f in fields}


def parse_doc(doc_text: str, explicit_date: Optional[str] = None) -> Dict[str, str]:
    """解析日报文档，提取各字段。"""
    lines = doc_text.splitlines()
    title = next((l[2:].strip() for l in lines if l.startswith('# ')), '')
    window = next(
        (l.replace('统计窗口：', '').strip() for l in lines if l.startswith('统计窗口：')),
        '',
    )

    section = re.search(r'## 最值得注意的 3 条\n(.*?)(?:\n## |\Z)', doc_text, re.S)
    tops: List[str] = []
    if section:
        tops = [
            m.strip()
            for m in re.findall(
                r'^###\s+\d+[\.）)]\s*(.+)$', section.group(1), re.M
            )
        ]

    conclusion = ''
    m = re.search(r'## 一句话结论\n\n(.+)', doc_text, re.S)
    if m:
        conclusion = re.sub(r'\s+', ' ', m.group(1).strip())

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


def list_records(base_id: str, table_id: str) -> List[Dict[str, Any]]:
    """查询多维表中已有记录。"""
    all_records = []
    cursor = None
    while True:
        cmd = [
            'dws', 'aitable', 'record', 'query',
            '--base-id', base_id,
            '--table-id', table_id,
            '--limit', '100',
            '--format', 'json',
        ]
        if cursor:
            cmd.extend(['--cursor', cursor])
        result = run(cmd)
        records = result.get('records', [])
        all_records.extend(records)
        cursor = result.get('nextCursor') or result.get('cursor')
        if not cursor:
            break
    return all_records


def write_record(
    base_id: str,
    table_id: str,
    record_id: Optional[str],
    cells: Dict[str, str],
) -> Dict[str, Any]:
    """创建或更新多维表记录。"""
    if record_id:
        result = run([
            'dws', 'aitable', 'record', 'update',
            '--base-id', base_id,
            '--table-id', table_id,
            '--records', json.dumps(
                [{'recordId': record_id, 'cells': cells}], ensure_ascii=False
            ),
            '--format', 'json',
        ])
    else:
        result = run([
            'dws', 'aitable', 'record', 'create',
            '--base-id', base_id,
            '--table-id', table_id,
            '--records', json.dumps(
                [{'cells': cells}], ensure_ascii=False
            ),
            '--format', 'json',
        ])
    # 处理不同的响应格式
    records = result.get('records', [])
    if records:
        return records[0]
    # AI 表格的 create 响应格式：data.newRecordIds
    new_ids = result.get('data', {}).get('newRecordIds', [])
    if new_ids:
        return {'recordId': new_ids[0]}
    raise RuntimeError(f'写入记录失败: {result}')


def main() -> int:
    ap = argparse.ArgumentParser(description='钉钉日报归档到多维表')
    ap.add_argument('--doc-url', required=True, help='钉钉文档链接')
    ap.add_argument('--base-id', required=True, help='钉钉多维表 Base ID')
    ap.add_argument('--table-id', required=True, help='钉钉多维表 Table ID')
    ap.add_argument('--date', default='', help='日期 YYYY-MM-DD')
    ap.add_argument('--status', default='已归档', help='归档状态')
    args = ap.parse_args()

    # 1. 读取文档内容
    doc_text = fetch_doc(args.doc_url)
    node_id = extract_node_id(args.doc_url)

    # 2. 解析文档字段
    fields = parse_doc(doc_text, args.date or None)
    fields['文档链接'] = args.doc_url
    fields['文档Token'] = node_id
    fields['状态'] = args.status

    # 3. 获取多维表字段映射
    schema = get_table_schema(args.base_id, args.table_id)

    # 4. 将字段名映射为 fieldId，构建 cells
    cells = {}
    for field_name, value in fields.items():
        fid = schema.get(field_name)
        if fid:
            cells[fid] = value

    # 5. 查重：按文档Token 或 日期 找已有记录
    existing = list_records(args.base_id, args.table_id)
    target = None
    token_fid = schema.get('文档Token')
    date_fid = schema.get('日期')
    for item in existing:
        f = item.get('cells', {}) or {}
        if token_fid and f.get(token_fid) == node_id:
            target = item['recordId']
            break
    if not target:
        for item in existing:
            f = item.get('cells', {}) or {}
            if date_fid and fields['日期'] and f.get(date_fid) == fields['日期']:
                target = item['recordId']
                break

    # 6. 写入记录
    result = write_record(args.base_id, args.table_id, target, cells)

    out = {
        'mode': 'update' if target else 'create',
        'record_id': result.get('recordId', ''),
        'title': fields['标题'],
        'date': fields['日期'],
        'doc_url': args.doc_url,
        'aitable_url': f"https://alidocs.dingtalk.com/i/nodes/{args.base_id}",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())