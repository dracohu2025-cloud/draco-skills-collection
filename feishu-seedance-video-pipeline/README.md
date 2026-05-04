# Feishu + Seedance 视频产线

用飞书多维表格管理 Seedance 视频生产：Director 决策、Reviewer 门禁、素材台账、Prompt、payload、成片、QA、tokens、成本，全在一条可追溯链路里。

这不是“调一下视频 API”。正确姿势是先把角色、场景、服装、参考图和镜头语言准备好，再让 Seedance 执行。烧钱前有 Reviewer，省得废片写进账本。

![Feishu + Seedance pipeline](./assets/feishu-seedance-video-pipeline-flow.svg)

## 适合做什么

| 场景 | 结果 |
|---|---|
| 从飞书多维表第 N 行生成视频 | Prompt / Payload / Task ID / 成片 / QA 全回填 |
| 管理角色、场景、服装和动作参考资产 | 每个资产有工具、Prompt、附件、URL 和用途说明 |
| 多幕短剧按幕独立生成再拼接 | 多个 Task ID / 每幕成片 / 最终 concat 成片 |
| 复用历史成功 baseline | 新 Prompt 结构不低于 baseline，避免缩水 |
| 提交前做流程审查 | `reviewer_report.md` 给出 `PASS_TO_SUBMIT` 或 `BLOCKED` |
| 生成后做成本和媒体规格复核 | ffprobe / 抽帧 / tokens / 估算成本 |

## 核心流程

```text
飞书 Base 行
→ Director Module
   ├─ 判断主要角色 → Character Reference Sheet 计划 / Prompt
   ├─ 判断环境空间 → Scene, Environment, and Settings reference image 计划 / Prompt
   ├─ 判断官方人像 → Wardrobe Reference image 门禁
   ├─ 判断复杂走位 → Top-Down Blocking Map / keyframes
   └─ 拆镜头 → Seedance 中文细导演稿
→ 生成 / 复用参考资产
→ 写入 asset_manifest.json
→ 由 manifest 机械回填当前 Base 行物料台账
→ record-get 回读 + ledger audit
→ 生成 Seedance Prompt + Payload
→ Reviewer Module 强制审查
   ├─ 物料台账
   ├─ baseline Prompt 对照
   ├─ reference_image 绑定顺序
   ├─ Dialogue Lock
   └─ Prompt/Payload/Base 一致性
→ PASS_TO_SUBMIT 后提交 Seedance
→ 轮询、下载、ffprobe、抽帧
→ 多幕 ffmpeg concat（如需要）
→ 回填成片、QA、tokens、成本、Prompt_Output_Map
```

## 默认策略

- 默认模型：`doubao-seedance-2-0-260128`（Seedance 2.0 标准版 / 非 Fast）
- 默认分辨率：`480p`
- 默认比例：短剧/横屏 demo 通常 `16:9`
- 默认 Prompt：中文完整版，逐秒时间轴必须带镜头语言
- 使用官方 `asset://...` 人像时，必须加入 `Wardrobe Reference image`
- 未经确认不提交 billable Seedance 任务
- 成功后必须报告 tokens 和估算成本

## Director Module

Director 是创作前的工程化拆解：

- 判断有几个主要角色，谁需要 Character Reference Sheet，谁只是背景/配角。
- 为每个主要角色确定 `official_asset / existing_character_reference_sheet / generate_character_reference_sheet / text_only`。
- 判断环境是否需要 Scene, Environment, and Settings reference image，锁空间锚点、灯光、材质、道具状态。
- 判断官方人像是否需要 Wardrobe Reference image。一般需要，别偷懒。
- 判断是否需要 Top-Down Blocking Map 或 keyframes。
- 把视频拆成逐秒导演稿：景别、构图、运镜、动作、表情、空间连续性、对白/音效。

先输出 `director_plan`，再写资产 Prompt 和 Seedance Prompt。没有 Director 方案就直接烧，通常会翻车。

## Reviewer Module

Reviewer 是烧钱前的硬门禁。它不信口头承诺，只信 Base 回读和审计证据。报告只能是：

```text
PASS_TO_SUBMIT
BLOCKED
```

检查项：

1. 当前 Base 行是否完整登记 Character Reference Sheet / Scene, Environment, and Settings reference image / Wardrobe Reference image。
2. 如有历史 baseline，新 Prompt 是否不低于 baseline 结构。
3. Prompt 里的参考图顺序是否和 payload.content[] 完全一致。
4. 对白是否逐字锁定，标点、语气词、顺序都不能变。
5. 可见角色数量、站位、道具状态、禁止项是否写清楚。
6. Base Asset Ledger Write Guard 是否 PASS：manifest、写入 payload、record-get、audit result 是否齐全。
7. Prompt、Payload、Prompt_Output_Map、计划参数、附件是否已经提交前回填。

`BLOCKED` 就禁止提交 Seedance。这个规则很粗暴，也很有用。

## Prompt 标准

一个合格的 Seedance Prompt 至少包含：

1. 片长、比例、分辨率、音频设置
2. Dialogue Lock：对白逐字锁定
3. 角色数量、身份、服装、站位锁定
4. 参考图按 `content[]` 顺序说明用途，不写 `@Image1`
5. 场景锚点和道具状态
6. 逐秒时间轴：每段都有构图、运镜/切换、动作、空间连续性、对白/音效
7. 限制项：无字幕、无气泡、无水印、无额外角色、无身份漂移

## 多幕短剧

多幕短剧默认同一 Base 行管理：

- 每幕一个独立 Prompt、Payload、Task ID、成片、抽帧。
- 共享角色参考图、场景参考图、服装参考图。
- 最终用 ffmpeg concat 拼接。
- tokens 和成本按任务合计。

## 文件结构

```text
feishu-seedance-video-pipeline/
├── SKILL.md
├── README.md
├── assets/
│   └── feishu-seedance-video-pipeline-flow.svg
├── references/
│   ├── director-module.md
│   ├── base-asset-ledger-write-guard.md
│   └── reviewer-module.md
├── scripts/
│   └── base_asset_ledger_audit.py
└── templates/
    ├── character-reference-sheet-prompt-template.md
    ├── director-decision-output-template.md
    ├── reviewer-report-template.md
    ├── scene-environment-settings-prompt-template.md
    └── seedance-row24-director-template.md
```

## 最小 payload

```json
{
  "model": "doubao-seedance-2-0-260128",
  "duration": 12,
  "resolution": "480p",
  "ratio": "16:9",
  "generate_audio": true,
  "return_last_frame": false,
  "content": [
    {"type": "text", "text": "完整中文导演稿..."},
    {"type": "image_url", "image_url": {"url": "https://example.com/reference.png"}, "role": "reference_image"}
  ]
}
```

## 安全注意

- 不要把 Base Token、Table ID、API Key、签名 URL 写进仓库。
- Base 资产字段不要手填摘要；用 manifest 生成并审计。
- 公开文档里用 `<BASE_TOKEN>`、`<TABLE_ID>`、`<RECORD_ID>` 这类占位符。
- 推送前扫描 staged diff。凭据零容忍。
