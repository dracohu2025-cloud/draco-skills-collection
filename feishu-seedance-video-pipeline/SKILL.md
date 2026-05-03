---
name: feishu-seedance-video-pipeline
description: "Use when running a Feishu/Lark Base-centered Seedance video production pipeline: manage the Base row as the source of truth, prepare assets, build Row-24-style Chinese prompts, submit/poll/download Seedance videos, QA results, and backfill lineage, tokens, and cost."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [feishu, lark, bitable, seedance, video-generation, asset-lineage, qa]
---

# Feishu + Seedance Video Pipeline

## Overview

Use this skill when the real workflow is not merely “call Seedance once”, but a production line:

```text
Feishu/Lark Base row
→ story brief and asset ledger
→ character / scene / action references
→ Seedance-ready prompt and payload
→ billable generation
→ download, QA, transcript if needed
→ tokens, estimated cost, media, and lineage backfilled into Base
```

The Base row is the source of truth. Seedance is the video engine.

## When to Use

Use when:

- A user gives a Feishu/Lark Base row and asks to prepare, generate, repair, or QA a Seedance video.
- The task mentions “row N”, “Base”, “Bitable”, “asset management”, “backfill”, “Prompt_Output_Map”, “Task ID”, “tokens”, or “cost”.
- A generated video must remain auditable: exact prompt, payload, references, output, QA, and cost are all recorded.

Do not use when:

- The user only wants creative ideation with no Base row or production tracking.
- The user explicitly wants a different project management system.
- The task is pure low-level API troubleshooting. You may still reference the API section.

## Defaults

- Model: `doubao-seedance-2-0-fast-260128`.
- Use `doubao-seedance-2-0-260128` only when the user explicitly asks for Standard, quality-priority, or A/B comparison.
- Resolution: `480p` by default to control cost.
- Prompt language: full Chinese prompt by default for Chinese short-drama work.
- Default visual style when no other style is specified: Shao Brothers-inspired cinematic realism, Chinese period studio-set texture, martial-arts comedy energy, warm practical lighting, readable rich camera.
- Never submit a billable Seedance POST without explicit user confirmation.
- Always report tokens and estimated CNY cost after a successful task.

## Base Row as Source of Truth

A complete row should answer:

- What story/script was used?
- Which references were sent to Seedance, in what `content[]` order?
- Which tool/model/prompt produced each reference asset?
- What exact text prompt did Seedance receive?
- What payload, model, duration, ratio, resolution, and audio setting were used?
- What task ID, output video, contact sheet, transcript, QA result, tokens, and cost were produced?
- Which files are human-review attachments and which URLs/asset URIs are API inputs?

Typical fields vary by table. Always run field discovery first. Common field meanings include:

```text
Character Reference Sheet tool / prompt / attachment / URL
Scene, Environment, and Settings reference image tool / prompt / attachment / URL
Top-Down Blocking Map or keyframe reference tool / prompt / attachment
Prompt
Seedance video prompt
Payload file
Reference URLs
Prompt_Output_Map
Planned parameters
Task ID
Output video
Quality review contact sheet
QA summary
Tokens
Estimated cost CNY
Local path
Status
```

## Workflow

### 1. Inspect the row

```bash
BASE='<BASE_TOKEN>'
TABLE='<TABLE_ID>'
REC='<RECORD_ID>'
WORK=/tmp/feishu_seedance_pipeline
mkdir -p "$WORK"

lark-cli base +field-list --as user \
  --base-token "$BASE" --table-id "$TABLE" \
  > "$WORK/fields.json"

lark-cli base +record-get --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  > "$WORK/record.json"
```

Read `data.record`. Do not assume every CLI response uses `data.record.fields`.

### 2. Prepare references

Character Reference Sheet:

- One main character per sheet unless the user requests a cast sheet.
- Use clean readable boards; avoid scene backgrounds, watermarks, logos, fake text, and extra characters.
- If the sheet has multiple panels, the video prompt must state that all panels describe the same character and that labels/layout must not appear in the final video.

Scene, Environment, and Settings reference image:

- Locks environment, lighting, spatial anchor, material palette, and key props.
- Usually should not include main characters, readable text, signs, labels, arrows, or storyboard panels.
- Use one coherent 16:9 cinematic frame.

Action / blocking / keyframe reference:

- Use only when spatial continuity, contact, or timing matters.
- Prefer low-noise references for Seedance. Avoid dense labels, arrows, grids, and repeated characters.
- Write full names in model-facing prompts: `Character Reference Sheet`, `Scene, Environment, and Settings reference image`, `Top-Down Blocking Map`.

### 3. Publish references

Seedance needs public HTTPS URLs or supported `asset://...` URIs.

For local static hosting, use placeholders in public documentation:

```bash
PUBLIC_DIR=/var/www/<your-domain>/media/seedance
PUBLIC_URL="https://<your-domain>/media/seedance/reference.png"
```

For Feishu attachments, upload from the file directory and pass a relative filename:

```bash
cd /path/to/files
lark-cli base +record-upload-attachment --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  --field-id '<ATTACHMENT_FIELD_NAME_OR_ID>' \
  --file reference.png
```

### 4. Build the Row-24-style Seedance prompt

A weak prompt only describes plot. A production prompt binds plot to camera, spatial continuity, props, and audio.

Required structure:

1. Overall hard constraints: duration, ratio, resolution, audio, visible cast count, identity/outfit locks.
2. Style lock: default Shao Brothers-style cinematic realism unless the user specifies another style.
3. Reference usage by `content[]` order. Never write `@Image1`.
4. Spatial constraints: left/right positions, entrances/exits, final positions, stable anchors.
5. Prop/object state: initial state, state changes, forbidden inherited props.
6. Timeline: every segment includes shot size/composition, movement or cut, spatial anchor, action, expression, dialogue/sound.
7. Audio: exact dialogue lines when `generate_audio=true`.
8. Restrictions: no subtitles, speech bubbles, visible text, labels, arrows, watermark, duplicate characters, identity drift, prop drift.

Timeline pattern:

```text
[0-2秒] 镜头构图与运镜：中广角建立镜头，镜头围绕桌面空间锚点轻轻推近。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
[2-4秒] 镜头构图与运镜：切到中近景，保持角色左右关系不变。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
```

Before payload:

```text
Prompt == Seedance video prompt == payload.content[0].text == local prompt file
No @Image syntax
No unexplained internal shorthand
Every timeline block includes camera language
Model is Fast unless explicitly overridden
No billable submission yet
```

### 5. Build payload

```json
{
  "model": "doubao-seedance-2-0-fast-260128",
  "duration": 12,
  "resolution": "480p",
  "ratio": "16:9",
  "generate_audio": true,
  "return_last_frame": false,
  "content": [
    {"type": "text", "text": "..."},
    {"type": "image_url", "image_url": {"url": "https://example.com/reference.png"}, "role": "reference_image"}
  ]
}
```

Supported content examples:

```json
{"type":"image_url","image_url":{"url":"https://example.com/ref.png"},"role":"reference_image"}
{"type":"image_url","image_url":{"url":"asset://<ASSET_ID>"},"role":"reference_image"}
{"type":"image_url","image_url":{"url":"https://example.com/first.png"},"role":"first_frame"}
{"type":"image_url","image_url":{"url":"https://example.com/last.png"},"role":"last_frame"}
```

### 6. Pre-submit Base gate

Before any billable POST:

- Target row exists.
- Prompt file and payload file are saved.
- All known asset prompts/tools/attachments/URLs are filled or marked not used.
- Planned parameters include model, duration, ratio, resolution, audio, and reference order.
- `Prompt_Output_Map` draft is present.
- Only post-generation fields remain empty: task ID, final video, contact sheet, final QA, transcript, tokens, cost.
- Re-read with `record-get`.
- User explicitly confirms generation.

### 7. Submit and poll safely

```bash
curl -sS -X POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks \
  -H "Authorization: Bearer ${VOLCENGINE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @payload.json | tee post_response.json | jq .
```

Persist the task ID immediately. If a script times out or output is interrupted, inspect `post_response.json` and saved task IDs before doing anything else. Duplicate POSTs burn money.

Poll by task ID only:

```bash
TASK_ID='cgt-...'
curl --max-time 30 -sS "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/${TASK_ID}" \
  -H "Authorization: Bearer ${VOLCENGINE_API_KEY}" \
  | tee result_latest.json | jq '{status, usage, error, content}'
```

### 8. Download and QA

Use `ffprobe` for real media facts:

```bash
ffprobe -v error \
  -show_entries stream=index,codec_type,width,height,duration,nb_frames,r_frame_rate,codec_name \
  -of json output.mp4 > ffprobe.json
```

Create a contact sheet:

```bash
ffmpeg -y -hide_banner -loglevel error -i output.mp4 \
  -vf "fps=1,scale=240:-1,tile=5x3" -frames:v 1 contact_sheet.jpg
```

If dialogue matters, extract and transcribe audio:

```bash
ffmpeg -y -hide_banner -loglevel error -i output.mp4 -vn -ac 1 -ar 16000 audio.wav
whisper audio.wav --language Chinese --model tiny --output_dir whisper --output_format txt --fp16 False
```

QA summary should cover:

- width, height, fps, duration, audio stream
- character identity stability
- spatial continuity and prop state
- required action beats
- subtitle/text/watermark contamination
- duplicate or extra characters
- dialogue transcription if applicable
- tokens and estimated cost
- verdict: baseline / candidate / reject

### 9. Estimate cost

```bash
TOKENS=$(jq -r '.usage.total_tokens // .usage.completion_tokens' result_final.json)
MODEL=$(jq -r '.model // "doubao-seedance-2-0-fast-260128"' payload.json)
HAS_VIDEO=$(jq '[.content[]? | select(.type == "video_url")] | length > 0' payload.json)
python3 - <<PY
tokens = int("$TOKENS")
model = "$MODEL"
has_video = "$HAS_VIDEO" == "true"
rate = 22 if ("fast" in model and has_video) else 37 if "fast" in model else 28 if has_video else 46
print(f"tokens={tokens:,}")
print(f"estimated_cost_cny={tokens * rate / 1_000_000:.2f}")
PY
```

Typical public-rate assumptions:

- Seedance 2.0 Fast: about 37 CNY / 1M tokens without video input; about 22 CNY / 1M tokens with video input.
- Seedance 2.0 Standard: about 46 CNY / 1M tokens without video input; about 28 CNY / 1M tokens with video input.

### 10. Backfill and verify

For `lark-cli base +record-batch-update`, use:

```json
{"record_id_list":["<RECORD_ID>"],"patch":{"Prompt":"...","QA摘要":"..."}}
```

Then re-read:

```bash
lark-cli base +record-get --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  > "$WORK/verify_record.json"
```

Only report completion after the intended fields are present.

## Official `asset://` Human Rules

- Use official or authorized assets as `asset://<ASSET_ID>` URLs inside `content[]`.
- Do not write the asset ID as the character name in the prompt.
- Explain the reference by content order: “the first reference_image item is the official virtual human asset for face, hairstyle, age, body proportions, and expression”.
- Outfit changes via text may be ignored if the official asset strongly locks clothing. Warn the user before submission.
- If a role uses `asset://...`, do not also upload a self-generated Character Reference Sheet into that role’s input attachment field unless it is clearly marked as a non-input audit note.

## Security Rules

- Never expose or commit API keys, app secrets, access tokens, base tokens, table IDs from private workspaces, signed URLs, or raw `.env` files.
- Public examples must use placeholders such as `<BASE_TOKEN>`, `<TABLE_ID>`, `<RECORD_ID>`, `<ASSET_ID>`.
- Do not put tokens in Git remote URLs.
- Scan staged diffs before pushing.

## Common Pitfalls

1. Treating API generation and Base backfill as separate jobs. They are one pipeline.
2. Submitting short prompts that only describe plot. Use Row-24-style director prompts.
3. Timeline blocks without camera language.
4. Re-running submit scripts after a timeout. First check whether a task ID already exists.
5. Writing `@Image1` in API prompts. Bind by `content[]` order and role.
6. Miscounting Fast tasks with Standard pricing, or writing Standard in planned parameters while payload uses Fast.
7. Trying to clear Feishu attachment fields through unverified PATCH calls. They may append duplicates or be rejected.
8. Auto-regenerating after small defects or dialogue errors. Report the defect and cost, then ask for confirmation.
9. Publishing private IDs, signed URLs, local paths, or credentials.

## Verification Checklist

- [ ] Field list fetched.
- [ ] Target row re-read.
- [ ] References prepared or explicitly marked unused.
- [ ] Reference URLs or `asset://` URIs verified.
- [ ] Full Chinese Row-24-style prompt prepared when applicable.
- [ ] Payload saved with the intended model.
- [ ] Prompt, Base prompt field, payload text, and local prompt file match.
- [ ] Pre-submit Base gate passed.
- [ ] User confirmed billable generation.
- [ ] Task ID saved immediately.
- [ ] Poll/download used task ID only.
- [ ] ffprobe and contact sheet QA completed.
- [ ] Transcript generated when dialogue matters.
- [ ] Tokens and estimated cost recorded.
- [ ] Output video, contact sheet, QA, payload, prompt, and lineage backfilled.
- [ ] Final `record-get` verification passed.
- [ ] User-facing report contains no secrets.
