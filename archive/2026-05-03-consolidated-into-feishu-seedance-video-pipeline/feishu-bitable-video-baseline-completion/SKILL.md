---
name: feishu-bitable-video-baseline-completion
description: "Use when producing, approving, or repairing a Feishu/Lark Base video baseline row end-to-end: generate Character Reference Sheet and Scene, Environment, and Settings reference image assets from proven prompt templates, build a Seedance-ready payload, QA the video, then backfill tools, prompts, URLs, attachments, cost, and Prompt_Output_Map into one auditable Base row."
version: 1.1.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [Feishu, Bitable, Video Generation, Baseline, Asset Lineage, Prompt Templates]
    related_skills: []
---

# Feishu Bitable Video Baseline Completion

## Overview

This skill turns a video idea or an already approved video into a complete Feishu Base baseline record.

It covers the whole baseline path:

```text
Brief
→ Character Reference Sheet prompts
→ Character Reference Sheet images
→ Scene, Environment, and Settings reference image prompt
→ Scene reference image
→ optional action / blocking reference
→ Seedance-ready video prompt and payload
→ video generation and QA
→ approved baseline row backfill
→ re-read verification
```

The final target is one Base row that is useful for humans and machines: it contains the video, prompts, payload, reference images, tools, public URLs, attachments, quality review, tokens, estimated cost, and `Prompt_Output_Map`.

## When to Use

Use when:

- A user wants to produce a video baseline with Feishu Base as the source of truth.
- A user marks a generated video version as approved, qualified, accepted, or baseline.
- A Base video row has the output video but lacks upstream assets, tools, prompts, attachments, URLs, or mapping.
- Character Reference Sheet or Scene, Environment, and Settings reference image assets need to be generated with reusable templates.
- A scattered media workflow needs to be consolidated into one reviewable Base row.

Do not use when:

- The task is only ideation with no media production or Base record.
- The user has not authorized a billable video generation step.
- The user explicitly wants a different project management system instead of Feishu Base.

## Core Principle

A baseline row is not just a video URL.

A proper baseline row answers:

- What visual references created this video?
- Which tool/model produced every reference asset?
- Which prompt produced every asset?
- Which reference image was sent into the video payload?
- What did the video model receive exactly?
- What did QA find?
- What seed, tokens, cost, duration, resolution, ratio, and audio setting were used?
- Which local/public files match the attachments?

## Required Inputs

Minimum inputs for a new end-to-end run:

- Feishu `base_token`, `table_id`, and either an existing target `record_id` or permission to create one.
- Story brief or approved script.
- Character list, one entry per main character.
- Scene/environment brief.
- Target video parameters: duration, ratio, resolution, audio setting.
- User confirmation before any billable video generation.

Minimum inputs for a repair/backfill run:

- Feishu `base_token`, `table_id`, target video `record_id`.
- Existing source asset rows, prompt files, payload files, public URLs, or local files.

Never print or report real base tokens, table IDs, app tokens, API keys, access tokens, signed URLs, or credentials. Use `[REDACTED]` in user-facing summaries.

## Standard Field Pattern

Field names vary by project. Always run `field-list` before writing.

Common target fields:

```text
角色参考图（CRS）_角色1_工具
角色参考图（CRS）_角色1_Prompt
输入资产_角色1参考图
角色1参考图_URL

角色参考图（CRS）_角色2_工具
角色参考图（CRS）_角色2_Prompt
输入资产_角色2参考图
角色2参考图_URL

角色参考图（CRS）_角色3_工具
角色参考图（CRS）_角色3_Prompt
输入资产_角色3参考图
角色3参考图_URL

场景环境设定参考图（SES）_工具
场景环境设定参考图（SES）_Prompt
输入资产_场景环境设定参考图
场景环境设定参考图_URL

动作参考图 / 关键帧参考图 / Top-Down Blocking Map_工具
动作参考图 / 关键帧参考图 / Top-Down Blocking Map_Prompt
输入资产_动作时序参考图

视频生成_Prompt / Seedance视频_Prompt
视频生成 Payload文件 / Seedance Payload文件
Prompt文件
Reference_URLs
Prompt_Output_Map
生成视频成片
质量检查抽帧图
QA摘要
视频生成_TaskID
视频生成_Seed
视频生成_Tokens
视频生成_估算成本CNY
视频生成_计划参数
```

Base field headers may include local shorthand in parentheses. Model-facing prompt text should use full names such as `Character Reference Sheet`, `Scene, Environment, and Settings reference image`, and `Top-Down Blocking Map`.

## End-to-End Workflow

### 1. Inspect or create the Base row

```bash
BASE='[REDACTED]'
TABLE='[REDACTED]'
REC='rec...'
WORK=/tmp/video_baseline_workflow
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
r = json.load(open('/tmp/video_baseline_workflow/target_record.json'))['data']['record']
for k, v in r.items():
    if v not in (None, '', []):
        print(k, str(v)[:300])
```

For a new run, create or reserve a row early. It becomes the running ledger for prompts, assets, payload, and final QA.

### 2. Build Character Reference Sheet prompts

Generate one Character Reference Sheet per main character. Do not merge main characters into one sheet unless the user explicitly asks for a cast sheet.

Recommended tool:

```text
Hermes image_generate, Seedream, or another image model selected by the user/environment.
```

Do not silently switch tools if the user specified one.

#### Character Reference Sheet prompt template

Use this as the default high-quality template. Fill placeholders explicitly.

```text
Create a single unified MASTER CHARACTER REFERENCE SHEET for one fictional character.

STYLE: [visual style, e.g. stylized 3D cinematic comedy, premium animation visual bible, clean character continuity sheet]
SUBJECT: [character name or role]
IDENTITY: [species / gender / age range if relevant / body type / face shape / hair or fur / eyes / signature silhouette]
COSTUME OR SURFACE DESIGN: [outfit, fur pattern, fabric, accessories, color blocking]
PERSONALITY: [3 to 6 traits visible in posture and expression]
STORY FUNCTION: [protagonist, rival, comic relief, customer, villain, etc.]
FORBIDDEN DRIFT: [identity traits that must never change]

Create the board in a 4:3 horizontal layout. The board layout, background, typography and spacing must be clean, neutral, minimal and technical, on a pure white or clean off-white background. Use clear section titles, readable English labels, balanced spacing, no clutter, no watermark, no logo. Apply the style only to the character and visual elements, not to the board layout or UI. All text must be clearly readable at normal viewing size. Avoid tiny or dense text.

Use this exact layout:
Top row = left: title + horizontal info block, right: COLOR PALETTE.
Center = large MAIN IDENTITY + SCALE SHEET as the biggest section.
Right column = EXPRESSION PROGRESSION + HEAD DETAIL SHEET + NEUTRAL BASELINE + POSTURE VARIATION + CLOSE-UP POSE.
Bottom = WARDROBE / ACCESSORIES DETAILS + PROP + HAND GESTURES.

Include title: CHARACTER REFERENCE SHEET.
1. TOP INFO BLOCK: Name, Role, Age or Life Stage, Personality, Core Theme, Speech or Movement Style.
2. COLOR PALETTE: 6 to 8 clean swatches, no labels.
3. MAIN IDENTITY + SCALE SHEET: largest section. Same subject only. Show Front, 3/4 View, Side, Back over subtle measurement guide lines. Include small SILHOUETTE GUIDE.
4. EXPRESSION PROGRESSION: exactly 8 panels: Neutral, Curious, Worried, Surprised, Afraid, Sad, Determined, Relieved.
5. MICRO EXPRESSIONS: exactly 5 panels: subtle eye tension, slight smirk, lip tension, micro fear, controlled breath.
6. HEAD DETAIL SHEET: 3/4 Headshot, Side Headshot, Top Angle, Low Angle, Diagonal Angle.
7. NEUTRAL BASELINE: 1 relaxed panel.
8. POSTURE VARIATION: 3 panels: relaxed, tense, confident.
9. CLOSE-UP POSE: exactly 1 cinematic chest-up close-up.
10. WARDROBE / ACCESSORIES DETAILS: exactly 4 close-up callouts.
11. PROP: exactly 1 isolated key prop with info block. If no prop is needed, use a simple silhouette marker instead.
12. HAND OR PAW GESTURES: relaxed, tense fingers or paw, pointing, gripping, subtle gesture near face.

Keep the subject fully consistent across all panels. MAIN IDENTITY + SCALE SHEET must visually dominate. No extra characters, no environment, no storyboard panels, no speech bubbles. No unreadable fake text beyond short section titles.
```

#### Character Reference Sheet QA

Reject or mark as candidate only if any of these occur:

- More than one character appears.
- Main identity changes across views.
- Human character becomes animal-like unintentionally.
- Animal character becomes a different species.
- Clothes, fur patterns, or signature colors drift heavily.
- Text, badges, logos, watermarks, fake glyphs, or symbols pollute the character.
- Important view is cropped.
- The sheet is too dense for a video model to interpret.

Record per character:

```text
Tool:
Model:
Prompt:
Output local path:
Public URL:
Attachment field:
QA status:
```

### 3. Build the Scene, Environment, and Settings reference image

The Scene, Environment, and Settings reference image locks the world, not the characters. It should normally contain no main characters.

#### Scene, Environment, and Settings reference image prompt template

```text
Create a single clean cinematic Scene, Environment, and Settings reference image.

PURPOSE: This image defines only the environment, lighting, spatial layout, material palette, camera mood, and key props for a later video generation. It is not a storyboard and not a character sheet.

SETTING: [place, era, culture, genre]
SPATIAL LAYOUT: [main anchor object, entrances, exits, windows, stairs, tables, vehicles, stage, counter, or other stable geometry]
KEY PROPS: [only the important props that should persist]
LIGHTING: [motivated light sources, time of day, contrast, haze, rim light, practical lamps]
COLOR PALETTE: [dominant colors and accent colors]
MATERIALS: [wood, stone, metal, fabric, glass, dust, rain, neon, etc.]
CAMERA FEEL: [cinematic medium-wide establishing frame, stable perspective, readable depth]
MOOD: [comedy, suspense, warmth, tension, premium commercial, etc.]

Generate one coherent environment image in 16:9 landscape format. Make it a single cinematic frame, not a collage, not a multi-panel board, not a blueprint, not a concept sheet with labels.

No characters, no people, no animals, no faces, no silhouettes of main characters. No text, no captions, no labels, no title, no signs with readable writing, no logos, no watermark, no arrows, no diagrams, no panel borders. Keep the main spatial anchor clearly visible and reusable for video continuity.
```

If the scene must include a table, vehicle, door, stage, counter, or other blocking anchor, state exactly where it is in frame. Do not rely on vague mood words.

#### Scene reference QA

Reject or mark as candidate only if:

- Main characters appear.
- Text, labels, signs, arrows, panels, or diagrams appear.
- The core spatial anchor is missing.
- The scene contradicts the script.
- Key props are present in the wrong state and would confuse the video prompt.

### 4. Optional action, keyframe, or blocking reference

Use an action reference only if the video needs precise movement, contact, direction, or spatial continuity.

Choose the lowest-risk format:

```text
No extra reference
→ single clean Top-Down Blocking Map
→ 2×3 or 3×3 Seedance-safe blocking board
→ first_frame / last_frame chain
```

Rules:

- Human review boards may contain labels, arrows, and notes.
- Seedance-safe references should avoid text, captions, dense arrows, grids, labels, and repeated characters.
- If using a Top-Down Blocking Map, write the full name in prompts. Do not use only `TDBM`.
- If using first/last frames in Seedance, do not mix `last_frame` with regular `reference_image` items in the same payload if the API rejects that combination. Generate keyframes first, then feed only first/last frames plus text.

### 5. Publish or attach generated assets

For API reproducibility, publish reference images to stable HTTPS URLs or store them in the system expected by the video API.

For human review, upload images into Feishu attachment fields.

Feishu CLI upload requires a safe relative file path from the current working directory. Do not pass absolute paths.

```bash
cd /path/to/reference/images

lark-cli base +record-upload-attachment --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  --field-id '输入资产_角色1参考图' \
  --file character_1_reference_sheet.png
```

### 6. Build the Seedance-ready video prompt

Use the image references by content order, not UI syntax. Do not write `@Image1`.

Recommended structure:

```text
Generate a [duration] second [ratio] video with audio setting: [generate_audio true/false].

REFERENCE USAGE
The first reference_image item in content[] is the Character Reference Sheet for [Character 1]. Use it only for identity, outfit or surface design, silhouette, and expression range.
The second reference_image item in content[] is the Character Reference Sheet for [Character 2]. Use it only for identity, outfit or surface design, silhouette, and expression range.
The third reference_image item in content[] is the Character Reference Sheet for [Character 3]. Use it only for identity, outfit or surface design, silhouette, and expression range.
The fourth reference_image item in content[] is the Scene, Environment, and Settings reference image. Use it for environment, lighting, spatial anchor, material palette, and camera mood.
[If present] The fifth reference_image item in content[] is the Top-Down Blocking Map or action reference. Use it only for spatial blocking, action order, contact points, movement direction, and camera rhythm. Do not reproduce its text, labels, arrows, grid lines, icons, panel borders, or diagram style in the final video.

CHARACTERS
[Character 1]: [short stable identity].
[Character 2]: [short stable identity].
[Character 3]: [short stable identity].
Visible cast count must stay consistent: [exact count rule].

SETTING
[Concise scene description from the Scene, Environment, and Settings reference image. Mention spatial anchor.]

TIMELINE
[0-2s] [scene, camera, action, expression, sound]
[2-4s] [scene, camera, action, expression, sound]
[4-6s] [scene, camera, action, expression, sound]
[6-8s] [scene, camera, action, expression, sound]
[8-10s] [scene, camera, action, expression, sound]
[10-12s] [scene, camera, action, expression, sound]

CAMERA
Mostly stable cinematic medium-wide base around the same spatial anchor. Gentle push-ins during dialogue or reaction beats. Use one clear wider shot for the final physical action. No chaotic fast camera movement, no position swaps.

AUDIO
[Dialogue, sound effects, background music, or no audio. If dialogue is required, write the exact lines and speaker order.]

RESTRICTIONS
No subtitles, no speech bubbles, no dialogue text, no captions, no storyboard text visible in final video. No logo, no watermark, no extra characters, no duplicate characters, no identity drift, no temporal flicker, no bent limbs, no distorted faces, no unwanted text, no arrows, no diagram style.
```

Keep text within the API's prompt length limit. If the model has a strict Chinese character limit, compress the timeline and keep only the hard constraints.

### 7. Build payload JSON

Generic Seedance-style payload:

```json
{
  "model": "doubao-seedance-2-0-260128",
  "duration": 12,
  "resolution": "480p",
  "ratio": "16:9",
  "generate_audio": true,
  "return_last_frame": false,
  "content": [
    {"type": "text", "text": "..."},
    {"type": "image_url", "image_url": {"url": "https://example.com/character_1.png"}, "role": "reference_image"},
    {"type": "image_url", "image_url": {"url": "https://example.com/character_2.png"}, "role": "reference_image"},
    {"type": "image_url", "image_url": {"url": "https://example.com/character_3.png"}, "role": "reference_image"},
    {"type": "image_url", "image_url": {"url": "https://example.com/scene_reference.png"}, "role": "reference_image"}
  ]
}
```

Before submission:

- Verify every URL returns HTTP 200.
- Verify content order matches the prompt.
- Verify no forbidden shorthand appears in model-facing text unless expanded first.
- Save payload JSON and prompt text locally.
- Upload payload and prompt file to the Base row if the row already exists.
- Get explicit user confirmation before billable generation.

### 8. Submit video and poll without duplicate billing

Separate phases:

1. Build payload and save it.
2. Submit once.
3. Persist task id immediately.
4. Poll only by task id.
5. Download result.
6. QA and upload.

Do not re-run a combined submit+poll script after timeout unless you first inspect saved POST response and task id.

### 9. QA the generated video

Use `ffprobe` for media facts:

```bash
ffprobe -v error -show_entries stream=index,codec_type,width,height,duration,nb_frames,r_frame_rate,codec_name -of json output.mp4 > ffprobe.json
```

Create a contact sheet:

```bash
ffmpeg -y -hide_banner -loglevel error -i output.mp4 \
  -vf "fps=1,scale=240:-1,tile=5x3" -frames:v 1 contact_sheet.jpg
```

If audio or dialogue matters, extract and transcribe:

```bash
ffmpeg -y -hide_banner -loglevel error -i output.mp4 -vn -ac 1 -ar 16000 audio.wav
whisper audio.wav --language Chinese --model tiny --output_dir whisper --output_format txt --fp16 False
```

QA report should cover:

- Actual width, height, duration, fps, audio stream.
- Character identity stability.
- Scene and spatial anchor stability.
- Required action beats.
- Dialogue transcription if applicable.
- Text/subtitle/watermark contamination.
- Extra characters or duplicates.
- Tokens and estimated cost.
- Whether this version is usable as a baseline, candidate, or reject.

### 10. Complete the Base row

Use `record-batch-update` with this JSON shape:

```json
{
  "record_id_list": ["rec..."],
  "patch": {
    "角色参考图（CRS）_角色1_工具": "Image generation tool / model name",
    "角色参考图（CRS）_角色1_Prompt": "...",
    "场景环境设定参考图（SES）_工具": "Image generation tool / model name",
    "场景环境设定参考图（SES）_Prompt": "...",
    "视频生成_Prompt": "...",
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
Status: approved baseline / candidate / rejected

INPUT ASSET MAP — completed on YYYY-MM-DD HH:MM TZ

1. Character 1 Reference Sheet
Tool: ...
Model: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Source asset row: ...
QA: ...

2. Character 2 Reference Sheet
Tool: ...
Model: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Source asset row: ...
QA: ...

3. Character 3 Reference Sheet
Tool: ...
Model: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Source asset row: ...
QA: ...

4. Scene, Environment, and Settings reference image
Tool: ...
Model: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Source asset row: ...
QA: ...

5. Optional action / blocking reference
Tool: ...
Prompt: stored in field ...
Public URL: ...
Attachment field: ...
Payload role: ...
QA: ...

Video generation
Tool: ...
Model: ...
Payload file: ...
Prompt file: ...
Output video field: ...
Quality-review contact sheet field: ...
QA summary field: ...
```

### 11. Repair/backfill existing approved rows

If the video already exists, do not generate new assets by default.

Search existing records and local/public files for source assets. Match by asset names, payload reference URLs, file names, hashes, and status; do not rely on memory alone.

Useful source row fields usually include:

- `资产类型`
- `工具`
- `模型`
- `Prompt`
- `Output_URL`
- `图片附件`
- `Local_Path`
- `Reference_URLs`

Verify file identity before upload:

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

### 12. Verify by re-reading target row

```bash
lark-cli base +record-get --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  > /tmp/video_baseline_workflow/verify_record.json
```

Verification script:

```python
import json
r = json.load(open('/tmp/video_baseline_workflow/verify_record.json'))['data']['record']
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
  '视频生成_Prompt',
  '视频生成 Payload文件',
  '生成视频成片',
  '质量检查抽帧图',
  'QA摘要',
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

- One approved video version should have one complete baseline row.
- The Base row is the source of truth for review, reuse, and comparison.
- Attachments are for human review and Gallery views; public URLs are for API reproducibility.
- Public URL fields should contain clean URLs only. Multi-line explanations belong in `Prompt_Output_Map` or notes.
- Use full names in prompts and maps:
  - `Character Reference Sheet`
  - `Scene, Environment, and Settings reference image`
  - `Top-Down Blocking Map`
  - `background music`
- Do not use unexplained internal abbreviations in model-facing text.
- Preserve rejected/candidate assets when useful; label status clearly instead of overwriting history.
- Do not submit extra billable video attempts without user confirmation.

## Security Rules

- Never expose real base tokens, table IDs, app secrets, API keys, access tokens, or signed URLs in chat, docs, cards, commits, or examples.
- If command output includes sensitive identifiers, redact before reporting.
- Before any Git push involving this workflow, scan staged changes for credentials. Credentials are zero-tolerance.
- Do not commit `.env`, token files, raw API responses containing signed URLs, or private workspace exports.

## Common Pitfalls

1. **Treating this as only a backfill skill.** It now covers generation templates, payload construction, QA, and backfill. Use the backfill-only path only when assets already exist.

2. **Generating all characters in one reference sheet.** Main characters need separate Character Reference Sheets for stable reuse.

3. **Letting scene reference images contain characters or text.** Scene references should lock the world, not pollute the video with unwanted people, animals, signs, labels, or panels.

4. **Uploading absolute paths to Feishu Base.** `record-upload-attachment` may reject unsafe absolute paths. `cd` into the directory and pass a relative filename.

5. **Trusting `record-list` after field changes.** It may show incomplete long fields. Use `record-get --record-id` for verification.

6. **Wrong batch update shape.** Use `{"record_id_list": [...], "patch": {...}}`.

7. **Assuming source asset row equals payload asset.** Check target `Reference_URLs`, payload JSON, public URL, local file, and hashes.

8. **Re-running submit scripts after timeout.** First check whether a task id was already created. Duplicate submission can burn money.

9. **Printing sensitive identifiers.** Tool logs may contain base tokens or table IDs. User-facing summaries must omit or redact them.

## Verification Checklist

- [ ] Target Base row exists or has been created.
- [ ] Field list fetched and field names confirmed.
- [ ] Character list approved.
- [ ] Character Reference Sheet prompt generated per main character.
- [ ] Character Reference Sheet images generated and QA checked.
- [ ] Scene, Environment, and Settings reference image prompt generated.
- [ ] Scene reference image generated and QA checked.
- [ ] Optional action / keyframe / blocking reference selected deliberately.
- [ ] Public URLs verified with HTTP 200 or equivalent storage checks.
- [ ] Payload JSON saved.
- [ ] User confirmed before billable video generation.
- [ ] Task id saved immediately after submission.
- [ ] Video downloaded.
- [ ] `ffprobe` QA completed.
- [ ] Contact sheet generated and reviewed.
- [ ] Audio/dialogue transcribed if relevant.
- [ ] Tokens and estimated cost recorded.
- [ ] Prompt, payload, output video, contact sheet, and assets uploaded or attached.
- [ ] Tool fields populated.
- [ ] Prompt fields populated.
- [ ] `Prompt_Output_Map` populated with asset lineage.
- [ ] Re-read with `record-get`.
- [ ] Missing required fields count is 0 for the intended field set.
- [ ] Final user summary contains no base token, table ID, or credential.
