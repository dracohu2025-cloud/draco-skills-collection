# epub2podcast

`epub2podcast` 是一个面向本地工作流的 skill，用来把电子书内容整理成更适合收听和传播的播客形态。

简单来说，它想解决的是这样一个问题：

> 手上有一本电子书，能不能把它进一步处理成“能听、能看、能分享”的播客内容？

这个 skill 提供的就是这样一条本地链路：

- 电子书 → 双人中文播客脚本
- 脚本 → 音频分段与完整音频
- 内容 → Smart Slide 页面
- 音频 + 页面 → 最终 MP4 视频

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

## 示例效果

下面是一张实际生成的 Smart Slide 示例图，可以帮助你快速理解这个 skill 最终会产出什么样的视觉结果：

![epub2podcast 示例封面页](./assets/example-slide-cover.png)

> 说明：这里展示的是一张示例封面页，主要用于说明产出风格与版式效果。

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
