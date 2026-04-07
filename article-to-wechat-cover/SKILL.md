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
