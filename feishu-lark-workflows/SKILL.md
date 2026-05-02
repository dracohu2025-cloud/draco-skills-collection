---
name: feishu-lark-workflows
description: Use when working with Feishu/Lark native documents, Drive uploads, Bitable schema discovery, Bitable record writes, and lark-cli setup/validation.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [lark-cli]
metadata:
  hermes:
    tags: [feishu, lark, bitable, docs, drive, productivity]
---

# Feishu / Lark Workflows

## Overview

A routing skill for Feishu/Lark automation: native docs, Drive uploads, Bitable schema discovery, record writes, and CLI setup validation.

Use this skill whenever a task mentions Feishu, Lark, 飞书, 多维表, Bitable, Drive, native docs, or `lark-cli`.

## Core Routes

| Route | Use When |
|---|---|
| Native docs | Create or fetch real Feishu/Lark documents |
| Drive upload | Upload local files and resolve openable URLs |
| Bitable metadata | Inspect fields before writing records |
| Bitable sync | Create/update records with correct field shapes |
| CLI setup | Validate `lark-cli` auth and scopes |

## Common Commands

```bash
lark-cli auth status
lark-cli auth scopes
lark-cli docs +create --as user --title '<TITLE>' --markdown '<MARKDOWN>'
lark-cli docs +fetch --as user --doc '<DOC_URL>' --format pretty
lark-cli api GET "/open-apis/bitable/v1/apps/<BASE_TOKEN>/tables/<TABLE_ID>/fields?page_size=100" --as user
```

## Bitable Rules

- Inspect field metadata before writing.
- URL fields often require `{link, text}`.
- Attachment fields usually require upload first, then field update.
- Do not assume wrapper commands support every field shape; direct `bitable/v1` calls are often clearer.

## Verification Checklist

- [ ] `lark-cli` is installed
- [ ] `lark-cli auth status` passes
- [ ] Target workspace/base/table IDs are known
- [ ] Field types are checked before writes
- [ ] Returned tokens are resolved to user-openable URLs
