# Archived skill: article-to-wechat-cover

Original path: `productivity/article-to-wechat-cover`

Consolidation reason: Cover generation is one stage of WeChat article publishing.

---

---
name: article-to-wechat-cover
description: 从飞书文档或本地 Markdown 提炼文章主题与风格，调用 OpenRouter 的 Nano Banana / Gemini Flash Image 生成 2.35:1 的微信公众号封面图，并可选上传为微信封面素材。
version: 0.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, cover, feishu, lark, markdown, nano-banana, openrouter, image-generation]
---

# Article to WeChat Cover

当用户想要：
- 为一篇飞书文档生成微信公众号封面图
- 为一篇本地 Markdown 文章自动生成公众号头图
- 让封面图主题跟随文章内容自动变化
- 复用 Nano Banana / OpenRouter 图片生成链路做公众号封面
- 在用户确认最终 prompt 后，把生成图片自动插入飞书文档最顶部作为 Hero 图

就用这个 skill。

## 目标

这个 skill 会做三件事：

1. 读取文章内容（飞书文档 URL / token，或本地 Markdown）
2. 用 OpenRouter 文本模型提炼：
   - 文章核心主题
   - 文章视觉风格
   - 适合公众号封面的构图与主视觉
3. 先输出最终版生图 prompt 给用户确认
4. 只有确认后，才用 OpenRouter 图片模型（Nano Banana / Gemini Flash Image）生成 **2.35:1** 微信公众号封面图

默认要求：
- 宽高比固定 `2.35:1`
- 画面体现文章核心主题
- 风格由文章内容语气、领域、表达风格共同决定
- 默认**不渲染多余文字**，避免把公众号封面做成低质海报

## 输入来源

支持两种：

### 1) 飞书文档

```bash
python3 scripts/run.py from-feishu-doc \
  --doc 'https://xxx.feishu.cn/docx/xxx' \
  --final-prompt-output /tmp/wechat-cover-prompt.txt
```

### 2) 本地 Markdown

```bash
python3 scripts/run.py from-markdown \
  --input ./article.md \
  --final-prompt-output /tmp/wechat-cover-prompt.txt
```

## 输出

成功后会输出：
- 本地封面图路径（仅在已确认并真正生图后）
- 主题分析 JSON 路径（可选）
- 图片 JSON spec 路径（可选）
- 最终版生图 prompt（可打印，也可写入文件）
- 可选 `feishu_url`
- 可选 `thumb_media_id`

## 必须先确认最终 prompt

这个 skill 现在默认采用两阶段流程：

### 关键经验：给用户确认的内容，优先使用纯 JSON spec

这次真实使用后，新增一个重要经验：

- **给用户确认时，不要把“执行指令 + JSON”混在一起展示**
- 更适合确认的是：**纯 JSON 的 review spec**
- 真正发给 Nano Banana / Gemini Flash Image 的执行输入，应再从 review spec 中提炼成**更干净、更短的 execution JSON**

原因：

1. 用户审阅时，纯 JSON 更清楚，能直接看：
   - 主题
   - 主体
   - 场景
   - 构图
   - 光线
   - 配色
   - 必须包含 / 必须避免
2. 如果把太多解释层字段、流程字段、工作流说明一起喂给图片模型，模型可能会把其中一部分也误当成画面语义，导致：
   - 画面过度抽象
   - 偏概念图
   - 偏“AI 工作流示意图”而不是文章头图
3. 真正给图片模型的 payload 应尽量只保留：
   - `subject`
   - `scene`
   - `style`
   - `composition`
   - `lighting`
   - `color_palette`
   - `aspect_ratio`
   - `must_include`
   - `must_avoid`

推荐分层：

### A. 分析层 JSON
用于内部主题提炼，可包含：
- `core_theme`
- `tone`
- `reader_takeaway`
- `visual_direction`
- `subject`
- `scene`
- `composition`
- `lighting`
- `palette`
- `style_keywords`
- `must_include`
- `must_avoid`

### B. 审核层 JSON（推荐给用户确认）
字段收紧，只保留：
- `title`
- `core_theme`
- `tone`
- `subject`
- `scene`
- `composition`
- `lighting`
- `color_palette`
- `aspect_ratio`
- `must_include`
- `must_avoid`

### C. 执行层 JSON（真正喂给图片模型）
应更干净，只保留：
- `subject`
- `scene`
- `style`
- `composition`
- `lighting`
- `color_palette`
- `aspect_ratio`
- `must_include`
- `must_avoid`

必要时在外层只补一句非常短的执行指令，例如：

```text
Generate one premium editorial WeChat cover image strictly following this JSON.
```

不要把冗长的解释层字段、工作流说明、输出契约都一并送入图片模型。

### 阶段 1：先生成最终版生图 prompt，给用户确认

推荐：

```bash
python3 scripts/run.py from-feishu-doc \
  --doc 'https://g1mu6da08l.feishu.cn/docx/xxxx' \
  --final-prompt-output /tmp/wechat-cover-prompt.txt
```

或：

```bash
python3 scripts/run.py from-markdown \
  --input ./article.md \
  --final-prompt-output /tmp/wechat-cover-prompt.txt
```

这一步会：
- 先分析文章主题与风格
- 生成最终版生图 prompt
- 在终端打印 prompt 预览
- 可选写入 `--final-prompt-output`
- **不会真的调用图片模型生图**

如果命令输出里看到：

```text
generation_skipped=pending_user_confirmation
```

说明流程正常停在“待确认”阶段。

### 阶段 2：确认后，再真正生图

只有在用户确认最终 prompt 没问题后，才重新执行并加上：

```bash
--confirm-generate
```

例如：

```bash
python3 scripts/run.py from-feishu-doc \
  --doc 'https://g1mu6da08l.feishu.cn/docx/xxxx' \
  --final-prompt-output /tmp/wechat-cover-prompt.txt \
  --output ./wechat-cover.jpg \
  --confirm-generate
```

经验规则：
- **不要**在第一次分析出 prompt 后立刻自动生图
- 必须先把 final prompt 发给用户审阅
- 用户确认后，才允许 `--confirm-generate`

补充经验：
- 图片模型实际可能返回 `image/jpeg`，即使你手动把输出文件写成 `.png`
- 因此脚本应按返回的 `mime_type` 自动修正输出后缀，避免出现“JPEG 内容却使用 PNG 扩展名”的混淆
- 如果用户显式传入了一个不匹配的输出路径，CLI 最好打印一个 `output_adjusted_from=...` 提示，便于排查

## 统一入口命令

### 飞书文档 → 生成封面

```bash
python3 scripts/run.py from-feishu-doc \
  --doc 'https://g1mu6da08l.feishu.cn/docx/xxxx' \
  --output ./wechat-cover.png
```

### 本地 Markdown → 生成封面

```bash
python3 scripts/run.py from-markdown \
  --input ./article.md \
  --output ./wechat-cover.png
```

## 常用参数

- `--output`：输出图片路径
- `--upload-feishu`：生成后上传飞书云盘
- `--upload-wechat-cover`：直接上传成微信封面素材，返回 `thumb_media_id`
- `--analysis-json`：导出文章主题分析 JSON
- `--dump-json-spec`：导出最终图片 JSON 规格
- `--final-prompt-output`：导出最终版生图 prompt，便于发给用户确认
- `--confirm-generate`：只有用户确认最终 prompt 后，才允许真正生图
- `--insert-into-feishu-doc-top`：生成后把 Hero 图自动插到飞书文档正文最顶部
- `--replace-existing-top-image` / `--no-replace-existing-top-image`：插入 Hero 图时是否替换已有顶部图片
- `--image-model`：覆盖默认图片模型
- `--text-model`：覆盖默认文本模型
- `--provider-order`：OpenRouter provider 顺序，默认 `Vertex AI`
- `--visual-style-hint`：人工补充风格偏好
- `--must-include`：逗号分隔，指定必须出现的视觉元素
- `--must-avoid`：逗号分隔，指定必须避免的视觉元素
- `--allow-text-overlay`：允许封面内出现少量标题文字（默认关闭）

## 与飞书文档 → 微信草稿箱 skill 的关系

这个 skill 不直接替代 `feishu-doc-to-wechat-draft`，而是作为它的前置封面生成步骤。

推荐组合方式：

1. 先用本 skill 生成封面图
2. 若需要，直接 `--upload-wechat-cover` 拿到 `thumb_media_id`
3. 再把这个 `thumb_media_id` 交给 `feishu-doc-to-wechat-draft`

例如：

```bash
python3 scripts/run.py from-feishu-doc \
  --doc 'https://xxx.feishu.cn/docx/xxx' \
  --final-prompt-output /tmp/wechat-cover-prompt.txt
```

确认 prompt 没问题后，如果你想把生成图直接插回飞书文档最顶部：

```bash
python3 scripts/run.py from-feishu-doc \
  --doc 'https://xxx.feishu.cn/docx/xxx' \
  --final-prompt-output /tmp/wechat-cover-prompt.txt \
  --confirm-generate \
  --insert-into-feishu-doc-top
```

如果还要同时上传成微信封面素材：

```bash
python3 scripts/run.py from-feishu-doc \
  --doc 'https://xxx.feishu.cn/docx/xxx' \
  --final-prompt-output /tmp/wechat-cover-prompt.txt \
  --confirm-generate \
  --insert-into-feishu-doc-top \
  --upload-wechat-cover
```

然后把输出的 `thumb_media_id` 用于：

```bash
python3 ~/.hermes/skills/productivity/feishu-doc-to-wechat-draft/scripts/run.py publish-feishu-doc-default \
  --doc 'https://xxx.feishu.cn/docx/xxx' \
  --thumb-media-id 'MEDIA_ID'
```

## 设计原则

### 1. 主题来自文章，不靠人工硬写 prompt
脚本会先从标题、摘要、正文提炼主题与风格，再生成图片 prompt。

### 2. 公众号封面优先“像封面”，不是“像 PPT 截图”
默认避免：
- 杂乱文字
- UI 截图感
- 信息图堆砌
- 水印
- logo 拼贴

### 3. 优先横向头图构图
固定 `2.35:1`，适合公众号封面横幅视觉。

## 依赖

- `OPENROUTER_API_KEY`
- 可选：`OPENROUTER_TEXT`（默认 `google/gemini-3.1-flash-lite-preview`）
- 可选：`OPENROUTER_IMAGE`
- 如需读取飞书文档：已可用的 `lark-cli`
- 如需上传微信封面素材：
  - `WECHAT_APP_ID`
  - `WECHAT_APP_SECRET`

## 验证建议

先本地跑：

```bash
python3 scripts/run.py from-markdown --input ./article.md --analysis-json /tmp/analysis.json --dump-json-spec /tmp/spec.json
```

确认：
- analysis 是否抓住主题
- spec 是否保持 `2.35:1`
- 最终图片是否贴合文章主题

## 实战经验 / 已验证行为

### 1. 生图前必须先做最终 prompt 确认

这个 skill 现在默认会在真正调用图片模型前停下来，输出：
- 文章主题分析
- 最终版生图 prompt 预览
- 可选 `--final-prompt-output` 文件

只有在用户明确确认后，再带上：

```bash
--confirm-generate
```

才允许真正生图。

#### 新增经验：给用户审的应该优先是 **纯 JSON review spec**

这次真实使用里，用户明确指出：
- 待确认的“最终 prompt”如果外面再包一层自然语言执行说明，阅读上会混淆
- 对人审核时，重点应该是结构化字段本身，而不是执行包装文案

更稳的做法是把“审核对象”和“执行对象”分层：

1. **review JSON**：给用户确认
   - 只保留人最关心的字段，例如：
     - `core_theme`
     - `tone`
     - `subject`
     - `scene`
     - `composition`
     - `lighting`
     - `color_palette`
     - `aspect_ratio`
     - `must_include`
     - `must_avoid`
2. **execution JSON**：真正喂给 Nano Banana / Gemini Flash Image
   - 进一步瘦身，只保留直接影响画面的字段
   - 避免混入 `task` / `model_intent` / `template` / `prompt_design_rules` / `output_contract` 这类解释层字段
3. 如确实需要外层执行指令，也应由程序在最后一步自动包裹，不要把它作为用户主要审核对象

经验结论：
- **用户确认时优先展示纯 JSON spec**
- **真正送给图片模型的 JSON 应比 review JSON 更干净、更短、更少解释层噪音**
- 否则 Nano Banana 可能把流程说明、模板说明也误吸收为视觉语义，导致画面偏抽象、偏概念图、偏离文章主题

### 1.1 给用户确认时，优先展示“纯 JSON review spec”

真实联调发现：
- 如果把最终 prompt 展示成“英文执行指令 + 一整段 JSON”的混合结构，用户在审阅时会觉得不够干净
- 对用户真正有价值的，通常不是外层那句 `Interpret the following JSON ...`，而是 JSON 本体里的视觉语义字段

更稳的做法：
- **用户确认阶段**：优先展示纯 JSON review spec
- **模型执行阶段**：再由程序自动包一层极短的执行指令

推荐 review spec 至少保留：

```json
{
  "title": "...",
  "core_theme": "...",
  "tone": "...",
  "subject": "...",
  "scene": "...",
  "composition": "...",
  "lighting": "...",
  "color_palette": "...",
  "aspect_ratio": "2.35:1",
  "must_include": ["..."],
  "must_avoid": ["..."]
}
```

### 1.2 真正喂给 Nano Banana 的执行 JSON 要更“瘦”

这次还验证出一个很重要的经验：
- 给图片模型的 payload 如果包含太多解释层字段（如 `task`、`model_intent`、`template`、`prompt_design_rules`、`output_contract`、冗长 `article_context`），模型有机会把这些说明也当成视觉语义的一部分
- 结果往往会让画面更抽象、更像概念图，甚至偏离“文章头图”这个目标

因此建议把最终执行输入拆成两层：

1. **review JSON**：给用户看，便于审阅和修改
2. **execution JSON**：给 Nano Banana，用更少字段直接描述画面

推荐 execution JSON 只保留这类字段：

```json
{
  "subject": "...",
  "scene": "...",
  "style": "...",
  "composition": "...",
  "lighting": "...",
  "color_palette": "...",
  "aspect_ratio": "2.35:1",
  "must_include": ["..."],
  "must_avoid": ["..."]
}
```

经验结论：
- review 阶段可以更可解释
- execution 阶段应尽量“纯净、短、少解释字段”
- 当文章主题是“内容工作流 / 封面生成 / 文档头图”时，`subject` 和 `scene` 要尽量写成**内容场景本身**，少写泛化的“数据流 / 抽象节点 / 科技光效”，这样更像公众号头图

补充经验：
- **给用户确认时，最好展示纯 JSON 的 review spec**，不要把执行说明、工作流解释、模型意图说明混在一起。
- 用户真正要审核的是：`subject`、`scene`、`style`、`composition`、`lighting`、`color_palette`、`aspect_ratio`、`must_include`、`must_avoid` 这些视觉决策字段。
- 如果把 `task`、`model_intent`、`template`、`prompt_design_rules`、`output_contract` 之类解释层字段一起展示或一起送进图片模型，容易让用户看着别扭，也可能让 Nano Banana / Gemini Flash Image 误吸收无关语义。
- 更稳的分层方式是：
  1. **analysis JSON**：文章理解结果，字段可以较丰富；
  2. **review JSON**：给用户确认的精简视觉 spec；
  3. **execution JSON**：真正喂给图片模型的超精简 payload，只保留会直接影响画面的字段。
- 真正给 Nano Banana 的 payload 应尽量干净，避免混入流程说明、审核说明和多余元字段。

### 2. 飞书文档顶部 Hero Insert 的可靠做法

这次真实验证后，确认了一个比“直接往顶部插图”更稳的实现路径：

1. 先 `docs +fetch` 取回原始 Markdown
2. 如果开启 `--replace-existing-top-image`，先去掉开头连续的 `<image .../>` Hero 图标签
3. 用 `docs +update --mode overwrite` 把文档临时改成一个占位文本
4. 再调用 `docs +media-insert`
   - 这样飞书会把图片插入到当前文档内容末尾
   - 因为此时文档只剩占位文本，所以本质上得到“顶部 Hero 图”
5. 再次 `docs +fetch`，从返回 Markdown 中提取飞书生成的 `<image token="..."/>`
6. 最后再 `docs +update --mode overwrite`，把文档改写成：
   - Hero 图
   - 空行
   - 原正文内容

这样可以稳定得到“文档正文最顶部 Hero 图”的效果。

### 3. 为什么不直接把文档清空后再插图

真实踩坑发现：

- `lark-cli docs +update --mode overwrite` 如果不给 `--markdown`，会直接报：

```text
--overwrite mode requires --markdown
```

所以更稳的方式不是“清空文档”，而是先写入一个占位文本，再插图，再重写成最终内容。

### 4. `lark-cli docs +media-insert` 的路径限制

真实联调确认：
- `--file` 不能用绝对路径
- 必须是当前工作目录下的相对路径

稳妥做法：
- 先把目标图片复制到一个临时目录
- `cwd` 切到该目录
- 再用 `./filename` 形式调用 `docs +media-insert`

### 5. 回滚策略很重要

因为 Hero Insert 会临时重写飞书文档，所以中途任一步失败，都必须：
- 重新用原始 Markdown 执行一次 `docs +update --mode overwrite`
- 把文档恢复到操作前状态

这能避免用户文档被卡在“占位文本”或半成品状态。

## 适用边界

适合：
- 技术文章
- 观点评论
- 方法论总结
- 产品/AI/效率类公众号文章

不适合直接拿来做：
- 强品牌商业广告 KV
- 多页海报
- 需要精确排版文字设计的活动主视觉

这类任务应额外提供人工 art direction。
