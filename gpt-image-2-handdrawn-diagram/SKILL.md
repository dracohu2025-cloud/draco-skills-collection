---
name: gpt-image-2-handdrawn-diagram
description: Use when generating high-readability hand-drawn knowledge diagrams, architecture diagrams, workflow maps, or consulting-style visual explanations with GPT-Image-2 via image_generate.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [gpt-image-2, image-generation, handdrawn, infographic, architecture-diagram, workflow]
    related_skills: [baoyu-infographic, architecture-diagram]
    source_author: 小小东
    source_homepage: https://x.com/xiaoxiaodong01
---

# GPT-Image-2 Hand-Drawn Diagram

## Overview

This skill turns text, architecture notes, workflows, or reference diagrams into a high-readability hand-drawn knowledge diagram.

Use Hermes `image_generate` for rendering. In this environment, `image_generate` is backed by GPT-Image-2, so do not route this workflow through another image generator unless the user explicitly asks.

The core pattern comes from 小小东's GPT-Image-2 article: lock information design first, then visual style. The goal is not cute decoration. The goal is: **core judgment first, modular reading path second, memorable bottom line last**.

Source credit: 小小东 — https://x.com/xiaoxiaodong01

## When to Use

Use this skill when the user asks for:

- 手绘知识图解
- GPT-Image-2 架构图 prompt
- 高可读性流程图 / 框架图
- 给非工程师看的技术架构解释图
- 把 Mermaid / draw.io / 白板 / 文档内容变成更好看的传播图

Do not use when the user needs a machine-verifiable topology diagram. For that, Mermaid / PlantUML / SVG architecture diagrams are safer.

## Inputs

Collect or infer these fields:

- `topic`: diagram title/topic
- `audience`: target reader, e.g. PM / boss / client / engineers
- `core_judgment`: one-sentence takeaway
- `modules`: 3-6 modules, each with 3-5 short bullets
- `flow_summary`: one-line bottom summary
- `aspect_ratio`: default `16:9`
- `language`: default follows user language; keep technical terms in original English

If content has more than 8 modules, split into multiple diagrams. Do not force 10+ modules into one image.

## Canonical GPT-Image-2 Prompt Template

Use this as the base template. Replace the final `{请输入你的内容或者参考图片}` block with structured content.

```markdown
请把我提供的内容转化成一张高可读性的手绘知识图解。风格像认真整理过的创意手帐 + 白板推演 + 咨询报告信息图，而不是冰冷模板。

【输出目标】
生成一张适合传播、汇报和复用的知识图解。它必须先让人抓住核心判断，再沿着模块逐步阅读，最后记住一句结论。

【语言要求】
图上所有可见文字根据用户的输入来确定语言，中文，英文或其他
不要混用语言，除非是技术名词、产品名、协议名、代码路径或数字指标。

【画布要求】
比例：{16:9 / 5:4 / 4:3 / 21:9}
质量：4K high resolution
背景：浅米白 / 浅暖灰，保留轻微纸张纹理和呼吸感。
整体清晰、留白稳定，不要把文字挤到看不清。

【信息设计规则】
不要逐字搬运原文。先压缩信息，再画图。
请把内容整理成：
1. 顶部：强标题 + 一句话核心判断
2. 中部：3–6 个主模块，按流程、对比、阶段或因果关系排列
3. 模块内：每个模块最多 3–5 条短 bullet
4. 底部：一条 Flow Summary / Decision Summary / Bottom Line
5. 如果内容很多，只保留最关键的 8–10 个判断，避免微型文字

【可读性规则】
标题必须最大、清楚、有重量。
模块标题要有秩序，正文必须短句化。
每个模块不要超过 6 行正文。
每条 bullet 尽量简短。
不要使用密密麻麻的小字表格。
不要为了完整而牺牲可读性。

【视觉风格】
黑色或深墨色手写线条建立阅读骨架。
使用圆角分区、细线框、轻阴影、编号、箭头、标签和小图标。
线条允许轻微手绘抖动，但整体对齐、边距、分组要稳定。
图标只做路标和强调，不要抢走文字层级。

【配色规则】
使用克制的标记笔色彩：
浅米白背景 + 黑色主线条；
低饱和青绿、鼠尾草绿、淡紫、柔橙、浅蓝作为分区和路径颜色。
避免霓虹色、强渐变、过度商业光效和整页单色化。
彩色区域只占少量到中等面积。

【准确性规则】
严格保持输入内容中的技术链路、组件名称、箭头方向、协议、端口、数据流和判断。
不要自行新增未提供的组件。
不要把动作写错，例如“读取日志”不能画成“生成日志”。
如果空间不足，优先保留主链路、关键差异和最终判断，删掉次要解释。

【内容】
{请输入你的内容或者参考图片}
```

## Assembly Workflow

1. Compress the source into 3-6 modules.
2. Keep each module to 3-5 short bullets.
3. Preserve exact technical names: APIs, tools, protocols, file paths, ports, models.
4. Put the strongest takeaway near the top as a sticky-note style callout.
5. End with a bottom line.
6. Call `image_generate` directly with the assembled prompt.
7. Use `aspect_ratio='landscape'` for 16:9, `square` for 1:1, `portrait` for 9:16.

## Content Block Format

Use this compact block inside `【内容】`:

```markdown
主题：<topic>
读者：<audience>
核心判断：<one sentence>
画布：16:9，中文，技术名词保留英文

阅读路径：从左到右，输入 → 解析 → 生成 → 渲染 → 交付；关键保障放在侧边便签。

模块 1：<title>
- <short bullet>
- <short bullet>
- <short bullet>

模块 2：<title>
- <short bullet>
- <short bullet>
- <short bullet>

底部总结：<flow_summary>
```

## Pitfalls

1. **Too many modules**: More than 8 modules collapses readability. Split the diagram.
2. **Tiny text**: GPT-Image-2 may invent or distort small labels. Use fewer, larger labels.
3. **Over-specific colors**: Let the prompt's color semantics work. Extra color rules often clash.
4. **Translated technical terms**: Keep terms like OpenRouter, Volcengine, ffmpeg, Puppeteer, Smart Slide in English.
5. **Icon abuse**: Icons are signposts, not content. Text owns the hierarchy.
6. **Architecture hallucination**: Do not add unprovided components. If a component is uncertain, omit it or mark it as optional.

## Verification Checklist

- [ ] Image was generated via `image_generate`.
- [ ] Diagram has one strong title and one core judgment.
- [ ] Middle section has 3-6 modules, not a dense wall.
- [ ] Technical names and arrows match the source.
- [ ] Bottom line exists.
- [ ] Text is readable at normal chat preview size.
