# epub2podcast

一个**可独立运行**的本地项目：把 EPUB 内容转换成双人中文播客脚本、音频、Smart Slide，以及最终 MP4 视频。

> 现在这份目录已经不再依赖外部 `epub2podcast-local` 项目路径。下载当前目录、安装依赖、配置 `.env` 后，就可以直接运行。

---

## 你能用它做什么

`epub2podcast` 当前最稳的工作流是：

- 读取 **EPUB** 文件
- 生成双人中文播客脚本
- 生成分段音频并合并为完整音频
- 生成 Smart Slide HTML 与 PNG
- 合成最终 MP4 视频
- 按需压缩视频，便于上传或分享

如果你想把一本书快速整理成“可听、可看、可传播”的内容，这就是它最适合做的事。

---

## 适合谁

这个项目特别适合：

- 想把一本 EPUB 做成中文播客的人
- 想把文字内容进一步做成视频播客的人
- 想在本地掌控脚本、音频、页面和视频产出的人
- 想把“电子书 → 播客”做成可复用流程的人

---

## 示例效果

### 示例 1：封面页风格

![epub2podcast 示例封面页](./assets/example-slide-cover.png)

### 示例 2：信息页风格

![epub2podcast 示例信息页](./assets/example-slide-infographic.png)

---

## 工作流程

```mermaid
flowchart LR
    A[EPUB 文件] --> B[解析图书内容]
    B --> C[生成双人中文播客脚本]
    C --> D[生成分段音频]
    D --> E[合并完整播客音频]
    C --> F[生成 Smart Slide HTML]
    F --> G[渲染 Smart Slide PNG]
    E --> H[合成最终 MP4 视频]
    G --> H
    H --> I[按需压缩视频]
```

---

## 安装前准备

### 系统依赖

请先确认本机已安装：

- Node.js 20+
- npm
- `ffmpeg`
- `ffprobe`
- Chrome / Chromium

### 环境变量

你至少需要准备以下能力对应的密钥：

- 文本/HTML 生成：通常使用 `OPENROUTER_API_KEY`
- 中文 TTS：通常使用火山引擎（Volcengine）相关变量

项目里已经附带：

- `.env.example`

你可以复制它来开始配置。

---

## 快速开始

### 1. 安装依赖

```bash
cd epub2podcast
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

然后按你的实际账号信息填写 `.env`。

### 3. 构建项目

```bash
npm run build
```

### 4. 运行主流程

```bash
node dist/cli/run.js --epub ./book.epub --output-dir ./deliveries
```

或者使用脚本入口：

```bash
bash scripts/epub2podcast_local_run.sh --epub ./book.epub --output-dir ./deliveries
```

---

## 常用命令

### 查看主命令帮助

```bash
node dist/cli/run.js --help
```

### 从 EPUB 生成完整交付物

```bash
node dist/cli/run.js --epub ./book.epub --output-dir ./deliveries
```

### 重生成某一页 slide

```bash
node dist/cli/regenerate-slide.js \
  --delivery-dir /path/to/delivery \
  --slide-index 0 \
  --recompose
```

### 压缩最终视频

```bash
node dist/cli/compress-video.js \
  --input /path/to/final_podcast.mp4 \
  --output /path/to/final_podcast_compressed.mp4
```

### 环境检查

```bash
npm run smoke-test
```

---

## 输出内容

一次成功运行后，输出目录中通常会包含：

- `source/`：输入书文件副本
- `audio_segments/`：分段音频
- `smart_slides/`：Slide PNG
- `smart_slides_html/`：Slide HTML
- `full_podcast.mp3`：完整播客音频
- `final_podcast.mp4`：最终视频

---

## 当前状态

### 已验证

当前 standalone 版本已经完成过真实端到端验证，验证通过的链路包括：

- 主流程：EPUB → 脚本 → 音频 → Slide → MP4
- 单页重生成：`regenerate-slide`
- 视频压缩：`compress-video`

### 当前最稳的输入类型

- **EPUB**

### 还会继续完善的方向

- 更完整的 PDF / MOBI / AZW3 支持
- 更少的历史依赖
- 更统一的 CLI 参数设计
- 更完善的错误提示和自动检查

---

## 常见问题

### 现在还需要原始 `epub2podcast-local` 项目吗？

**不需要。**

当前这个目录已经具备独立安装、独立构建和独立运行能力。

### 是不是下载后就能直接跑？

原则上是，但前提是：

- 系统依赖已安装
- `.env` 已配置
- 你使用的是当前最稳的输入路径（推荐 EPUB）

### 如果最终 MP4 太大怎么办？

可以直接运行：

```bash
node dist/cli/compress-video.js --input /path/to/final_podcast.mp4
```

### 如果只想重做某一页 slide，可以吗？

可以：

```bash
node dist/cli/regenerate-slide.js --delivery-dir /path/to/delivery --slide-index 0 --recompose
```

---

## 排查建议

### 找不到 `ffmpeg` / `ffprobe`

先检查：

```bash
ffmpeg -version
ffprobe -version
```

### `.env` 没配好

先重点检查：

- `OPENROUTER_API_KEY`
- `VOLCENGINE_ACCESS_TOKEN`
- `VOLCENGINE_APP_ID`
- `VOLCENGINE_VOICE_ID_MALE`
- `VOLCENGINE_VOICE_ID_FEMALE`

### Smart Slide 生成失败

优先检查：

- Chrome / Chromium 是否可用
- Puppeteer 是否安装正常
- 当前机器能否访问所需模型服务

---

## 目录结构

```text
epub2podcast/
├── README.md
├── SKILL.md
├── package.json
├── tsconfig.json
├── .env.example
├── assets/
├── scripts/
└── src/
```

其中：

- `src/`：独立运行所需源码
- `scripts/`：方便调用的 shell 入口
- `assets/`：README 示例图
