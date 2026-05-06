---
name: ai-news-bitable-archive-dingtalk
description: Use when parsing a DingTalk daily news document and syncing title, date, Top 3, summary, conclusion, document link, and status into a DingTalk multidimensional table. 钉钉专用版。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - dingtalk
    - dws
    - aitable
    - archive
    - news
    - cron
---
# AI News → DingTalk Multidimensional Table Archive (DingTalk Edition)

## Overview

This skill archives a DingTalk daily news document into a multidimensional table record. It fetches the document, extracts standard daily-report fields, creates or updates a multidimensional table record, and prints the resulting `record_id`.

## When to Use

- A daily AI / Agent / AIGC report was published to DingTalk Docs
- The report should be searchable in the multidimensional table later
- You need idempotent create/update behavior by document token or date

## Input Source: Read DingTalk Doc

```bash
dws doc read --node '<DOC_ID_OR_URL>' --format json
```

Extract `content` from the JSON response.

## Archive Target: DingTalk Multidimensional Table

Use the DingTalk-specific archive script:

```bash
python3 scripts/sync_doc_to_dingtable.py \
  --doc-url '<DINGTALK_DOC_URL>' \
  --base-id '<DINGTALK_BASE_ID>' \
  --table-id '<DINGTALK_TABLE_ID>' \
  --date 'YYYY-MM-DD' \
  --status '已归档'
```

The script:
1. Reads the DingTalk doc via `dws doc read`
2. Parses the standard fields (标题, 日期, Top1-3, 一句话结论, 摘要)
3. Obtains the multidimensional table schema via `dws aitable table get`
4. Maps field names to fieldIds
5. Checks for existing records by 文档Token or 日期 (idempotent create/update)
6. Writes via `dws aitable record create` or `dws aitable record update`
7. Outputs `record_id`, mode (create/update), title, date, doc_url, and aitable_url

## Validate Archived Record

```bash
dws aitable record query \
  --base-id '<DINGTALK_BASE_ID>' \
  --table-id '<DINGTALK_TABLE_ID>' \
  --record-ids '<RECORD_ID>' \
  --format json
```

Verify fields: 标题, 文档链接, 文档Token, 统计窗口, Top1-3, 一句话结论, 摘要, 状态.

## Inspect Table Schema (when needed)

```bash
dws aitable table get --base-id '<DINGTALK_BASE_ID>' --table-id '<DINGTALK_TABLE_ID>' --format json
```

DingTalk multidimensional table URLs follow this format:

```text
https://alidocs.dingtalk.com/i/nodes/{baseId}
```

## Entry Point

```bash
python3 scripts/sync_doc_to_dingtable.py \
  --doc-url 'https://alidocs.dingtalk.com/i/nodes/<NODE_ID>' \
  --base-id '<DINGTALK_BASE_ID>' \
  --table-id '<DINGTALK_TABLE_ID>' \
  --date 'YYYY-MM-DD' \
  --status '已归档'
```

## Parsed Fields

- 标题
- 日期
- 文档链接
- 文档Token
- 统计窗口
- Top1 / Top2 / Top3
- 一句话结论
- 摘要
- 状态

## Multidimensional Table Notes

- DingTalk multidimensional table uses fieldId as cell keys, not field names.
- The included script `sync_doc_to_dingtable.py` automatically maps field names to fieldIds.
- Check field names/types before first use via `dws aitable table get`.

## Verification Checklist

- [ ] `dws doc read` works
- [ ] Target base/table IDs are correct
- [ ] Script returns `record_id`
- [ ] Record can be read back by `record_id` via `dws aitable record query`
