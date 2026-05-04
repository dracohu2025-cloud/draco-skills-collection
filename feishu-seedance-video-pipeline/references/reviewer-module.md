# Reviewer Module

Reviewer Module 是 Seedance 产线的强制质量门禁，位置在 Director Module / 物料准备 / Prompt & Payload 构建之后，任何 billable Seedance POST 之前。

它的目标不是“润色”，而是拦截流程违规。Reviewer 不通过，禁止提交。

## Mandatory Rule

任何新视频生成任务都必须产出 `reviewer_report.md`，并上传到当前 Base 行的 Prompt文件或审计附件字段。报告结论只能是：

- `PASS_TO_SUBMIT`
- `BLOCKED`

只有 `PASS_TO_SUBMIT` 才能提交 Seedance。

## Inputs

Reviewer 必须读取并核验：

1. 当前 Base 行：`record-get`。
2. 当前表字段：`field-list`。
3. 如果用户提到第 N 行、baseline、之前成功版本：必须 `record-list` / `record-get` 读取对应行。
4. 当前行所有本地文件：director_plan、Prompt、Payload、reference_urls、物料生成 Prompt、QA/自审文件。
5. 当前行附件字段：Character Reference Sheet、Scene, Environment, and Settings reference image、Wardrobe Reference image、Prompt文件、Payload文件。

## Review Gates

### Gate 1 — Base Material Ledger

必须确认当前行已经完整维护物料台账：

- 每个主要角色的 Character Reference Sheet：工具、Prompt、附件或明确官方 asset 策略。
- Scene, Environment, and Settings reference image：工具、Prompt、附件或明确复用来源。
- 使用官方/预置人像 asset 时：Wardrobe Reference image 必须存在，并上传/登记到当前行。
- 复用旧物料也必须在当前行写清楚来源、URL/asset、用途、payload 中的引用顺序。
- 当前行输入资产字段不得因“复用旧资产”而空白跳过；无法放入专用字段时，至少要放入图片附件/Prompt文件审计附件，并在 Prompt_Output_Map 写清楚。

缺任一项：`BLOCKED`。

### Gate 2 — Baseline Prompt Comparison

若存在历史成功 baseline（例如第32行）：

- 必须拉取 baseline Prompt。
- 新 Prompt 结构完整度不得低于 baseline。
- 至少包含：Dialogue Lock、整体风格与硬约束、reference_image 逐项绑定、空间关系硬约束、道具与状态硬约束、音频、逐秒导演稿、禁止项。
- 多幕视频每一幕都要独立满足上述结构；不能只写一个总纲。

低于 baseline：`BLOCKED`。

### Gate 3 — Reference Binding

必须确认：

- Prompt 中的参考图顺序与 payload.content[] 完全一致。
- Prompt 不写 `@Image1`。
- Prompt 不使用内部缩写：不要写 CRS / SES / WR / TDBM；写全称。
- Payload 每个 reference image 的 URL/asset 可访问或格式正确。
- 使用 `asset://...` 人像时，Wardrobe Reference image 在每个相关 task 中作为 `reference_image`。

不一致：`BLOCKED`。

### Gate 4 — Dialogue Lock

用户给出的对白必须逐字保留：

- 文字、标点、语气词、波浪号、空格、顺序全部一致。
- 多幕分别验证。
- 重复台词用顺序扫描，不用 `index()`。

不一致：`BLOCKED`。

### Gate 5 — Character / Scene / Prop Constraints

必须检查 Prompt 是否明确约束：

- 可见角色数量。
- 每个角色外观、服装、站位、左右关系。
- 场景空间锚点。
- 道具初始状态和变化。
- 禁止额外角色、字幕、文字、水印、气泡、分镜格。

缺关键约束：`BLOCKED`。

### Gate 6 — Base Pre-submit State

必须确认提交前已回填：

- Prompt / Seedance视频_Prompt。
- Prompt文件。
- Payload文件。
- Reference_URLs 或本地 `reference_urls.json` 附件/说明。
- Prompt_Output_Map。
- Seedance视频_计划参数。
- 状态：待提交/Reviewer PASS。

未回填或未复核：`BLOCKED`。

## Output Schema

```markdown
# Reviewer Report

result: PASS_TO_SUBMIT | BLOCKED
record_id: rec...
baseline_record_id: rec... | none
model: doubao-seedance-2-0-260128

## Gate Results

- Base Material Ledger: PASS | BLOCKED — evidence
- Baseline Prompt Comparison: PASS | BLOCKED | N/A — evidence
- Reference Binding: PASS | BLOCKED — evidence
- Dialogue Lock: PASS | BLOCKED — evidence
- Character / Scene / Prop Constraints: PASS | BLOCKED — evidence
- Base Pre-submit State: PASS | BLOCKED — evidence

## Blocking Issues

1. ...

## Required Fixes Before Submit

1. ...

## Evidence

- current_record_get: path
- baseline_record_get: path | none
- prompt_files: path list
- payload_files: path list
- reference_files: path list
```

## Enforcement

- Reviewer 报告必须上传 Base。
- `result=BLOCKED` 时，不得提交 Seedance。
- 如果已经误提交，必须立即把该 Base 行状态改为失败/废片，并上传 postmortem。
