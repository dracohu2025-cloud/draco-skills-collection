# epub2podcast

`epub2podcast` 是一个把电子书内容整理成播客形态的本地工作流 skill。

它适合这样的场景：你手上有一本 EPUB / PDF / MOBI / AZW3，希望把它进一步处理成更适合收听和传播的内容，例如：

- 双人中文播客脚本
- 完整播客音频
- Smart Slide 视觉页
- 最终 MP4 视频

## 这个 skill 适合谁用

这个 skill 更适合下面这些用户：

- 已经有本地 `epub2podcast` 项目代码的人
- 想把“电子书 → 播客”流程标准化的人
- 想把这条工作流封装成可复用 skill 的 Hermes 用户
- 想在本地完成脚本、音频、页面和视频产出的人

如果你希望的是“下载这个目录后直接一键运行”，那它目前并不是一个完全独立的软件包，而更像是一个**建立在现有本地项目之上的 skill 封装**。

## 它能做什么

这个 skill 主要覆盖下面这条本地链路：

1. 读取 EPUB / PDF / MOBI / AZW3
2. 生成双人中文播客脚本
3. 生成分段音频并合成为完整音频
4. 生成 Smart Slide
5. 合成最终 MP4 视频
6. 在需要时压缩视频，方便后续分享或上传

## 开始之前要准备什么

在真正运行之前，你需要先准备好下面这些内容。

### 1）本地 `epub2podcast` 项目代码

你需要已经拥有可运行的本地项目目录，例如：

```bash
/path/to/epub2podcast-local/frontend/server
```

然后设置环境变量：

```bash
export EPUB2PODCAST_PROJECT_ROOT=/path/to/your/epub2podcast-local/frontend/server
```

这个 skill 目录里的脚本，会通过这个环境变量找到真正的项目代码并执行。

### 2）Node.js 和 npm

因为底层项目是 Node / TypeScript 运行链路，所以本机需要先安装：

- Node.js
- npm

### 3）ffmpeg / ffprobe

如果你要生成和处理最终音频、视频，本机通常需要：

- `ffmpeg`
- `ffprobe`

### 4）Chrome 或 Chromium

如果你要渲染 Smart Slide，通常还需要：

- Chrome
- 或 Chromium

它们主要给 Puppeteer 用于页面渲染和截图。

### 5）模型和 TTS 相关环境变量

如果你的本地 `epub2podcast` 项目依赖模型服务或 TTS 服务，那么对应环境变量也需要提前配置好。

常见会涉及：

- OpenRouter 相关配置
- Volcengine TTS 相关配置

具体变量名，以你实际使用的 `epub2podcast` 项目为准。

## 3 分钟快速开始

当你已经准备好本地项目和依赖后，可以按下面方式开始。

### 第一步：设置项目路径

```bash
export EPUB2PODCAST_PROJECT_ROOT=/path/to/your/epub2podcast-local/frontend/server
```

### 第二步：运行主脚本

```bash
bash scripts/epub2podcast_local_run.sh --epub ./book.epub
```

### 第三步：如果需要，重生成某一页 slide

```bash
bash scripts/epub2podcast_local_regenerate_slide.sh \
  --delivery-dir /path/to/delivery \
  --slide-index 0 \
  --recompose
```

### 第四步：如果视频太大，先压缩再分享

```bash
bash scripts/epub2podcast_local_compress_feishu_video.sh \
  --input /path/to/final_podcast.mp4 \
  --output /path/to/final_podcast_compressed.mp4
```

## 目录说明

当前目录包含：

- `SKILL.md`：完整的 skill 说明、推荐命令和经验总结
- `scripts/epub2podcast_local_run.sh`：主运行入口
- `scripts/epub2podcast_local_regenerate_slide.sh`：重生成单页 slide
- `scripts/epub2podcast_local_compress_feishu_video.sh`：压缩最终视频

## 常见问题

### 这个 skill 是不是下载后就能直接跑？

不是。

它依赖你本地已经有可运行的 `epub2podcast` 项目代码，以及对应的运行环境。

### 为什么 README 里要写这么多前置条件？

因为对外部用户来说，最容易踩坑的地方不是“命令怎么写”，而是：

- 本地有没有底层项目代码
- 依赖装没装
- 环境变量配没配
- Chrome / ffmpeg 是否可用

如果这些前提不清楚，别人很容易误以为这是一个开箱即用的独立工具。

### 如果只想重做某一页 slide，可以吗？

可以。

可以使用：

- `scripts/epub2podcast_local_regenerate_slide.sh`

### 如果最终 MP4 太大怎么办？

可以先使用：

- `scripts/epub2podcast_local_compress_feishu_video.sh`

把视频压缩后再上传或分享。

## 这个 skill 的边界

这个目录聚焦的是 **local-only** 路径，也就是：

- 本地生成脚本
- 本地生成音频
- 本地生成 Smart Slide
- 本地合成视频

它不负责远端服务调用，也不试图替代完整的线上系统。

## 想进一步了解

如果你想看更完整的命令、默认参数、实战经验和问题排查，可以继续看：

- `SKILL.md`
