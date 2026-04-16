---
name: seedance-video-local
description: 用火山引擎 Ark 的 Seedance 2.0 系列做视频生成（文本+参考图/视频/音频），支持提交任务、轮询状态、下载结果，默认 480p 控成本。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [volcengine, ark, seedance, video-generation, multimodal]
---

# Seedance Video Local

当用户想要：
- 调用火山引擎 Seedance 2.0 生成视频
- 使用参考图/参考视频/参考音频做多模态控制
- 在本机可复用一套“提交→轮询→下载”的稳定流程
- 先低成本验证（默认 480p）

就用这个 skill。

## 默认策略（重要）

- 默认 `resolution=480p`（控成本）
- 默认 `ratio=16:9`
- 默认 `duration=5`（更省）
- 默认 `watermark=false`
- 默认模型：`doubao-seedance-2-0-260128`

## 鉴权与环境变量

- 脚本要求显式传入：`--api-key`
- 推荐在 shell 中以变量方式传入：`--api-key "$VOLCENGINE_API_KEY"`
- 可选环境变量：`ARK_BASE_URL`（默认 `https://ark.cn-beijing.volces.com/api/v3`）

## 脚本

- `scripts/seedance_video.py`
- `scripts/seedance_prompt_generator.py`
- `scripts/seedance_workflow.py`
- `scripts/seedance_cost_estimator.py`

### A) 生成任务脚本：`seedance_video.py`

功能：
- `check`：检查环境
- `preview`：只打印请求 JSON，不发请求
- `submit`：创建任务
- `get`：查询任务状态
- `run`：创建并轮询到结束（可选自动下载）
- `cancel`：取消/删除任务

### B) Prompt Generator：`seedance_prompt_generator.py`

用途：把自然语言视频需求按 Seedance 方法论结构化。

固定方法：
- `subject > action > camera > style > constraints`

能力：
- 识别时间分镜（如 `2-4 秒：...` / `[0-4s]: ...` / `[0.0-0.8s] ...` / `[00:00-00:04] ...`）
- 识别分层标题并提取结构（如 `Core Subject` / `Main Action` / `Action Sequence` / `Cinematography` / `Visual Style` / `【角色】` / `【风格】`）
- 输出五层结构与最终 prompt，尽量避免 `subject` / `action` 重复
- 遵循 Seedance Prompt Bible 的实战规则：非时间轴场景默认只保留一个主摄像机运动（避免冲突）
- 自动修复退化关键词（如 `fast`、`glow/glimmer/glints`、单独 `cinematic`、`lots of movement`）
- 自动补默认约束（防抖动、防形变、防闪烁等）

示例：

```bash
python3 scripts/seedance_prompt_generator.py \
  --brief '第一视角果茶广告，2-4 秒摇杯，4-6 秒成品特写，golden hour，避免抖动' \
  --json
```

### C) 统一入口：`seedance_workflow.py`

用途：一条命令完成「需求结构化 -> 生成 prompt -> 提交/轮询 Seedance 任务」。

模式：
- `preview`：只生成结构化结果与最终 payload（不扣费）
- `submit`：生成并提交任务（默认）
- `run`：生成、提交并轮询到结束（可选下载）

模板：
- `--template ./template.json` 可给单条与批量任务提供默认参数（refs、duration、ratio、resolution 等）
- 合并优先级：`item 字段 > template 字段 > 命令行默认值`（批量时）

注意：
- `seedance_workflow.py` 默认 mode 是 `submit`，会真实发起任务并产生费用。
- 强烈建议先跑 `--mode preview` 做结构化与 payload 校验，再提交。
- 若用户明确要求“先看 prompt 再决定是否生成”（高成本场景常见），必须执行审批门：
  1) 先输出导演版 prompt（可含中文注释版）供 review；
  2) 未收到用户明确确认前，禁止 `submit/run`；
  3) 用户确认后再提交，且默认继续使用 `480p` 控成本。
- 对“剧情型 prompt”（多段事件）必须做 **beat 覆盖核对**：提交前逐条核对关键事件是否都在 timeline 里（例如：开火→子弹充能→贴地飞行→击中爆裂→拉回人物→收枪离场），避免后半段语义丢失。

示例（推荐先 preview）：

```bash
python3 scripts/seedance_workflow.py \
  --mode preview \
  --brief '第一视角果茶广告，2-4 秒摇杯，4-6 秒成品特写，golden hour' \
  --ref-image-url 'https://ark-project.tos-cn-beijing.volces.com/doc_image/r2v_tea_pic1.jpg' \
  --json
```

正式提交：

```bash
python3 scripts/seedance_workflow.py \
  --mode submit \
  --api-key "$VOLCENGINE_API_KEY" \
  --brief '第一视角果茶广告，2-4 秒摇杯，4-6 秒成品特写，golden hour' \
  --ref-image-url 'https://ark-project.tos-cn-beijing.volces.com/doc_image/r2v_tea_pic1.jpg' \
  --ref-video-url 'https://ark-project.tos-cn-beijing.volces.com/doc_video/r2v_tea_video1.mp4' \
  --generate-audio \
  --duration 11 \
  --json
```

### D) 成本统计模块：`seedance_cost_estimator.py`

依据（与你给的图一致）：
- `tokens = (宽 * 高 * 帧率 * 时长) / 1024 * 条数`
- 单价：`¥0.046 / 1000 tokens`

说明：
- `seedance_workflow.py` 已内置成本估算输出到 `cost_estimate`
- 同时输出人类可读摘要：单条结果 `cost_summary_human`（示例：`预计 ¥x.xx / 条，本次合计 ¥y.yy`）
- 批量结果 `summary` 里额外包含：`estimated_video_count` 与 `cost_summary_human`（示例：`预计 ¥x.xx / 条，批量总计 ¥y.yy`）
- 终端非 JSON 模式会直接打印 `cost_summary: ...`，方便快速看预算
- 默认参数：`fps=24`、`video_count=1`、`token_price_cny_per_1k=0.046`
- 可覆盖参数：`--fps`、`--video-count`、`--token-price-cny-per-1k`、`--width`、`--height`
- `--width/--height` 不填时，会按 `resolution + ratio` 自动估算像素尺寸
- 智能比例/智能时长模式下仅能估算，实际以最终结果为准

示例：

```bash
python3 scripts/seedance_workflow.py \
  --mode preview \
  --brief '第一视角果茶广告，2-4 秒：摇杯，4-6 秒：成品特写' \
  --resolution 480p \
  --ratio 16:9 \
  --duration 5 \
  --fps 24 \
  --video-count 1 \
  --json
```

批量模式（`--auto-submit-from-file`）：

说明：
- 支持三种输入：`JSON 数组`、`{"items": [...]}`、`JSONL`（每行一个 JSON 对象）。
- 每条 item 可覆盖全局参数，常用覆盖字段：
  - `brief` / `brief_file`
  - `mode`（preview/submit/run）
  - `resolution` / `ratio` / `duration` / `seed`
  - `fps` / `video_count` / `token_price_cny_per_1k`
  - `width` / `height`
  - `ref_image_url` / `ref_video_url` / `ref_audio_url`
  - `first_frame_url` / `last_frame_url`
  - `generate_audio` / `watermark` / `extra_json` / `download`
- 批量模式退出码：有失败项时返回非 0；可配 `--continue-on-error` 继续后续任务。

#### 方案1：不使用 template（每条自己带参数）

```json
[
  {
    "brief": "第一视角果茶广告，2-4 秒：摇杯，4-6 秒：成品特写",
    "ref_image_url": ["https://ark-project.tos-cn-beijing.volces.com/doc_image/r2v_tea_pic1.jpg"],
    "duration": 6
  },
  {
    "brief": "第一视角举杯递给镜头，golden hour",
    "ref_video_url": ["https://ark-project.tos-cn-beijing.volces.com/doc_video/r2v_tea_video1.mp4"],
    "resolution": "720p"
  }
]
```

#### 方案2：使用 template（推荐，batch 里只写 brief）

`template.json`（常用默认参数）：

```json
{
  "ref_image_url": ["https://ark-project.tos-cn-beijing.volces.com/doc_image/r2v_tea_pic1.jpg"],
  "ref_video_url": ["https://ark-project.tos-cn-beijing.volces.com/doc_video/r2v_tea_video1.mp4"],
  "ratio": "16:9",
  "duration": 8,
  "resolution": "480p",
  "generate_audio": true
}
```

`batch.json`（只保留差异）：

```json
[
  {"brief": "第一视角果茶广告，2-4 秒：摇杯，4-6 秒：成品特写"},
  {"brief": "第一视角举杯递给镜头，golden hour", "duration": 11}
]
```

合并优先级：
- 批量 item 字段 > template 字段 > 命令行默认值

2) 先批量 preview（零成本）：

```bash
python3 scripts/seedance_workflow.py \
  --mode preview \
  --auto-submit-from-file ./batch.json \
  --template ./template.json \
  --batch-output ./batch.preview.result.json \
  --json
```

3) 批量 submit（真实提交，可选遇错继续）：

```bash
python3 scripts/seedance_workflow.py \
  --mode submit \
  --api-key "$VOLCENGINE_API_KEY" \
  --auto-submit-from-file ./batch.json \
  --template ./template.json \
  --continue-on-error \
  --batch-output ./batch.submit.result.json \
  --json
```

### Prompt Generator 方法要点（来自实测）

- 五层顺序固定：`subject > action > camera > style > constraints`
- 时间分镜优先：识别 `2-4 秒：...`、`[0-4s]: ...`、`[00:00-00:04] ...`、`[0.8-1.6s] ...`（小数秒）后，优先生成 time-coded prompt
- 当需求包含“后半段关键剧情”（如子弹飞行→击中目标→爆裂→人物收枪离场）时，必须写成显式分镜时间线；不要只给长段叙述，否则模型易压缩后半段动作
- 结构化标题优先：可直接写 `Core Subject / Main Action / Action Sequence / Cinematography / Visual Style / Camera Settings / Quality`，也支持 `【角色】/【风格】/【场景】`
- 长句解析支持分号切分（`；`/`;`），可降低 `subject` 与 `action` 重复
- 非 timeline 场景默认单主镜头运动，减少镜头冲突
- 对退化词做自动修复：
  - `fast` → `single fast element, keep all other elements steady`
  - `glow/glimmer/glints` → `steady intensity diffuse light`
  - `cinematic`（单独）→ `cinematic film tone, 35mm`
  - `lots of movement` → `one primary movement only`
- 默认约束建议始终注入：
  - `avoid jitter`
  - `avoid bent limbs`
  - `avoid temporal flicker`
  - `maintain face consistency`

### Prompt Generator 回归测试

```bash
python3 scripts/test_seedance_prompt_generator.py
python3 scripts/test_seedance_workflow.py
python3 scripts/test_seedance_cost_estimator.py
```

如果你改了关键词映射/正则、成本公式参数、或统一入口编排，先跑这组测试再提交。

## 快速开始

### 1) 零成本预览（推荐）

```bash
python3 scripts/seedance_video.py preview \
  --prompt '第一视角果茶广告，首尾帧清晰，节奏轻快' \
  --ref-image-url 'https://ark-project.tos-cn-beijing.volces.com/doc_image/r2v_tea_pic1.jpg' \
  --ref-image-url 'https://ark-project.tos-cn-beijing.volces.com/doc_image/r2v_tea_pic2.jpg' \
  --ref-video-url 'https://ark-project.tos-cn-beijing.volces.com/doc_video/r2v_tea_video1.mp4' \
  --ref-audio-url 'https://ark-project.tos-cn-beijing.volces.com/doc_audio/r2v_tea_audio1.mp3' \
  --generate-audio
```

### 2) 提交并轮询

```bash
python3 scripts/seedance_video.py run \
  --api-key "$VOLCENGINE_API_KEY" \
  --prompt '第一视角果茶广告，镜头从摘果到成品递杯' \
  --ref-image-url 'https://ark-project.tos-cn-beijing.volces.com/doc_image/r2v_tea_pic1.jpg' \
  --ref-image-url 'https://ark-project.tos-cn-beijing.volces.com/doc_image/r2v_tea_pic2.jpg' \
  --ref-video-url 'https://ark-project.tos-cn-beijing.volces.com/doc_video/r2v_tea_video1.mp4' \
  --ref-audio-url 'https://ark-project.tos-cn-beijing.volces.com/doc_audio/r2v_tea_audio1.mp3' \
  --generate-audio \
  --duration 11 \
  --download ./outputs/seedance_ad.mp4
```

### 3) 查询已有任务

```bash
python3 scripts/seedance_video.py get \
  --api-key "$VOLCENGINE_API_KEY" \
  --task-id cgt-xxxx
```

## 参考 API 路径

- 创建：`POST /contents/generations/tasks`
- 查询：`GET /contents/generations/tasks/{id}`
- 取消/删除：`DELETE /contents/generations/tasks/{id}`

## 结果说明

- 成功状态：`succeeded`
- 运行中状态：`queued` / `running`
- 失败状态：`failed` / `expired` / `cancelled`
- 成功后关注：`content.video_url`（通常有时效，建议立刻下载）

## 常见坑

1. `401/403`：API Key 不对或没生效。
2. 参考资源 URL 必须公网可访问。
3. `first_frame/last_frame` 不能与 `reference_image/reference_video/reference_audio` 混用；会报 `InvalidParameter`。
4. 分辨率、时长越高，成本越高；先用 480p+短时长确认可行再提档。
5. 运行中的任务无法删除（`InvalidAction.RunningTaskDeletion`）；通常只支持取消排队中的任务。
6. 任务状态轮询若看不到实时日志，优先用 `python3 -u .../seedance_video.py run`（unbuffered）或直接 `get` 查询 task_id。

## 交付建议（飞书）

生成完成后，建议立刻上传飞书云盘并返回可打开链接：

1. `lark-cli drive +upload` 上传 mp4（注意 `--file` 必须是当前目录相对路径）
2. 用 `drive metas batch_query` 通过 `file_token` 取 `url`
3. 回复用户该 `https://*.feishu.cn/file/<token>` 链接

这一步建议作为默认交付收尾，避免只给本地路径。
