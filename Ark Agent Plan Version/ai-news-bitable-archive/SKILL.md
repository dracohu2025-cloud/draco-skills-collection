---
name: ai-news-bitable-archive
description: Use when parsing a Feishu/Lark native daily news document and syncing title, date, Top 3, summary, conclusion, document link, and status into Feishu Bitable.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3, lark-cli]
metadata:
  hermes:
    tags: [feishu, lark, bitable, docx, archive, news, cron]
---

# AI News → Feishu Bitable Archive

## Overview

This skill archives a Feishu/Lark native daily news document into a Bitable record.

It fetches the document, extracts standard daily-report fields, creates or updates a Bitable record, and prints the resulting `record_id`.

## When to Use

- A daily AI / Agent / AIGC report was published to Feishu/Lark Docs
- The report should be searchable in Bitable later
- You need idempotent create/update behavior by document token or date

## Entry Point

```bash
python3 scripts/sync_doc_to_bitable.py   --doc-url '<FEISHU_DOC_URL>'   --base-token '<FEISHU_BITABLE_BASE_TOKEN>'   --table-id '<FEISHU_BITABLE_TABLE_ID>'   --date 'YYYY-MM-DD'   --status '已归档'
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

## Bitable Notes

- URL fields often require `{link, text}`, not a raw string.
- The included script writes `文档链接` as `{link, text}`.
- Check field names/types before first use.

## Verification Checklist

- [ ] `lark-cli auth status` works
- [ ] Target base/table IDs are correct
- [ ] Script returns `record_id`
- [ ] Record can be read back by `record_id`
