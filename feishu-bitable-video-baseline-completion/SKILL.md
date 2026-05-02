---
name: feishu-bitable-video-baseline-completion
description: Use when a Feishu/Lark Base row for an approved video baseline is missing upstream asset lineage, prompts, tools, URLs, or attachment fields; reconstruct and verify the full video asset map from existing source asset rows and local/public files.
version: 1.0.1
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [Feishu, Bitable, Video Generation, Baseline, Asset Lineage]
    related_skills: []
---

# Feishu Bitable Video Baseline Completion

## Overview

Backfill a completed or approved video-generation row in Feishu Base so it becomes a reliable baseline record.

The target row should contain enough information to reproduce, audit, compare, and review the version without hunting through old rows, chat history, local folders, or temporary files.

Typical missing pieces:

- Character Reference Sheet tool / prompt / image attachment
- Scene, Environment, and Settings reference image tool / prompt / image attachment
- public reference image URLs
- prompt / payload / output video / quality-review contact sheet mapping
- `Prompt_Output_Map`
- task id / seed / tokens / estimated cost summary

## When to Use

Use when:

- A user marks a video version as approved, qualified, accepted, or baseline.
- A Feishu Base video row has the output video but lacks upstream asset fields.
- Character Reference Sheet or Scene, Environment, and Settings reference fields are blank.
- The user asks why a row is missing tools, prompts, images, or asset lineage.
- A scattered media pipeline needs to be consolidated into one reviewable Base row.

Do not use when:

- The user is asking to generate a new video.
- The source assets do not exist yet.
- The task is only a narrative brief, not Base cleanup.

## Required Inputs

You need:

- `base_token` and `table_id` available locally or from prior context.
- Target video `record_id`.
- Source asset rows for all input assets used by the video payload, such as:
  - Character 1 Reference Sheet
  - Character 2 Reference Sheet
  - Character 3 Reference Sheet
  - Scene, Environment, and Settings reference image
  - keyframe / blocking / storyboard reference image if used
- Local or public files matching the reference URLs.

Never print or report real base tokens, table IDs, app tokens, API keys, or access tokens. Use `[REDACTED]` in user-facing summaries.

## Standard Field Pattern

Field names vary by project. Always run `field-list` before writing.

Common target fields:

```text
角色参考图（CRS）_角色1_工具
角色参考图（CRS）_角色1_Prompt
输入资产_角色1参考图

角色参考图（CRS）_角色2_工具
角色参考图（CRS）_角色2_Prompt
输入资产_角色2参考图

角色参考图（CRS）_角色3_工具
角色参考图（CRS）_角色3_Prompt
输入资产_角色3参考图

场景环境设定参考图（SES）_工具
场景环境设定参考图（SES）_Prompt
输入资产_场景环境设定参考图

关键帧参考图（Keyframes）_工具
关键帧参考图（Keyframes）_Prompt
输入资产_动作时序参考图

Prompt_Output_Map
Reference_URLs
视频生成_Prompt / Seedance视频_Prompt
视频生成 Payload文件 / Seedance Payload文件
Prompt文件
生成视频成片
质量检查抽帧图
QA摘要
视频生成_Tokens / Seedance视频_Tokens
视频生成_估算成本CNY / Seedance视频_估算成本CNY
视频生成_计划参数 / Seedance视频_计划参数
```

Base field headers may include local shorthand in parentheses. Model-facing prompt text should use full names, for example `Character Reference Sheet` and `Scene, Environment, and Settings reference image`.

## Workflow

### 1. Inspect target row and fields

```bash
BASE='[REDACTED]'
TABLE='[REDACTED]'
REC='rec...'
WORK=/tmp/video_baseline_completion
mkdir -p "$WORK"

lark-cli base +field-list --as user \
  --base-token "$BASE" --table-id "$TABLE" \
  > "$WORK/fields.json"

lark-cli base +record-get --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  > "$WORK/target_record.json"
```

Read `data.record`; do not assume `data.record.fields` exists.

```python
import json
r = json.load(open('/tmp/video_baseline_completion/target_record.json'))['data']['record']
for k, v in r.items():
    if v not in (None, '', []):
        print(k, str(v)[:300])
```

### 2. Locate source asset rows

Search existing Base records for source assets. Match by asset names, payload reference URLs, file names, hashes, and status; do not rely on memory alone.

Useful source row fields usually include:

- `资产类型`
- `工具`
- `模型`
- `Prompt`
- `Output_URL`
- `图片附件`
- `Local_Path`
- `Reference_URLs`

If source rows are unclear, inspect:

1. target row `Reference_URLs`
2. payload JSON
3. prompt file
4. local workspace path
5. public media directory
6. previous asset rows in the same Base

### 3. Verify file identity with hashes

Before uploading files into the target row, verify that local files match the payload/public reference assets.

```bash
python3 - <<'PY'
import hashlib, os
pairs = [
  ('/var/www/.../character_1_reference_sheet.png', '/tmp/.../source_character_1.png'),
]
for a, b in pairs:
    def h(p):
        return (hashlib.sha256(open(p,'rb').read()).hexdigest(), os.path.getsize(p)) if os.path.exists(p) else None
    print(a, h(a))
    print(b, h(b))
    print('same=', h(a) == h(b))
PY
```

If hashes differ, do not silently upload. Decide which file actually entered the video payload.

### 4. Upload attachment fields

Feishu CLI upload requires a safe relative file path from the current working directory. Do not pass absolute paths.

```bash
cd /path/to/reference/images

lark-cli base +record-upload-attachment --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  --field-id '输入资产_角色1参考图' \
  --file character_1_reference_sheet.png
```

Repeat for each Character Reference Sheet, Scene, Environment, and Settings reference image, keyframe reference, payload file, prompt file, output video, and quality-review artifact as needed.

### 5. Build text patch

Use `record-batch-update` with this JSON shape:

```json
{
  "record_id_list": ["rec..."],
  "patch": {
    "角色参考图（CRS）_角色1_工具": "Hermes image_generate / image model name",
    "角色参考图（CRS）_角色1_Prompt": "...",
    "Prompt_Output_Map": "..."
  }
}
```

Do not use `records: [{record_id, fields}]`; this CLI expects `record_id_list + patch`.

Recommended `Prompt_Output_Map` structure:

```text
Baseline video task completed.
Task ID: ...
Record ID: ...
Seed: ...
Tokens: ...
Estimated cost: ...
Actual media: width×height / fps / duration / audio

INPUT ASSET MAP — completed on YYYY-MM-DD HH:MM TZ

1. Character 1 Reference Sheet
Tool: ...
Model: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Source asset row: ...

2. Character 2 Reference Sheet
Tool: ...
Model: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Source asset row: ...

3. Character 3 Reference Sheet
Tool: ...
Model: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Source asset row: ...

4. Scene, Environment, and Settings reference image
Tool: ...
Model: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Source asset row: ...

Video output:
...

Payload / prompt / quality-review files are stored in the dedicated attachment fields on this same row.
```

### 6. Update record

```bash
JSON_ARG=$(python3 - <<'PY'
print(open('/tmp/video_baseline_completion/text_patch.json').read())
PY
)

lark-cli base +record-batch-update --as user \
  --base-token "$BASE" --table-id "$TABLE" \
  --json "$JSON_ARG" \
  > /tmp/video_baseline_completion/update_result.json
```

If rate-limited, sleep and retry. Do not assume failure until the target row is re-read.

### 7. Verify by re-reading target row

```bash
lark-cli base +record-get --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  > /tmp/video_baseline_completion/verify_record.json
```

Verification script:

```python
import json
r = json.load(open('/tmp/video_baseline_completion/verify_record.json'))['data']['record']
required = [
  '角色参考图（CRS）_角色1_工具',
  '角色参考图（CRS）_角色1_Prompt',
  '输入资产_角色1参考图',
  '角色参考图（CRS）_角色2_工具',
  '角色参考图（CRS）_角色2_Prompt',
  '输入资产_角色2参考图',
  '角色参考图（CRS）_角色3_工具',
  '角色参考图（CRS）_角色3_Prompt',
  '输入资产_角色3参考图',
  '场景环境设定参考图（SES）_工具',
  '场景环境设定参考图（SES）_Prompt',
  '输入资产_场景环境设定参考图',
  'Prompt_Output_Map',
]
missing = []
for k in required:
    v = r.get(k)
    ok = v not in (None, '', [])
    if not ok:
        missing.append(k)
    print(('OK  ' if ok else 'MISS'), k)
print('missing_count=', len(missing))
```

Only report completion when `missing_count=0` for the intended field set.

## Quality Rules

- Target video row remains the single source of truth for the approved baseline.
- Do not split active prompt / asset / video records unless they are clearly archival.
- Use full names in prompts and maps:
  - `Character Reference Sheet`
  - `Scene, Environment, and Settings reference image`
  - `Top-Down Blocking Map`
- Avoid internal abbreviations in model-facing text.
- Public URL fields should contain clean URLs only. Multi-line explanations belong in `Prompt_Output_Map` or notes, not URL-style fields.
- Attachment fields are for human review and Gallery views; public URLs are for API reproducibility.

## Security Rules

- Never expose real base tokens, table IDs, app secrets, API keys, access tokens, or signed URLs in chat, docs, cards, commits, or examples.
- If command output includes such identifiers, redact before reporting.
- Before any Git push involving this workflow, scan for credentials. Credentials are zero-tolerance.

## Common Pitfalls

1. **Uploading absolute paths to Feishu Base.** `record-upload-attachment` may reject unsafe absolute paths. `cd` into the directory and pass a relative filename.

2. **Trusting `record-list` after field changes.** It may show incomplete long fields. Use `record-get --record-id` for verification.

3. **Wrong batch update shape.** Use `{"record_id_list": [...], "patch": {...}}`.

4. **Assuming source asset row equals payload asset.** Check target `Reference_URLs`, payload JSON, and hashes.

5. **Losing the baseline distinction.** If the user approved a video, preserve that row. Backfill; do not overwrite with a new experimental asset unless explicitly asked.

6. **Printing sensitive identifiers.** Tool logs may contain base tokens or table IDs. User-facing summaries must omit or redact them.

## Verification Checklist

- [ ] Target video row identified by `record_id`.
- [ ] Field list fetched and field names confirmed.
- [ ] Source asset rows identified for each Character Reference Sheet and Scene reference.
- [ ] Public/local reference image files hash-checked against source assets or payload URLs.
- [ ] Attachment fields uploaded to the target row.
- [ ] Tool fields populated.
- [ ] Prompt fields populated.
- [ ] `Prompt_Output_Map` populated with asset lineage.
- [ ] Payload / prompt / output / quality-review fields left intact or improved.
- [ ] Re-read with `record-get`.
- [ ] Missing required fields count is 0.
- [ ] Final user summary contains no base token, table ID, or credential.
