---
name: gpt-image-2-paper-ppt-images
description: Use when generating PPT-style image slides, poetic presentation covers, quiet paper-texture visual pages, report pages, invitations, social cards, or slide-image sets with GPT-Image-2 via image_generate.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [gpt-image-2, image-generation, ppt, slides, paper-texture, visual-design, presentation]
    related_skills: [gpt-image-2-handdrawn-diagram, baoyu-infographic, ppt-keynote]
    source_author: 小小东
    source_homepage: https://x.com/xiaoxiaodong01
    source_post: https://x.com/xiaoxiaodong01/status/2056615926724976911
    source_posts:
      - https://x.com/xiaoxiaodong01/status/2056615926724976911
      - https://x.com/xiaoxiaodong01/status/2056412276593410537
---

# GPT-Image-2 Paper PPT Images

## Overview

This skill generates PPT-style image pages with a light, quiet, paper-breathing visual language.

Use Hermes `image_generate` for rendering. Configure `image_generate` to use GPT-Image-2, then call it directly unless the user explicitly asks for another image backend.

Source credit: 小小东 — https://x.com/xiaoxiaodong01

Source posts:

- Paper-breathing PPT / soft visual nodes: https://x.com/xiaoxiaodong01/status/2056615926724976911
- Eastern editorial PPT / booklet-page layouts: https://x.com/xiaoxiaodong01/status/2056412276593410537

The style is useful for:

- PPT covers and section dividers
- lecture / course pages
- report pages
- poetic information graphics
- invitations
- social cards
- product / person / menu / exhibition guide pages

The goal is not a normal slide template. The goal is **quiet paper texture + soft floating visual nodes + restrained typography + strong whitespace control**.

## When to Use

Use this skill when the user asks for:

- PPT 式图片
- 一套 PPT 图片 / 课件图 / 报告页
- 轻盈安静的海报 / 封面 / 邀请函
- 带纸张呼吸感的视觉页
- GPT-Image-2 PPT prompt
- 把一个主题做成多张可直接放进 PPT 的图片

Do not use for editable `.pptx` production. If the user needs an editable PowerPoint file, use the PowerPoint / slide-generation skills instead.

## Template Selection

This skill contains multiple GPT-Image-2 prompt templates under one shared PPT-image workflow. Pick by intent:

- **Template A — Paper Breath / Soft Nodes**: default for poetic PPT covers, quiet report pages, course pages, invitations, and social cards with floating visual nodes.
- **Template B — Eastern Editorial / Booklet Page**: use when the user wants 东方编辑感, 米纸/淡墨/陈木, Chinese editorial layout, restrained booklet-page PPT, tea/craft/culture/architecture/product/report visuals, or a calmer premium deck.

If the user only says “PPT 风格图片” and gives no style, use Template A. If the topic has cultural, craft, tea, humanities, architecture, heritage, or editorial-publication flavor, prefer Template B.

## Core Visual Grammar

Lock these shared properties:

1. **Paper atmosphere**: warm white or pale gray-white background, subtle grain, fiber, old-film softness.
2. **Soft visual nodes**: objects, people fragments, data points, symbols, or abstract shapes float like misted color masses.
3. **Single-family color**: one main color system; accent color only in tiny details, labels, numbers, or texture anchors.
4. **Sparse rhythm**: objects scattered but intentional, following a diagonal, arc, breathing path, or asymmetrical balance.
5. **Typographic restraint**: small corner metadata, page number, date, vertical Chinese / Japanese / numbers / chapter words; title does not need to be huge.
6. **Quiet intelligence**: low voice, slightly strange, soft and sharp at once; whitespace matters more than decoration.

## Template A — Paper Breath / Soft Nodes

Use this as the default base template. Replace the final topic and usage fields with the user's actual content.

```markdown
请把画面处理成一种轻盈、安静、带纸面呼吸感的视觉作品：大面积温白或浅灰白背景像细颗粒印刷纸，略有噪点、纤维和柔和的旧胶片质感，不要做成干净塑料感或高饱和商业海报。主体不必照搬蓝莓，可以是任何与当前内容相关的物件、信息节点、人物局部、产品、数据点、概念符号或抽象形状，但它们应像柔软的色团一样悬浮在画面里，边缘被轻微雾化，中心有更深的色值，外圈向背景自然扩散，形成“靠近才发现层次”的细腻渐变。每个主体最好带一个小而清晰的暗部细节、切口、星形、标签、符号、编号或纹理锚点，让模糊的色团有记忆点，也让视线能从一个点跳到另一个点。

色彩遵循参考图的角色关系，而不是固定复制紫色。背景承担空气和留白，保持低饱和、偏温、轻颗粒；主体色根据内容气质改变，可以变得更学术、更清洁、更甜润、更锋利、更复古或更技术，但仍保持单一主色系的柔雾渐层，不要彩虹化。强调色只占很小面积，用在主体的中心、边缘细节、关键数字或微小标注上，负责情绪转折和阅读停顿。文字色使用低饱和的橄榄灰、旧金、烟褐、墨灰或与主题相称的沉静深色，像印在纸上的细线，而不是抢眼标题。阴影和深度也从主色内部生成，靠透明度、颗粒、模糊半径和轻微叠色形成层次。

版式要有明确的空白控制：主体散落但不是随机，整体沿一条隐约的斜向、弧线或呼吸式阅读路径移动，形成上轻下稳、左松右紧或中部漂浮的节奏。对象之间保持距离，让每个色团周围有安静的空气；可以有局部靠近、错位或轻微重叠，但不要排成机械网格。文字是画面结构的一部分：角落放置很小的英文、日期、页码、署名或元信息；一侧可以使用竖排中文、日文、数字、章节名或关键词，笔画细、间距松、像边界线一样拉住画面。标题不需要巨大，必要时让短句、竖排字、数字和注释成为构图重心的反向平衡。所有文字都要克制、清晰、留有边距，像设计学院作业、独立出版物、视觉实验海报或诗性信息图，而不是模板封面。

整体气质应是低声的、聪明的、有一点奇异感：少量颜色在白纸上发光，柔软和尖锐并存，空白比装饰更重要。适用于海报、PPT封面、报告页、信息图、排行榜、数据可视化、产品页、人物介绍、菜单、展览导视或社交卡片时，都把内容转化为若干有呼吸的视觉节点，用轻颗粒、雾化色彩、边缘文字和稀疏节奏组织阅读。现在把这种美学用于我的实际内容，让画面自然长成它需要的形式。

本次主题：
{主题}

每页的信息你自己规划
——————
用途：ppt、课件，最少10张ppt
```

## Template B — Eastern Editorial / Booklet Page

Use this template when the deck should feel like a refined Chinese editorial booklet: quiet, restrained, publication-grade, with rice paper, pale ink, warm wood, moon-gate / arch / folding-fan / lifted-page windows, sparse line drawings, and modern information hierarchy.

Source: 小小东 — https://x.com/xiaoxiaodong01/status/2056412276593410537

```markdown
请把画面处理成一种安静、克制、带有东方编辑感的高级视觉：它像一页被精心排过的纸本册页，又能自然适应现代信息设计。整体不要追求炫技和饱满，而要让留白成为主要结构，让内容在米纸、浅灰、淡墨、温润木色之间缓慢显形。画面可以有一两个柔和的图像窗口，像拱门、月洞、折扇或被风掀开的纸页，以大曲线切开空间，让照片、插图、数据或文字像被安放在旧院落的一角；这些窗口不必对称，边缘要干净，比例要有呼吸感，避免硬盒子、廉价圆角卡片和过度装饰。

如果出现影像，尽量让它带有低饱和、微雾、柔焦、侧光和时间感，像茶席、器物、手作、建筑、植物、文献或人物的一个片段，而不是完整说明一切。物体可以少，位置要准，宁可只露出半盏、一段桌面、一层纸纹、一束线描，也不要堆满素材。线描元素应像手边随笔留下的细线，轻、准、留有空隙，可用于手势、花枝、器物、路径、关系或隐喻，但不能变成花哨插画。色彩保持温和而有层次，主色接近宣纸和陈木，辅以墨灰、烟绿、茶褐、陶土、暗金或极淡的冷灰；任何醒目的颜色都应像印章或小标记，只承担必要的强调。

文字是画面气质的一部分，而不是贴上去的说明。中文可以有竖排、窄列、细长分行、古籍式停顿，也可以和现代无衬线数字、英文小字形成距离感；标题要像一块安静的重石，正文要像低声叙述，数字、日期、排名、图例、注释和索引要被整理成细线、短横、微小刻度或稀疏坐标。不要使用模板化的信息块，不要把所有内容平均分配到网格里，要让主次像书页气口一样自然形成：一处大留白，一处沉静主体，几组细小信息，少量线条把它们轻轻牵住。

当内容是PPT或报告，页面要像一组可翻阅的章节，每页只承担一个清晰判断，信息密度可以高，但必须有静气和秩序；当内容是信息图或数据可视化，图表应像墨线、案几、器物边缘或折页刻度那样被简化，重点数字要被安放而不是喊出；当内容是封面、海报、社媒卡片或排行榜，要让标题、图像和信息之间保持可被凝视的距离，既有东方审美的含蓄，也有现代编辑的准确。避免复古仿品感、茶文化套壳、空洞禅意、AI油亮质感、堆砌书法和廉价国风素材；它应该更像一种成熟的版面判断：淡、准、疏、稳，视觉很轻，但每个位置都有分量。

现在把这种美学用于我的实际内容：请根据我接下来提供的主题、文字、数据或用途，让画面自然长成它需要的形式，在静默留白中建立清晰的信息层级与可记住的视觉气质。

本次主题：
{主题}

用途：ppt、课件，不低于10张。每页信息和知识点由你规划，要求有趣、有料、生动。
```

## Template B Adaptation Rules

- Use for topics with humanities, tea, craft, culture, architecture, place, people, brand story, report, exhibition, or editorial mood.
- Prefer rice-paper background, pale ink, warm wood, smoke green, tea brown, terracotta, dark gold, and very pale cool gray.
- Use one or two soft image windows, not many cards.
- For data pages, simplify charts into ink lines, fold marks, sparse coordinates, or object-edge metaphors.
- Avoid fake retro, empty Zen, shiny AI texture, piled calligraphy, cheap guofeng assets, and tea-culture cosplay.

## Practical Adaptation for Hermes `image_generate`

`image_generate` returns one image per call. For a multi-page PPT image set, do **not** ask one call to generate 10 tiny slides in one canvas.

Instead:

1. Create a slide plan first.
2. Render each page separately with `image_generate`.
3. Keep the same art direction across all pages.
4. Put `Page N / Total` and a small metadata line in each page prompt.
5. Use `aspect_ratio='landscape'` for normal PPT 16:9.

## Deck Planning Rules

For `N` pages, use this common structure unless the user specifies otherwise:

1. Cover: topic, short poetic subtitle, key visual node.
2. Context: why this topic matters.
3. Main object / person / concept.
4. Timeline / mechanism / relationship.
5. Detail page: one quiet close-up with small labels.
6. Data / comparison / map / ranking if useful.
7. Tension or contradiction.
8. Interpretation / insight.
9. Summary page.
10. Closing / quote / bottom line.

For fewer pages, compress. For more pages, expand sections 3-8.

## Per-Page Prompt Format

Use this compact prompt block inside the canonical template:

```markdown
本次主题：
<deck topic>

页面：<N>/<TOTAL>
页面标题：<short title>
页面目的：<what this page should make the viewer understand>
可见文字：
- <main title or short phrase>
- <small metadata / date / page number>
- <1-3 short labels only>
视觉节点：
- <object / person detail / concept symbol / data node>
- <texture anchor or tiny accent detail>
构图：<diagonal / arc / left-loose-right-tight / floating center / top-light-bottom-stable>
色彩：<single main color family + tiny accent>
用途：PPT 16:9 单页图片
```

## One-Shot Single Image Mode

If the user wants only one PPT-style image, generate one page:

- default aspect ratio: `landscape`
- include 1 title, 1 subtitle, up to 3 labels
- no dense paragraphs
- use the canonical prompt directly with the user's topic

## Text Rules

GPT image models can distort long text. Keep visible text short:

- title: 4-12 Chinese characters or short English phrase
- subtitle: 1 short sentence
- labels: 1-3 items
- metadata: tiny but legible, e.g. `PAGE 03 / NOTES`

Avoid:

- paragraphs
- dense tables
- tiny legends
- long Chinese explanations
- copy-heavy slide bodies

If the user needs accurate long text, generate a cleaner background image first, then add text with a local HTML/SVG/PPT pipeline.

## Assembly Workflow

1. Extract topic, audience, page count, aspect ratio, language, and any required facts.
2. If page count is missing and user asks for a PPT set, default to 10 pages.
3. Build a page plan with titles and visual nodes.
4. For each page, assemble the canonical prompt + per-page block.
5. Call `image_generate` per page.
6. Save or report image paths in page order.
7. Visually inspect generated images before delivery when possible.

## Recommended Defaults

- Aspect: `landscape` / 16:9
- Language: user's language; keep technical names in English
- Page count: 10 for PPT sets, 1 for single cover/card
- Background: warm white or pale gray-white paper
- Typography: restrained, small metadata, optional vertical text
- Color: one main soft color family; tiny accent only

## Pitfalls

1. **One image cannot be a readable 10-slide deck**: render pages separately.
2. **Too much text ruins the style**: keep visible text minimal.
3. **High-saturation poster drift**: explicitly reject plastic, neon, glossy commercial poster style.
4. **Mechanical grid drift**: ask for scattered-but-intentional rhythm, not grid cards.
5. **Random blobs**: every soft color mass needs a small anchor detail: cut, label, symbol, number, texture, or dark core.
6. **Inconsistent deck style**: repeat the same color family, paper texture, metadata style, and visual rhythm across all pages.
7. **Attribution**: keep source credit to 小小东 when packaging or publishing this skill.

## Verification Checklist

- [ ] Image(s) generated via `image_generate`.
- [ ] 16:9 landscape used for PPT pages unless otherwise requested.
- [ ] Each page has short, readable text only.
- [ ] Visual nodes have soft fogged edges plus small anchor details.
- [ ] Background has paper grain / breathing whitespace.
- [ ] Deck pages share a consistent visual system.
- [ ] Source credit remains in the skill documentation.
