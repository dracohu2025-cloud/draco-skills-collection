# epub2podcast

这是一个基于 **本地链路** 的 `epub2podcast` skill。

它的目标是：把一本电子书整理成更适合传播的播客内容，包括脚本、音频、Smart Slide 和最终视频。

## 这个 skill 能做什么

它主要覆盖下面这条本地工作流：

- EPUB / PDF / MOBI / AZW3 → 双人中文播客脚本
- 生成分段音频，并合成为完整音频
- 生成 Smart Slide
- 合成最终 MP4 视频
- 压缩 MP4，方便后续分享或上传

## 目录内容

当前目录包含：

- `SKILL.md`：完整 skill 说明
- `scripts/epub2podcast_local_run.sh`：主运行脚本
- `scripts/epub2podcast_local_regenerate_slide.sh`：重生成某一页 slide
- `scripts/epub2podcast_local_compress_feishu_video.sh`：压缩最终视频

## 使用前提（Prerequisites）

是的，这个 skill **有前置条件**。

它不是“拿来就能直接跑”的独立软件包，而是一个建立在你本地 `epub2podcast` 项目之上的 skill 封装。

在使用前，至少需要准备好以下内容：

### 1. 本地 `epub2podcast` 项目代码

你需要已经拥有一个可运行的本地项目目录，例如：

```bash
/path/to/epub2podcast-local/frontend/server
```

然后设置环境变量：

```bash
export EPUB2PODCAST_PROJECT_ROOT=/path/to/your/epub2podcast-local/frontend/server
```

这个 skill 目录下的脚本，会通过这个环境变量找到真正的项目代码并执行。

### 2. Node.js 和 npm

这些脚本会调用项目里的 Node/TypeScript 构建与运行流程，因此本机需要：

- Node.js
- npm

### 3. ffmpeg / ffprobe

如果要生成和处理最终音频、视频，本机通常需要：

- `ffmpeg`
- `ffprobe`

### 4. Chrome / Chromium

如果要渲染 Smart Slide，通常需要本机安装：

- Chrome
- 或 Chromium

这是给 Puppeteer 截图和页面渲染使用的。

### 5. 必要的模型与服务环境变量

如果你的本地 `epub2podcast` 项目依赖模型服务或 TTS 服务，那么对应环境变量也需要提前配置好。

例如，常见会涉及：

- OpenRouter 相关配置
- Volcengine TTS 相关配置

具体变量名和取值方式，取决于你实际使用的 `epub2podcast` 项目实现。

## 为什么这些内容应该写进 README

**应该写，而且很有必要。**

因为对外部用户来说，README 最重要的几个问题就是：

- 这个东西是干什么的？
- 我能不能直接用？
- 使用前要先准备什么？
- 缺哪些依赖会跑不起来？

如果不把 prerequisites 写清楚，别人很容易误以为：

- 这是一个开箱即用的完整工具
- 只下载这个目录就能直接运行

但实际上，它更像是：

- 一个对现有本地项目的 skill 封装
- 一组帮助你运行该工作流的说明和脚本

所以 README 里应该明确告诉用户：

- 它依赖什么
- 谁适合用
- 怎么开始
- 哪些东西需要自己提前准备

## 最适合放在 README 里的内容

对于公开 README，建议至少写清楚这几类信息：

1. 这个 skill 是干什么的
2. 它依赖什么环境
3. 使用前要准备什么
4. 最基本的启动方式
5. 这个 skill 的边界是什么

## 最简单的开始方式

当你已经准备好本地项目和环境变量后，可以这样运行：

```bash
export EPUB2PODCAST_PROJECT_ROOT=/path/to/your/epub2podcast-local/frontend/server
bash scripts/epub2podcast_local_run.sh --epub ./book.epub
```

## 适用边界

这个目录只收录 **local-only** 路径：

- 本地生成中文双人播客脚本
- 本地生成音频
- 本地生成 Smart Slide
- 本地合成最终 MP4

它不覆盖远端服务调用逻辑，而是聚焦本地可控、可复用的工作流。
