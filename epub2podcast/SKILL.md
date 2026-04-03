---
name: epub2podcast-standalone
description: 可独立运行的 standalone 版 EPUB2Podcast：用户只需下载当前项目本身，即可在本地把 EPUB 转成 Smart Slide + 双人中文音频 + 最终 MP4 视频播客。
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [epub, podcast, smart-ppt, smart-slide, tts, video, mp4, standalone]
---

# EPUB2Podcast Standalone

这个 skill 对应的是 **standalone 版本** 的 epub2podcast 管线。用户只需要下载当前项目本身，就可以把 EPUB 转成：

- 双人中文播客脚本
- 分段音频
- 合并音频 `full_podcast.mp3`
- Smart Slide 图片
- Smart Slide HTML 源文件
- 最终视频播客 `final_podcast.mp4`
- 营销文案与 metadata

## 版本边界

为了避免混淆，这里明确区分三个版本：

- **remote 版**：调用远端运行中的 epub2podcast 服务，由远端项目实际生产结果
- **local 版**：依赖另一份本地 `epub2podcast-local` 源码目录，由 skill/wrapper 去调用那个项目
- **standalone 版（当前 GitHub 目录唯一保留的版本）**：当前目录自带独立源码、独立 package、独立 CLI，不依赖外部项目路径

**当前 GitHub 仓库中的 `epub2podcast/` 只对应 standalone 版本，不再把 local / remote 版 skill 一起放进去。**

## 核心原则

- **本地运行**
- **独立运行**（不依赖外部 `EPUB2PODCAST_PROJECT_ROOT`）
- **不依赖 Supabase 持久化**
- **不调用远端运行中的 epub2podcast 服务**
- 交付物优先落本地目录，后续可再上传飞书
- 首屏书籍封面应优先走**本地文件 + 本地 HTTP 临时地址**，避免直接把超长 base64 塞进 HTML 导致模型输出截断、封面缺失

## 当前默认配置

- `language=Chinese`
- `imageStyle.preset=smart_ppt`
- `imageStyle.colorTheme=gq_fashion`
- `imageStyle.pptModel=google/gemini-3-flash-preview`
- `apiProvider=openrouter`
- `textModel=gemini-3-flash`
- 中文 TTS 默认走 `volcengine`
- 对 `smart_ppt` / `antv_infographic` 模式，脚本生成现在会同时启用：
  - **长书多章节采样输入**（不再只吃书前 200k 字）
  - **更严格的 prompt 约束**（覆盖开头/中段/结尾）
  - **硬校验与自动重试**（段数、文本长度、预估时长不达标就失败重试）

## 依赖

当前机器需要：
- Node.js
- npm
- ffmpeg / ffprobe
- Chrome / Chromium（供 Puppeteer 截图 Smart Slide）
- OpenRouter / Volcengine 等环境变量

> 注意：本公开版 skill **不会包含任何真实 API key、token、secret 或私有凭证**；相关环境变量需由使用者自行提供。

## 推荐命令

主命令：
- `epub2podcast-local-run`
- `epub2podcast-local-regenerate-slide`（只重生某一页，可选自动重合成 mp4）
- `epub2podcast-local-compress-feishu-video`（把最终 mp4 压到更适合飞书上传的体积）

### 1) 最简单

```bash
epub2podcast-local-run --epub ./book.epub
```

### 2) 指定输出目录

```bash
epub2podcast-local-run --epub ./book.epub --output-dir ./deliveries
```

### 3) 覆盖主题或模型

```bash
epub2podcast-local-run \
  --epub ./book.epub \
  --output-dir ./deliveries \
  --color-theme gq_fashion \
  --ppt-model google/gemini-3-flash-preview \
  --text-model gemini-3-flash
```

### 4) 只重生某一页，并可选重合成视频

```bash
epub2podcast-local-regenerate-slide \
  --delivery-dir /path/to/delivery \
  --slide-index 0 \
  --recompose \
  --color-theme gq_fashion \
  --ppt-model google/gemini-3-flash-preview
```

说明：
- `--slide-index 0` 用于首页/封面页
- 首页会自动把 `metadata/book.json` 中的 `coverImageBase64` 落地到本地 `assets/cover.*`，并通过**本地 HTTP 临时地址**喂给 Puppeteer 渲染
- `--recompose` 会基于现有 `full_podcast.mp3 + smart_slides/*.png` 重写 `final_podcast.mp4`
- 不传 `--recompose` 时，只更新指定页的 PNG 和 HTML

### 5) 为飞书上传压缩 mp4

```bash
epub2podcast-local-compress-feishu-video \
  --input /path/to/final_podcast.mp4 \
  --output /path/to/final_podcast_feishu.mp4
```

默认压缩策略：
- 保持原始分辨率与比例（例如 4:3 的 1440x1080）
- `libx264`
- `-preset medium`
- `-crf 27`
- `-maxrate 2200k -bufsize 4400k`
- 音频 `aac -b:a 96k`

适用场景：
- 当 `lark-cli drive +upload` 因 **20MB** 限制无法上传最终 mp4 时
- 先压出一个 `*_feishu.mp4`，再上传到用户指定的飞书云盘文件夹

## 交付目录结构

输出目录通常包含：

- `source/`
- `audio_segments/`
- `smart_slides/`
- `smart_slides_html/`
- `metadata/book.json`
- `metadata/script.json`
- `metadata/marketing.json`
- `full_podcast.mp3`
- `final_podcast.mp4`
- `manifest.json`

默认视频合成为 **4:3 的 1440x1080**（保持当前 slide 比例不变，不拉伸到 16:9）。

## 实战经验补充

### 持久输出目录优先

不要把交付目录默认放在 `/tmp`。

原因：
- `/tmp` 下的 delivery 目录可能在会话后被清理
- 后续如果要做“只重生某一页”“重新合成视频”“补传飞书”，会失去中间产物

推荐使用持久目录，例如：

```bash
/home/ubuntu/deliveries/epub2podcast-local
```

### 飞书上传限制（当前 lark-cli 路径）

`lark-cli drive +upload` 当前路径对单文件有 **20MB 限制**。

这意味着：
- `full_podcast.mp3`、封面图、单张 slide 通常可直接上传
- `final_podcast.mp4` 若超过 20MB，可能上传失败

典型错误：

```text
file 23.9MB exceeds 20MB limit
```

遇到这种情况时：
1. 先上传 `mp3 / cover / 首图 / manifest / metadata`
2. 再决定是否：
   - 重新压缩 mp4 到 20MB 以下
   - 或改走别的交付通道

## 脚本生成保障（2026-04 更新）

针对 `smart_ppt` / `antv_infographic` 模式，当前本地管线已经补上三层保障，用于避免“只生成 6-7 分钟短播客、只覆盖书前半部分”的问题：

1. **长书输入覆盖**
   - 不再简单只截取书前 200k 字作为脚本生成输入
   - 优先使用章节级输入：完整章节大纲 + 按全书均匀采样的章节摘录
   - 强制提示模型覆盖开头 / 中段 / 结尾，而不是只围绕前几章

2. **更严格的 smart_ppt 约束**
   - 明确要求输出 `18-22` 段
   - 中文场景下要求更高的对话密度（至少约 `3200` 中文字符，推荐更高）
   - 明确要求脚本覆盖多个章节 / 主题 / 对象，而不是只讲第一个案例

3. **硬校验 + 自动重试**
   - 生成后做程序化质量闸门：
     - 段数是否在 `18-22`
     - 对话总长度是否达标
     - 预估时长是否至少约 `10 分钟`
     - 是否存在过多过短 segment
   - 不达标则直接判失败，交由脚本生成重试逻辑继续尝试

### 验证结果（真实案例）

在《十件古物中的丝路文明史》样本上：
- 修复前：`13` 段，约 `6分39秒`
- 修复后：`18` 段，约 `14分10秒`

因此，当用户反馈“播客太短”时，优先检查是否走到了上述新逻辑；如果没有，先同步代码或重建产物，再重新运行。

## 已知问题与排查

### 首屏缺少书籍封面（local 版常见）

如果用户反馈：
- 本地版 `final_podcast.mp4` 第一页右侧没有封面
- 但另一个实现路径同一本书第一页有封面

优先按下面顺序排查：

1. 检查 `metadata/book.json` 是否存在 `coverImageBase64`
   - 如果存在，说明 **EPUB 解析阶段已经成功提取封面**，问题不在 parser。
2. 检查 `smart_slides_html/000.html`
   - 搜索是否有 `<img class="book-cover" ...>`
   - 如果 HTML 里有 `<img src="data:image/...;base64,...">`，但最终 PNG / MP4 里看不到封面，说明问题出在 **HTML -> Puppeteer 渲染链路**。

### 经验结论

在当前这套 local 管线里：

- **直接把超长 base64 data URI 塞进第一页 `<img src>` 不够稳**
- 可能出现：
  - LLM 生成的 HTML 里明明有 `<img>`
  - 但 Puppeteer `page.setContent()` 后，最终 DOM/截图里封面消失

这会导致：
- `smart_slides_html/000.html` 看起来有封面代码
- `smart_slides/000.png` 和最终 `mp4` 却没有封面

### 推荐修法

把 local 管线进一步稳固：

- **不要直接把 `coverImageBase64` 传给第一页 prompt**
- 先把封面落成一个可访问资源，再传 URL

推荐优先级：

1. 最稳：启动一个本地 HTTP 可访问地址，再传 `http://.../cover.jpg`
2. 若项目允许外部存储：上传到对象存储/云存储，传公开 URL
3. 不推荐继续直接传超长 `data:image/...;base64,...`

### 调试提示

若要快速确认是不是这个问题：

- 用视觉或直接检查 `smart_slides/000.png`，确认右侧是否空白
- 再检查 `smart_slides_html/000.html` 是否仍然包含 `<img>`
- 如果 HTML 有 `<img>`、最终图片无封面，基本就能锁定为 **local 首屏封面资源引用方式不对**

### 播客时长明显偏短（例如只有 6-8 分钟）

如果用户反馈：
- 一本正常长度的书只生成了很短的播客
- 预期应该在 10-15 分钟甚至更长
- 怀疑不同运行路径逻辑不一致

优先检查以下几点：

1. `metadata/script.json` 的段数与总文本量
   - 当前经验：如果只有 `12-13` 段、总文本很短（例如 2000 多中文字符），最终时长通常会落到 6-8 分钟
2. `src/services/scriptService.ts` 的真实验收逻辑
   - prompt 虽然要求 **15 分钟 / 4500 words / 18-22 segments**
   - 但某些模型分支若只做极弱校验，13 段短文本也可能被直接放行
3. 输入给脚本生成模型的正文是否被截断
   - 如果只把正文前 `200000` 字符送入模型，长书就容易只覆盖前半本内容，覆盖度和时长都会受影响

### 对这个问题的经验结论

当用户说“播客应该至少 10 分钟，为什么这么短”时，优先怀疑：

- **脚本生成约束只写在 prompt 里，没有代码级强验收**
- **长书输入被前 200k 字符截断，导致覆盖范围不足**

而不是优先怀疑：
- ffmpeg 合成
- TTS 合成
- 封面页逻辑

### 建议修法

1. 在脚本生成后增加**硬校验**：
   - 段数必须在 `18-22`
   - 总文本长度达到阈值
   - 预估总时长达到阈值（例如至少 10 分钟）
2. 若不满足，自动重试或切更强模型，而不是直接进入 TTS
3. 不要只使用前 200k 字符；长书应改为：
   - 章节摘要后再生成，或
   - 从全书多段采样，避免内容只集中在前半本

## 自然语言触发建议

当用户说：
- “把这个 EPUB 做成带 Smart Slide 的视频播客”
- “生成双人音频 + 最终 mp4”
- “本地跑 epub2podcast，不要依赖 Supabase”

优先使用本 skill。
