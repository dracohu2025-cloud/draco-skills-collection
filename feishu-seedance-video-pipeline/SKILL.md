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

核心是 Director Module + Base Asset Ledger Write Guard + Reviewer Module：Director 先判断主要角色、角色参考资产、场景环境资产、空间调度和镜头拆分；Base 写入只能由 `asset_manifest.json` 机械生成并回读审计；Reviewer 在任何 billable Seedance POST 前做强制门禁，核验 Base 物料台账、baseline Prompt 对照、reference_image 绑定、Dialogue Lock、Prompt/Payload 一致性和 ledger audit。Reviewer 不出 `PASS_TO_SUBMIT`，禁止提交。Seedance API 只是执行层。

## When to Use

Use when:

- 项目输入给出飞书 Base 行，要求准备、提交、复核或修复 Seedance 视频。
- 需求中出现“第 N 行”“补表”“上传多维表”“生成视频”“准备烧钱”。
- 需要生成或复用 Character Reference Sheet、Scene, Environment, and Settings reference image、Top-Down Blocking Map、keyframes。
- 需要把已经生成的视频、抽帧、QA、tokens、成本回填到 Base。
- 需要把一个可看版本固化为 baseline。

Do not use when:

- 只是闲聊创意，不涉及视频生成或 Base 资产管理。
- 需求明确不用飞书 Base。
- 用户只要底层 Seedance API 问答；这时可仍参考本 skill 的 API 小节。

## Default Policy

- 默认模型：`doubao-seedance-2-0-260128`（Seedance 2.0 标准版 / 非 Fast）。
- 只有明确要求 Fast、低成本优先、或 Standard/Fast A/B 对比时，才用 `doubao-seedance-2-0-fast-260128`。
- 默认分辨率：`480p`，控成本。
- 默认比例：按项目；短剧/横屏 demo 通常用 `16:9`。
- 默认风格：邵氏电影质感 / 写实古风棚拍 / 武侠喜剧质感。项目指定其他风格时，以项目指定为准。
- 默认 Prompt：中文完整版，第24行 baseline 式细导演稿。
- 未经确认，不提交任何 billable Seedance POST。
- 提交前必须补齐 Base 中提交前已知字段，并 `record-get` 复核。
- 交付必须报 tokens 和估算成本。
- 使用官方 `asset://...` / Seedance 预置人像库时，不上传自生成 Character Reference Sheet 到该角色附件字段，避免误用。
- 使用官方 `asset://...` / Seedance 预置人像库时，必须生成 Wardrobe Reference image，并在每个 Seedance task 的 `content[]` 里作为 `reference_image` 输入；Prompt 中写全名 `Wardrobe Reference image`，不要写缩写。

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
Seedance视频_TaskID
生成视频成片
质量检查抽帧图
QA摘要
Seedance视频_Tokens
Seedance视频_估算成本CNY
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
- `references/base-asset-ledger-write-guard.md`：Base 资产台账写入门禁；要求 `asset_manifest.json`、写入 payload、`record-get` 回读和机械审计。
- `references/reviewer-module.md`：Reviewer 强制门禁；任何 billable Seedance POST 前必须产出并上传 `reviewer_report.md`，结论为 `PASS_TO_SUBMIT` 才能提交。
- `templates/director-decision-output-template.md`：每次处理新 Base 行时先填写的结构化导演方案模板。
- `templates/reviewer-report-template.md`：Reviewer 报告模板。

工作原则：先产出 `director_plan`，再写 CRS/SES/Seedance Prompt。没有导演方案就直接写 Prompt，视为不合格。

## Reviewer Module

Reviewer Module 是提交前强制审查层。它不负责创作，只负责拦截不符合流程和规范的任务。

位置：Director Module、物料准备、Prompt/Payload 构建之后；任何 billable Seedance POST 之前。

硬规则：

- 每条新视频必须产出 `reviewer_report.md`，上传到当前 Base 行。
- Reviewer 结果只能是 `PASS_TO_SUBMIT` 或 `BLOCKED`。
- `BLOCKED` 时禁止提交 Seedance。
- 若需求要求参考第 N 行或历史 baseline，Reviewer 必须先拉取该行 Prompt 和资产记录做对照。
- Reviewer 必须检查：当前 Base 行物料台账、Character Reference Sheet / Scene, Environment, and Settings reference image / Wardrobe Reference image、Prompt 完整度、payload.content[] 顺序、Dialogue Lock、Prompt/Payload一致性、附件回填、状态字段。

详见：`references/reviewer-module.md` 与 `templates/reviewer-report-template.md`。

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

读取 `data.record`，不要假设一定有 `data.record.fields`。当前 `lark-cli base +record-get` 可能直接把字段平铺在 `data.record` 根部（例如 `data.record["Prompt文件"]`），而不是放在 `data.record.fields`。Reviewer/回填验证脚本应兼容两种结构：优先 `data.record.fields`，不存在时把 `data.record` 本身当字段 dict。`field-list` 的字段数组在当前 `lark-cli` 版本里是 `data.fields`，不是 `data.items`。

如果用户给的是“基于某行/刚才那条视频”的新脚本，先 `record-get` 旧行复用可用资产，再创建新行。新行创建可用：

```bash
lark-cli base +record-batch-create --as user \
  --base-token "$BASE" --table-id "$TABLE" \
  --json '{"fields":["资产名","Prompt"],"rows":[["...","..."]]}'
```

返回里不一定有标准 `records[]`。优先从 `data.record_id_list[0]` 读取新行 ID；不要用宽松正则直接抓第一个 `rec...`，会误抓到正文里的 `record` 字样。随后立刻写入 `record_id.txt` 并 `record-get` 复核。

### 2. Prepare or verify assets

每个主角独立 Character Reference Sheet，除非需求明确要群像表。

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
- 默认邵氏电影 / 古风棚拍 / 武侠喜剧质感，除非项目指定别的风格。

Top-Down Blocking Map / keyframes：

- 只在动作、站位、接触关系复杂时用。
- 面向 Seedance 的参考图应少文字、少箭头、少网格，避免模型复现图表风格。
- Prompt 里写全名 `Top-Down Blocking Map`，不要只写 `TDBM`。

### 3. Publish references

Seedance API 需要可访问 URL 或 `asset://...`。

本机 HTTPS 发布例：

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
  "model": "doubao-seedance-2-0-260128",
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
   - 项目输入给出明确对白台词时，必须逐字保留原文、标点、语气词、波浪号和说话顺序；不得改写、合并、移动、补台词或删台词。
   - 导演稿可以补动作、表情、镜头、音效，但对白内容必须与用户脚本完全一致。
   - 提交前必须做 Dialogue Lock 复核：抽取用户对白数组，与 Prompt 中对白数组逐项比对；不一致不得提交 billable POST。
   - 若需求要求“像某真实演员/配音演员/名人”的声音，不要在模型 Prompt 或 payload 中写具体真人姓名；改写成抽象表演特征，例如“夸张港式无厘头国语男声、尖亮、拖腔、节奏欠揍、喜剧感强”。
8. 限制项：无字幕、无气泡、无文字、无分镜格、无箭头、无水印、无额外角色、无身份漂移、无道具漂移。

时间轴模板：

```text
[0-2秒] 镜头构图与运镜：中广角建立镜头，镜头从桌面空间锚点轻轻推近。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
[2-4秒] 镜头构图与运镜：切到中近景，保持角色左右关系不变。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
```

提交前复核：

```text
Prompt == Seedance视频_Prompt == payload.content[0].text == 本地 prompt 文件
模型 == doubao-seedance-2-0-260128，除非用户另指定 Fast 或 A/B 对比
无 @Image
无未解释 CRS / SES / TDBM / BGM 等缩写
每个时间段都有镜头语言
未擅自提交生成
```

## Multi-Act / Short-Drama Extension

当项目输入给出“多幕/多场/短剧”脚本，且要求每一幕独立生成时：

- Base 仍采用同一行作为整组短剧的 source of truth；不要为每幕拆新行，除非需求明确要求。
- 每一幕对应一个独立 Seedance prompt 文件、payload 文件、Task ID、成片和抽帧；最终再用 ffmpeg 拼接成完整视频。
- 多幕共享同一组主要角色 Character Reference Sheet 与同一张 Scene, Environment, and Settings reference image，除非某一幕明确换角色或换场景。
- 使用官方 `asset://...` / Seedance 预置人像库时，必须生成 Wardrobe Reference image：同一套服饰的前/侧/后/细节多视图；每个 act / 每个 Seedance task 的 `content[]` 都必须加入这张 Wardrobe Reference image 作为 `reference_image`。Prompt 中写全名 `Wardrobe Reference image`，不要写缩写。
- 同一行的 `Seedance视频_TaskID` 写入多行清单，例如 `Act1: cgt-...\nAct2: cgt-...`。
- `生成视频成片` 字段上传每幕成片和最终拼接成片；`质量检查抽帧图` 字段上传每幕抽帧和最终抽帧。飞书附件字段会 append，同一字段多次上传是预期行为。
- `Seedance视频_Tokens` 和 `Seedance视频_估算成本CNY` 写合计值；QA摘要里列每幕 tokens/成本和总计。
- `Reference_URLs` 字段实测会把 JSON/多 URL 字符串自动改写成奇怪 Markdown 链接；优先写短说明或资产标签清单，真实可访问 URL 以 payload 文件、附件和本地 `reference_urls.json` 为准。
- `Prompt_Output_Map` 必须说明：共享 CRS/SES、每幕 payload 文件、每幕 Task ID、最终拼接文件。
- 每一幕都必须单独执行 Dialogue Lock；跨幕不得合并、改写、挪动台词。若同一幕里有重复对白（如两次“还疼么？”），验证时必须用顺序扫描 `find(..., previous_pos+1)`，不要用 `prompt.index()` 列表，否则重复句会误判顺序失败。

多幕拼接命令：

```bash
cat > "$WORK/run/concat_list.txt" <<EOF
file '$WORK/run/act1.mp4'
file '$WORK/run/act2.mp4'
EOF
ffmpeg -y -hide_banner -loglevel error \
  -f concat -safe 0 -i "$WORK/run/concat_list.txt" \
  -c copy "$WORK/run/final_concat.mp4" \
  || ffmpeg -y -hide_banner -loglevel error \
    -f concat -safe 0 -i "$WORK/run/concat_list.txt" \
    -c:v libx264 -c:a aac -movflags +faststart "$WORK/run/final_concat.mp4"
```

## Pre-submit Base Gate

任何 billable POST 前：

- 已指定或创建目标行。
- 若需求要求“看第N行/沿用之前成功版本/参考baseline”，必须先 `record-list` / `record-get` 拉取该行 Prompt、Prompt文件、Prompt_Output_Map、Reference_URLs 和资产附件，对比后再写新 Prompt；不得凭记忆重写。
- 对任何新视频，即使复用旧资产，也必须在当前 Base 行完成物料台账：Character Reference Sheet、Scene, Environment, and Settings reference image、Wardrobe Reference image（如适用）的工具、**原始完整生成 Prompt**、附件或明确复用来源、URL/asset、payload引用顺序。不能只写“用途说明”“风格摘要”“真实猫身体”等摘要；当前行对应输入资产字段不能空着跳过。
- Prompt、Seedance视频_Prompt、payload 本地文件一致。
- Prompt 文件和 Payload 文件已上传或待上传路径明确。
- 角色、场景、动作参考的工具、Prompt、附件、URL 已填或明确 `未使用`。
- Reference_URLs 和 Prompt_Output_Map 草案已写。
- 视频计划参数已写：模型、时长、比例、分辨率、音频、参考图顺序。
- 只有生成后才知道的字段可空：Task ID、成片、抽帧、tokens、成本、最终 QA、转写。
- `record-get` 已复核。
- 已产出 Base Asset Ledger Write Guard 审计：`asset_manifest.json`、写入 payload、post-write `record-get`、audit result，且结果为 PASS。
- 已产出 Reviewer 报告并上传当前 Base 行；只有 `result=PASS_TO_SUBMIT` 才允许提交。
- 需求明确确认“开始生成”或等价授权。

## Poll, Download, QA

长任务不要静默。用后台进程跑，阶段性 poll。

- POST 成功立即保存 `task_id`，并立即回填 Base 的 Task ID / 状态，避免上下文断掉后丢任务。
- 超时、中断、下载卡住时，先查 `post_response.json` / `result_latest.json` / Task ID；不要重复 POST。
- 如果后台 Python 轮询脚本长时间没有任何输出，优先杀掉，改用前台 shell `curl --max-time 30` 循环验证；不要盲等。原因可能是 stdout 缓冲、网络请求卡住、Hermes process preview 没刷新，或 urllib 请求没有按预期输出。
- Seedance 标准版 15s 多参考图任务可能运行 30+ 分钟；只要 GET 仍是 `running` 且无 `error`，不要判失败、不要重复 POST。可以把轮询改成后台进程 + `notify_on_complete`，同时定期 `record-get`/状态回填，避免用户以为卡死。
- 后台 shell 轮询若通过 Hermes process 看不到输出，不一定没跑；检查 `result_*_latest.json` 的 mtime/status，或用 `process log` / `ps` 验证。必要时让脚本同时写日志文件。
- 如果 `succeeded` 后下载卡住，使用已保存 `video_url` 做 Range 分片下载；不要重提。

QA：

```bash
ffprobe -v error -show_entries stream=index,codec_type,width,height,duration,nb_frames,r_frame_rate,codec_name -of json output.mp4 > ffprobe.json
ffmpeg -y -hide_banner -loglevel error -i output.mp4 -vf "fps=1,scale=240:-1,tile=5x3" -frames:v 1 contact_sheet.jpg
```

对白/配音自动转写检查【暂时禁用】：

```bash
# 暂停使用 Whisper 做中文对白 QA：中文识别准确率不足，容易误判。
# 仅保留音轨存在性/规格检查；对白内容以人工验收为准。
# 未来替换为更高准确率模型后再恢复自动转写模块。
# ffmpeg -y -hide_banner -loglevel error -i output.mp4 -vn -ac 1 -ar 16000 audio.wav
# whisper audio.wav --language Chinese --model tiny --output_dir whisper --output_format txt --fp16 False
```

QA 摘要至少包括：

- 实际尺寸、fps、时长、音轨。
- 角色身份稳定性。
- 空间关系/道具状态。
- 关键动作是否完成。
- 是否有字幕、文字、水印、额外角色。
- 音轨存在性；对白内容以人工验收为准，暂不使用 Whisper 中文转写做判断。
- tokens 和估算成本。
- 结论：baseline / candidate / reject。

QA 注意：

- 视觉模型可能因为人物服装/内容安全策略对抽帧返回 403。不要硬编视觉自审；在 QA 中明确“自动视觉审查失败，需人工验收”，仍然回填抽帧图。
- `browser_navigate` 在本 VM 可能因 Chrome sandbox 失败；需要可视检查时可先用 `agent-browser open <file-or-url> --args "--no-sandbox"` 打开，再截图/人工核对。

## Cost Calculation

成功任务 GET 结果通常含 `usage.total_tokens`。

公开估算口径：

- Seedance 2.0 标准版：不含视频输入约 `46 元 / 1,000,000 tokens`；含视频输入约 `28 元 / 1,000,000 tokens`。
- Seedance 2.0 Fast：不含视频输入约 `37 元 / 1,000,000 tokens`；含视频输入约 `22 元 / 1,000,000 tokens`。
- 图生视频/文生视频默认按“不含视频输入”估算，除非 payload 有 `video_url`。

```bash
TOKENS=$(jq -r '.usage.total_tokens // .usage.completion_tokens' result_final.json)
MODEL=$(jq -r '.model // "doubao-seedance-2-0-260128"' payload.json)
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
- 文本写“第一个 reference_image 项是官方虚拟人像资产，用于脸型、发型、年龄、体态、表情；第二个 reference_image 项是 Wardrobe Reference image，用于锁定服装款式、颜色、纹理和跨镜头一致性”。
- 使用官方 `asset://...` / Seedance 预置人像库时，必须先生成 Wardrobe Reference image；每个相关 Seedance task 都把它作为 `reference_image` 输入。
- 官方 asset 可能强锁原服装；换装不保证 100%，所以 Wardrobe Reference image 是门禁，不是可选优化。
- 使用官方 asset 的角色，Base 该角色附件字段默认不放自生成 Character Reference Sheet 图，避免后续误作为输入资产。

## Security Rules

- 不向用户、文档、commit 暴露 base token、table id、app secret、access token、API key、签名 URL。
- 报告中统一 `[REDACTED]`。
- Git push 前必须扫 credentials，零容忍。
- 不提交 `.env`、token 文件、原始签名 URL 响应。

## Common Pitfalls

1. **把产线拆成“API 调用”和“补表”两件事。** 实战里它们是一条链：不补表就烧钱，后面必丢上下文。
2. **短 Prompt 直接提交。** 此工作流建议是 Row-24 式细导演稿。
3. **时间轴只写动作。** 每段都要有镜头语言。
4. **重复 POST。** 超时先查 Task ID；有 ID 就只 poll/download。
5. **把 `@Image1` 写进 API Prompt。** API 不认这个绑定。
6. **官方 asset 角色又上传自生成 CRS。** 后续容易误用。
7. **用 API 硬删附件。** 容易 append 或失败，先 UI。
8. **标准版误计 Fast 成本，或 Fast payload 却写标准版计划参数。** 模型、payload、Base、成本必须同步。
9. **不要基于 Whisper 中文转写自动判废。** Whisper 中文准确率不足；配音/对白内容先由人工验收，未来替换更高准确率模型后再恢复自动门禁。
11. **`field-list` / `record-get` JSON 结构猜错。** 当前 `lark-cli` 返回字段列表在 `data.fields`，不是 `data.items`；`record-get` 可能把业务字段直接平铺在 `data.record` 根部，不一定有 `data.record.fields`。Reviewer脚本必须兼容两种结构，否则会误判 Base Material Ledger / Pre-submit State 为 `BLOCKED`。
12. **`record-batch-create` 新行 ID 抓错。** 响应里优先读 `data.record_id_list[0]`；不要 regex 抓第一个 `rec...`，可能抓到普通英文单词前缀导致 `record-get` 失败。
13. **Reference_URLs 多行字符串被飞书当成奇怪 Markdown 链接。** 实测 JSON 字符串也可能被自动改写成 `[...](http://...)`。Base 里优先写短说明/资产标签，真实 URL 放 payload 附件、本地 `reference_urls.json` 或审计文件。
14. **后台轮询无输出还一直等。** 先杀掉，改前台 `curl --max-time 30` loop 复核任务状态；成功后再单独下载视频。
15. **字段名混淆。** 当前表使用 `Seedance视频_Tokens` / `Seedance视频_估算成本CNY`，不是 `视频生成_Tokens` / `视频生成_估算成本CNY`；写入前用 `field-list` 复核。
16. **视觉 QA 失败就编结论。** provider 403 时只说明自动视觉审查失败，回填抽帧并请求人工验收。

17. **多幕 Dialogue Lock 用 `index()` 验证重复台词。** 同一幕可能重复同一句台词；用 `prompt.index()` 会每次返回第一次出现的位置，导致误判顺序失败。用顺序扫描：`pos=-1; pos=prompt.find(quote, pos+1)`。
18. **多幕短剧拆成多行。** 需求要求共享 CRS/SES 的短剧测试时，默认同一 Base 行；每幕作为独立 Task/附件记录在同一行，最终拼接视频也回填同一行。
20. **官方/预置人像未加 Wardrobe Reference image。** 官方 `asset://` 负责身份，不负责稳定服装；任何使用 Seedance 预置人像库的任务都必须生成 Wardrobe Reference image，并在每个 payload 作为 `reference_image` 传入。Prompt 里写全称，不写缩写。
21. **需求中出现“开始生产”就直接烧。** 错。开始生产不等于跳过物料门禁；必须先把当前行的 CRS / Scene, Environment, and Settings reference image / Wardrobe Reference image / Prompt文件 / Payload文件 / Prompt_Output_Map 补齐并 `record-get` 复核。若当前行的输入资产字段为空，不得提交 Seedance。
23. **没有 Reviewer 报告就提交。** 严重违规。任何新视频必须在提交前产出并上传 `reviewer_report.md`；没有 `PASS_TO_SUBMIT` 就不得 POST。Reviewer 必须核验当前 Base 行物料台账、baseline 对照、Prompt/Payload一致性、Dialogue Lock 和附件回填。

## Verification Checklist

- [ ] 已 field-list。
- [ ] 已 record-get 目标行。
- [ ] 若存在项目指定或历史成功 baseline 行，已 record-get baseline 并对比 Prompt 结构，不低于 baseline 完整度。
- [ ] 已产出 Director `director_plan`。
- [ ] 已确认主要角色数量和每个角色的 asset_strategy。
- [ ] 已确认 Character Reference Sheet / Scene, Environment, and Settings reference image / Top-Down Blocking Map / keyframes 的生成或复用理由。
- [ ] 若使用官方 `asset://...` / Seedance 预置人像库，已生成 Wardrobe Reference image，并已作为每个相关 Seedance task 的 `reference_image`。
- [ ] shot_breakdown 覆盖完整时长，每段都有镜头语言。
- [ ] 已确认角色、场景、动作参考。
- [ ] 已生成/复用并 QA 参考资产。
- [ ] 当前 Base 行已上传或明确登记 Character Reference Sheet / Scene, Environment, and Settings reference image / Wardrobe Reference image 等输入资产；不是只把 URL 塞在 payload 里。
- [ ] 已生成 `asset_manifest.json` 或等价清单；Base 写入由清单机械生成，不是手写摘要。
- [ ] 已完成 post-write `record-get` 与 ledger audit，结果 PASS；Reviewer 报告引用 manifest / write payload / record-get / audit result。
- [ ] 参考 URL 或 asset:// 可用。
- [ ] 中文完整 Prompt 已写成 Row-24 细导演稿。
- [ ] Dialogue Lock 已通过：项目输入给出的每句对白逐字、标点、语气词、波浪号和顺序完全一致。
- [ ] 默认风格锁已写入，或项目指定风格已覆盖。
- [ ] payload 模型为 Seedance 2.0 标准版，除非用户另指定 Fast。
- [ ] `Prompt == Seedance视频_Prompt == payload.content[0].text == 本地 prompt 文件`。
- [ ] 已产出并上传 `reviewer_report.md`，结果为 `PASS_TO_SUBMIT`；若为 `BLOCKED`，不得提交。
- [ ] 提交前可填字段已补齐。
- [ ] 用户已确认 billable 生成。
- [ ] Task ID 已立即保存。
- [ ] 只按 Task ID poll/download，无重复 POST。
- [ ] ffprobe、抽帧、自审完成。
- [ ] 已跳过 Whisper 中文转写检查；仅确认音轨存在，内容由人工验收。
- [ ] tokens、成本已计算。
- [ ] 成片、抽帧、QA、Prompt_Output_Map 已回填。
- [ ] 最终 record-get 复核。
- [ ] 用户摘要无凭证、无敏感 token。
