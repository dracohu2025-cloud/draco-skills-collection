# epub2podcast

`epub2podcast` 是一个面向本地工作流的 skill，用来把电子书内容整理成更适合收听和传播的播客形态。

简单来说，它想解决的是这样一个问题：

> 手上有一本电子书，能不能把它进一步处理成“能听、能看、能分享”的播客内容？

这个 skill 提供的就是这样一条本地链路：

- 电子书 → 双人中文播客脚本
- 脚本 → 音频分段与完整音频
- 内容 → Smart Slide 页面
- 音频 + 页面 → 最终 MP4 视频

## 亮点摘要

如果你只想先快速了解这个 skill，可以先看这几条：

- **本地优先**：核心流程放在本地完成，更容易掌控产物和过程
- **产出完整**：不仅有脚本和音频，还有 Smart Slide 与最终视频
- **适合复用**：不是一次性命令，而是适合反复调用的 skill 封装
- **便于调整**：支持单独重做某一页 slide，也支持额外压缩最终视频
- **适合展示**：最终结果更适合传播、分享和二次整理

## 推荐使用场景

下面这些场景里，这个 skill 通常会比较有用：

- 你想把一本书快速整理成“可以听”的播客内容
- 你想把一本书进一步做成“可以看”的视频播客
- 你想把一条已经跑通的内容工作流封装成稳定 skill
- 你想在本地控制脚本、音频、页面和视频的完整产出
- 你需要一个适合继续扩展的 EPUB → Podcast 基础工作流

## 它适合什么场景

如果你遇到下面这些场景，这个 skill 会比较合适：

- 你想把一本书整理成播客节目
- 你想把文字内容变成更容易传播的视频内容
- 你已经有本地 `epub2podcast` 项目，希望把流程固定下来
- 你希望把“电子书 → 播客”的过程封装成可复用的 skill

## 它适合谁

这个 skill 更适合：

- 已经有本地 `epub2podcast` 项目代码的人
- 想把这条工作流沉淀下来的人
- 想复用成熟工作流的 Hermes 用户
- 想在本地掌控脚本、音频、页面和视频产出的人

如果你期待的是“下载这个目录后直接一键运行”，那它目前还不是一个完全独立的软件包，而是一个**建立在现有本地项目之上的 skill 封装**。

## 它能产出什么

在典型流程里，这个 skill 会帮助你得到：

- 双人中文播客脚本
- 分段音频
- 合并后的完整播客音频
- Smart Slide 图片
- Smart Slide HTML 源文件
- 最终 MP4 视频
- 必要时可进一步压缩的视频文件

## 工作流程图

下面这张流程图可以帮助你快速理解整个处理链路：

```mermaid
flowchart LR
    A[EPUB / PDF / MOBI / AZW3] --> B[解析图书内容]
    B --> C[生成双人中文播客脚本]
    C --> D[生成分段音频]
    D --> E[合并为完整播客音频]
    C --> F[生成 Smart Slide HTML]
    F --> G[渲染 Smart Slide 图片]
    E --> H[合成最终 MP4 视频]
    G --> H
    H --> I[按需压缩视频]
```

如果用更直白的话来说，就是：

- 先把电子书内容读出来
- 再生成播客脚本
- 一路产出音频
- 一路产出页面
- 最后把音频和页面合成视频
- 如果视频太大，再额外压缩一版

## 示例效果

下面放两张实际生成的 Smart Slide 示例图，帮助你快速理解这个 skill 可能产出的视觉风格。

### 示例 1：封面页风格

![epub2podcast 示例封面页](./assets/example-slide-cover.png)

这类页面更适合做视频开场、书籍介绍或主题引入。

### 示例 2：信息图风格

![epub2podcast 示例信息图页](./assets/example-slide-infographic.png)

这类页面更适合把一个主题拆成结构化信息，用于解释观点、梳理层次或做中段内容展示。

## 使用前提（Prerequisites）

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

这个 skill 目录中的脚本会通过这个环境变量，找到真正的项目代码并执行。

### 2）Node.js 和 npm

因为底层项目是 Node / TypeScript 运行链路，所以本机通常需要：

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

如果你的本地 `epub2podcast` 项目依赖模型服务或 TTS 服务，那么这些环境变量也需要提前配置好。

常见会涉及：

- OpenRouter 相关配置
- Volcengine TTS 相关配置

具体变量名，以你实际使用的本地 `epub2podcast` 项目为准。

## 安装前检查清单

在开始前，建议先快速确认下面这些项目：

- [ ] 已有可运行的本地 `epub2podcast` 项目代码
- [ ] 已设置 `EPUB2PODCAST_PROJECT_ROOT`
- [ ] 本机已安装 Node.js 和 npm
- [ ] 本机已安装 `ffmpeg` / `ffprobe`
- [ ] 本机已安装 Chrome 或 Chromium
- [ ] 所需模型 / TTS 环境变量已配置完成

如果这几项里有任何一项没准备好，后面运行时大概率会报错。

## 3 分钟快速开始

当你已经准备好项目和依赖之后，可以按下面方式开始。

### 第一步：设置项目路径

```bash
export EPUB2PODCAST_PROJECT_ROOT=/path/to/your/epub2podcast-local/frontend/server
```

### 第二步：运行主脚本

```bash
bash scripts/epub2podcast_local_run.sh --epub ./book.epub
```

### 第三步：如果某一页 slide 效果不理想，就单独重做

```bash
bash scripts/epub2podcast_local_regenerate_slide.sh \
  --delivery-dir /path/to/delivery \
  --slide-index 0 \
  --recompose
```

### 第四步：如果视频太大，就先压缩

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

### 为什么这里不是直接附上完整项目代码？

因为这里的定位是 **skill 封装**，不是完整项目镜像。

它更适合放：

- 工作流说明
- 推荐命令
- 运行入口脚本
- 实战经验总结

而不是把整个底层项目直接复制进来。

### 如果只想重做某一页 slide，可以吗？

可以。

可以使用：

- `scripts/epub2podcast_local_regenerate_slide.sh`

### 如果最终 MP4 太大怎么办？

可以使用：

- `scripts/epub2podcast_local_compress_feishu_video.sh`

先把视频压缩后再上传或分享。

## 常见报错与排查思路

### 1. 提示没有设置 `EPUB2PODCAST_PROJECT_ROOT`

说明脚本找不到底层项目代码。

先执行：

```bash
export EPUB2PODCAST_PROJECT_ROOT=/path/to/your/epub2podcast-local/frontend/server
```

然后再重新运行脚本。

### 2. 提示 `npm`、`node`、`ffmpeg` 或 `ffprobe` 不存在

说明本机依赖还没装好。

优先检查这些命令是否可用：

```bash
node -v
npm -v
ffmpeg -version
ffprobe -version
```

### 3. Smart Slide 生成失败

通常优先检查：

- Chrome / Chromium 是否可用
- Puppeteer 依赖是否正常
- 页面渲染环境是否齐全

### 4. 音频或脚本生成失败

通常优先检查：

- 模型服务相关环境变量是否正确
- TTS 相关环境变量是否正确
- 本地项目本身是否已经能独立跑通

### 5. 视频太大，上传困难

这是比较常见的问题。

可以先使用压缩脚本，把 MP4 压小以后再上传或分享。

## 这个 skill 的边界

这个目录聚焦的是 **local-only** 路径，也就是：

- 本地生成脚本
- 本地生成音频
- 本地生成 Smart Slide
- 本地合成视频

它不负责远端服务调用，也不试图替代完整的线上系统。

## 想进一步了解

如果你想看更完整的命令、默认参数、经验总结和问题排查，可以继续看：

- `SKILL.md`
