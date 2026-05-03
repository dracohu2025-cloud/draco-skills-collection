---
name: feishu-seedance-video-pipeline
description: "Use when running a Feishu/Lark Base-centered Seedance video production pipeline: inspect/backfill the Base row, create/reference assets, build Row-24-style Chinese Seedance prompts, submit/poll/download via Volcengine Seedance 2.0, QA the result, record tokens/cost, and keep asset lineage auditable."
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [Feishu, Bitable, Seedance, Video Generation, Asset Lineage, QA]
    related_skills: [builtin-image-generate-feishu, volcengine-seedream]
---

# Feishu + Seedance 视频产线

## Overview

这是默认视频产线 skill：以飞书多维表格作为工作流、资产台账和审计源，以 Volcengine Seedance 2.0 作为视频生成引擎。

目标不是“生成一条视频”这么窄，而是完成一条可复用、可追溯、可验收的 Base 行：脚本、角色资产、场景资产、参考图、Prompt、payload、Task ID、成片、抽帧、QA、tokens、成本、Prompt_Output_Map 都在同一行或可追溯链路里。

核心是 Director Module：先判断主要角色、角色参考资产、场景环境资产、空间调度和镜头拆分，再进入图片生成、payload 构建、Seedance 提交和 QA 回填。Seedance API 只是执行层，Director 才是决策层。

## When to Use

Use when:

- 用户给出飞书 Base 行，要求准备、提交、复核或修复 Seedance 视频。
- 用户说“第 N 行”“补表”“上传多维表”“生成视频”“准备烧钱”。
- 需要生成或复用 Character Reference Sheet、Scene, Environment, and Settings reference image、Top-Down Blocking Map、keyframes。
- 需要把已经生成的视频、抽帧、QA、tokens、成本回填到 Base。
- 需要把一个可看版本固化为 baseline。

Do not use when:

- 只是闲聊创意，不涉及视频生成或 Base 资产管理。
- 用户明确不用飞书 Base。
- 用户只要底层 Seedance API 问答；这时可仍参考本 skill 的 API 小节。

## Default Policy for This User

- 默认模型：`doubao-seedance-2-0-fast-260128`。
- 只有用户明确要求标准版、高质量优先、或 Standard/Fast A/B 对比时，才用 `doubao-seedance-2-0-260128`。
- 默认分辨率：`480p`，控成本。
- 默认比例：按项目；短剧/横屏 demo 通常用 `16:9`。
- 默认风格：邵氏电影质感 / 写实古风棚拍 / 武侠喜剧质感。用户指定其他风格时，以用户指定为准。
- 默认 Prompt：中文完整版，第24行 baseline 式细导演稿。
- 未经用户确认，不提交任何 billable Seedance POST。
- 提交前必须补齐 Base 中提交前已知字段，并 `record-get` 复核。
- 交付必须报 tokens 和估算成本。
- 使用官方 `asset://...` 人像时，不上传自生成 Character Reference Sheet 到该角色附件字段，避免误用。

## Feishu Base as Source of Truth

Base 行要回答：

- 这条视频的剧情/脚本是什么？
- 每个角色参考资产是什么，由什么工具和 Prompt 生成？
- 场景、环境与设定参考图是什么？
- 是否使用 Top-Down Blocking Map、keyframe 或 action reference？
- Seedance 收到的完整 `content[]` 顺序和 text prompt 是什么？
- 生成 Task ID、模型、时长、比例、分辨率、音频设置是什么？
- 成片、抽帧、自审、转写、tokens、成本是什么？
- 哪些附件是输入，哪些是输出，哪些只是审计说明？

常见字段：

```text
角色参考图（CRS）_角色名_工具
角色参考图（CRS）_角色名_Prompt
输入资产_角色名参考图
角色名参考图_URL

场景环境设定参考图（SES）_工具
场景环境设定参考图（SES）_Prompt
输入资产_场景环境设定参考图
场景环境设定参考图_URL

动作参考图 / 关键帧参考图 / Top-Down Blocking Map_工具
动作参考图 / 关键帧参考图 / Top-Down Blocking Map_Prompt
输入资产_动作时序参考图

Prompt
Seedance视频_Prompt
Seedance Payload文件 / 视频生成 Payload文件
Prompt文件
Reference_URLs
Prompt_Output_Map
视频生成_计划参数
视频生成_TaskID
生成视频成片
质量检查抽帧图
QA摘要
视频生成_Tokens
视频生成_估算成本CNY
Local_Path
状态
```

字段名会变。永远先 `field-list`，再写。

## Director Module

Director Module 是本 skill 的第一步，也是核心决策层。

职责：

1. 从 Feishu Base 行和脚本中判断主要角色数量。
2. 决定每个主要角色是否需要独立 Character Reference Sheet，以及 CRS Prompt 要锁什么。
3. 决定环境是否需要 Scene, Environment, and Settings reference image，以及 SES Prompt 要锁什么。
4. 判断是否需要 Top-Down Blocking Map 或 keyframes。
5. 把视频拆成 4-6 组镜头，覆盖完整时长。
6. 为每组镜头写可直接进入 Seedance Prompt 的导演稿：景别、构图、运镜、动作、表情、空间锚点、道具连续性、对白/音效、禁止项。

配套文件：

- `references/director-module.md`：Director 的职责、判断规则、输出 schema、门禁。
- `templates/director-decision-output-template.md`：每次处理新 Base 行时先填写的结构化导演方案模板。

工作原则：先产出 `director_plan`，再写 CRS/SES/Seedance Prompt。没有导演方案就直接写 Prompt，视为不合格。

## End-to-End Workflow

### 1. Inspect row and fields

```bash
BASE='[REDACTED]'
TABLE='[REDACTED]'
REC='rec...'
WORK=/tmp/feishu_seedance_pipeline
mkdir -p "$WORK"

lark-cli base +field-list --as user \
  --base-token "$BASE" --table-id "$TABLE" \
  > "$WORK/fields.json"

lark-cli base +record-get --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  > "$WORK/record.json"
```

读取 `data.record`，不要假设一定有 `data.record.fields`。

### 2. Prepare or verify assets

每个主角独立 Character Reference Sheet，除非用户明确要群像表。

本 skill 自带五份可直接调用的模板/参考文件：

- `references/director-module.md`：Director Module 规则，判断主要角色、Character Reference Sheet / Scene, Environment, and Settings reference image / Top-Down Blocking Map / keyframes 需求、镜头拆分和门禁。
- `templates/director-decision-output-template.md`：处理每条 Base 行时先填写的结构化 `director_plan` 模板。
- `templates/character-reference-sheet-prompt-template.md`：主要角色 Character Reference Sheet 完整 Prompt 模板与 QA 门禁。
- `templates/scene-environment-settings-prompt-template.md`：Scene, Environment, and Settings reference image 完整 Prompt 模板与 QA 门禁。
- `templates/seedance-row24-director-template.md`：符合第24行/第28行风格的 Seedance 中文细导演稿模板，要求逐秒时间轴绑定镜头语言、空间锚点、动作、对白/音效。

先填写 Director `director_plan`，再生成或复用具体资产。

Character Reference Sheet 要点：

- 单角色，不混多个主角。
- 4:3 横向布局优先。
- MAIN IDENTITY + SCALE SHEET 最大。
- 表情、头部角度、姿态、服装/配件、手/爪动作齐全。
- 不要把场景、字幕、Logo、水印塞进角色表。
- 生成后用视觉自审，不合格不要当 PASS。

Scene, Environment, and Settings reference image 要点：

- 锁环境、光线、材质、空间锚点、关键道具。
- 通常不要出现主角、动物、人物剪影。
- 16:9 单张电影画面，不要拼贴、分镜板、蓝图、文字、箭头。
- 默认邵氏电影 / 古风棚拍 / 武侠喜剧质感，除非用户指定别的风格。

Top-Down Blocking Map / keyframes：

- 只在动作、站位、接触关系复杂时用。
- 面向 Seedance 的参考图应少文字、少箭头、少网格，避免模型复现图表风格。
- Prompt 里写全名 `Top-Down Blocking Map`，不要只写 `TDBM`。

### 3. Publish references

Seedance API 需要可访问 URL 或 `asset://...`。

本机或自有 HTTPS 发布例：

```bash
SRC="/path/to/reference.png"
OUTDIR="/var/www/example.com/media/seedance"
sudo mkdir -p "$OUTDIR"
sudo cp "$SRC" "$OUTDIR/reference.png"
sudo chmod 644 "$OUTDIR/reference.png"
curl -L -s -o /tmp/ref_check.png -w '%{http_code} %{content_type} %{size_download}\n' \
  "https://example.com/media/seedance/reference.png"
```

Feishu 附件上传要求相对路径：

```bash
cd /path/to/files
lark-cli base +record-upload-attachment --as user \
  --base-token "$BASE" --table-id "$TABLE" --record-id "$REC" \
  --field-id '输入资产_场景环境设定参考图' \
  --file scene_reference.png
```

## Seedance API Essentials

Endpoint:

```text
POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
GET  https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}
Authorization: Bearer <VOLCENGINE_API_KEY>
Content-Type: application/json
```

Content rules:

```json
{"type":"text","text":"完整中文Prompt"}
{"type":"image_url","image_url":{"url":"https://..."},"role":"reference_image"}
{"type":"image_url","image_url":{"url":"asset://asset-id"},"role":"reference_image"}
{"type":"image_url","image_url":{"url":"https://..."},"role":"first_frame"}
{"type":"image_url","image_url":{"url":"https://..."},"role":"last_frame"}
```

不要在 API Prompt 里写 `@Image1`。参考图绑定靠 `content[]` 顺序和 `role`。

默认 payload：

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
    {"type": "image_url", "image_url": {"url": "https://example.com/character_or_scene.png"}, "role": "reference_image"}
  ]
}
```

提交：

```bash
curl -sS -X POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks \
  -H "Authorization: Bearer ${VOLCENGINE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @payload.json | tee post_response.json | jq .
```

轮询：

```bash
TASK_ID="cgt-..."
for i in {1..80}; do
  curl --max-time 30 -sS "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/${TASK_ID}" \
    -H "Authorization: Bearer ${VOLCENGINE_API_KEY}" \
    | tee result_latest.json | jq '{status, usage, error, content}'
  sleep 15
done
```

## Row-24 Director Prompt Standard

Prompt 不合格的典型病：只写剧情，不写镜头。

必须包含：

1. 整体硬约束：片长、比例、分辨率、音频、模型意图、可见角色数量、服装/身份锁。
2. 风格锁：默认邵氏电影质感 / 写实古风棚拍 / 武侠喜剧质感。
3. 参考图用途：按 `content[]` 顺序说明，不写 `@Image`。
4. 空间关系：左右、前后、入口、出口、最终位置、空间锚点。
5. 道具状态：初始状态、变化节点、禁止继承场景图里的错误道具。
6. 逐秒时间轴：每段同时写镜头、运镜/切换、空间锚点、动作、表情、对白/音效。
7. 音频：`generate_audio=true/false`，对白逐句列明。
8. 限制项：无字幕、无气泡、无文字、无分镜格、无箭头、无水印、无额外角色、无身份漂移、无道具漂移。

时间轴模板：

```text
[0-2秒] 镜头构图与运镜：中广角建立镜头，镜头从桌面空间锚点轻轻推近。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
[2-4秒] 镜头构图与运镜：切到中近景，保持角色左右关系不变。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
```

提交前复核：

```text
Prompt == Seedance视频_Prompt == payload.content[0].text == 本地 prompt 文件
模型 == doubao-seedance-2-0-fast-260128，除非用户另指定
无 @Image
无未解释 CRS / SES / TDBM / BGM 等缩写
每个时间段都有镜头语言
未擅自提交生成
```

## Pre-submit Base Gate

任何 billable POST 前：

- 已指定或创建目标行。
- Prompt、Seedance视频_Prompt、payload 本地文件一致。
- Prompt 文件和 Payload 文件已上传或待上传路径明确。
- 角色、场景、动作参考的工具、Prompt、附件、URL 已填或明确 `未使用`。
- Reference_URLs 和 Prompt_Output_Map 草案已写。
- 视频计划参数已写：模型、时长、比例、分辨率、音频、参考图顺序。
- 只有生成后才知道的字段可空：Task ID、成片、抽帧、tokens、成本、最终 QA、转写。
- `record-get` 已复核。
- 用户明确确认“开始生成”或等价授权。

## Poll, Download, QA

长任务不要静默。用后台进程跑，阶段性 poll。

- POST 成功立即保存 `task_id`。
- 超时、中断、下载卡住时，先查 `post_response.json` / `result_latest.json` / Task ID；不要重复 POST。
- 如果 `succeeded` 后下载卡住，使用已保存 `video_url` 做 Range 分片下载；不要重提。

QA：

```bash
ffprobe -v error -show_entries stream=index,codec_type,width,height,duration,nb_frames,r_frame_rate,codec_name -of json output.mp4 > ffprobe.json
ffmpeg -y -hide_banner -loglevel error -i output.mp4 -vf "fps=1,scale=240:-1,tile=5x3" -frames:v 1 contact_sheet.jpg
```

如有对白：

```bash
ffmpeg -y -hide_banner -loglevel error -i output.mp4 -vn -ac 1 -ar 16000 audio.wav
whisper audio.wav --language Chinese --model tiny --output_dir whisper --output_format txt --fp16 False
```

QA 摘要至少包括：

- 实际尺寸、fps、时长、音轨。
- 角色身份稳定性。
- 空间关系/道具状态。
- 关键动作是否完成。
- 是否有字幕、文字、水印、额外角色。
- 对白转写与错词。
- tokens 和估算成本。
- 结论：baseline / candidate / reject。

## Cost Calculation

成功任务 GET 结果通常含 `usage.total_tokens`。

公开估算口径：

- Seedance 2.0 标准版：不含视频输入约 `46 元 / 1,000,000 tokens`；含视频输入约 `28 元 / 1,000,000 tokens`。
- Seedance 2.0 Fast：不含视频输入约 `37 元 / 1,000,000 tokens`；含视频输入约 `22 元 / 1,000,000 tokens`。
- 图生视频/文生视频默认按“不含视频输入”估算，除非 payload 有 `video_url`。

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
print(f"rate_cny_per_million={rate}")
print(f"estimated_cost_cny={tokens * rate / 1_000_000:.2f}")
PY
```

## Backfill and Verify

`lark-cli base +record-batch-update` 用：

```json
{"record_id_list":["rec..."],"patch":{"字段名":"值"}}
```

不要用 `records: [{record_id, fields}]`。

写入后必须 `record-get` 复核，尤其是长 Prompt、附件、Prompt_Output_Map。

附件清理坑：Feishu Base 附件字段不要乱 PATCH 清空/去重。实测可能 append 成 double，或被 `MOBILE_ONLY` / `UploadAttachNotAllowed` 拒绝。删除旧附件优先让用户在 UI 手动删；未复核消失前，不要声称已删除。

## Official asset:// Human Rules

- Seedance 2.0 支持 `asset://...` 官方/授权人像素材。
- Prompt 里不要把 asset ID 当人物名写。
- 文本写“第一个 reference_image 项是官方虚拟人像资产，用于脸型、发型、年龄、体态、表情；服装按文本要求替换”。
- 官方 asset 可能强锁原服装；换装不保证 100%。
- 使用官方 asset 的角色，Base 该角色附件字段默认不放自生成 CRS 图，避免后续误作为输入资产。

## Security Rules

- 不向用户、文档、commit 暴露 base token、table id、app secret、access token、API key、签名 URL。
- 报告中统一 `[REDACTED]`。
- Git push 前必须扫 credentials，零容忍。
- 不提交本地凭证文件、token 文件、原始签名 URL 响应。

## Common Pitfalls

1. **把产线拆成“API 调用”和“补表”两件事。** 实战里它们是一条链：不补表就烧钱，后面必丢上下文。
2. **短 Prompt 直接提交。** 本用户 Seedance 必须是 Row-24 式细导演稿。
3. **时间轴只写动作。** 每段都要有镜头语言。
4. **重复 POST。** 超时先查 Task ID；有 ID 就只 poll/download。
5. **把 `@Image1` 写进 API Prompt。** API 不认这个绑定。
6. **官方 asset 角色又上传自生成 CRS。** 后续容易误用。
7. **用 API 硬删附件。** 容易 append 或失败，先 UI。
8. **标准版误计 Fast 成本，或 Fast payload 却写标准版计划参数。** 模型、payload、Base、成本必须同步。
9. **对白错字就自动重生。** 先报告成本和缺陷，让用户确认是否 V2。
10. **暴露敏感 ID 或签名 URL。** 该打码就打码。

## Verification Checklist

- [ ] 已 field-list。
- [ ] 已 record-get 目标行。
- [ ] 已产出 Director `director_plan`。
- [ ] 已确认主要角色数量和每个角色的 asset_strategy。
- [ ] 已确认 Character Reference Sheet / Scene, Environment, and Settings reference image / Top-Down Blocking Map / keyframes 的生成或复用理由。
- [ ] shot_breakdown 覆盖完整时长，每段都有镜头语言。
- [ ] 已确认角色、场景、动作参考。
- [ ] 已生成/复用并 QA 参考资产。
- [ ] 参考 URL 或 asset:// 可用。
- [ ] 中文完整 Prompt 已写成 Row-24 细导演稿。
- [ ] 默认风格锁已写入，或用户指定风格已覆盖。
- [ ] payload 模型为 Fast，除非用户另指定。
- [ ] `Prompt == Seedance视频_Prompt == payload.content[0].text == 本地 prompt 文件`。
- [ ] 提交前可填字段已补齐。
- [ ] 用户已确认 billable 生成。
- [ ] Task ID 已立即保存。
- [ ] 只按 Task ID poll/download，无重复 POST。
- [ ] ffprobe、抽帧、自审完成。
- [ ] 有对白时已 Whisper 转写。
- [ ] tokens、成本已计算。
- [ ] 成片、抽帧、QA、Prompt_Output_Map 已回填。
- [ ] 最终 record-get 复核。
- [ ] 用户摘要无凭证、无敏感 token。
