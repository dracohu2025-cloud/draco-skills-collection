---
name: remotion
description: "统一入口的 Remotion skill：用于 React/TS 视频制作、关键帧验图、中文旁白、字幕、渲染与交付。遇到 Remotion 视频需求时优先加载它。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [remotion, video, react, animation, captions, tts, rendering]
    related_skills: [motion-canvas, manim-video, volcengine-tts-local, lark-drive-upload]
---

# Remotion

这是 **统一入口**。以后遇到 Remotion 相关任务，优先加载这个 skill，不要先在 `remotion-best-practices` 和 `remotion-video-local` 之间犹豫。

它把两层东西合到一起：

1. **领域规则**：Remotion 的通用最佳实践、专题规则、常见坑
2. **本机工作流**：在当前机器上从脚手架、关键帧验图、旁白、字幕、渲染，到飞书交付的整套流程

## 什么时候用

当任务是下面这些时，优先用 Remotion：

- React 组件驱动的视频
- 模板化视频 / 批量视频
- UI / 卡片 / 仪表盘 / 图表类视频
- 数据驱动的解释视频
- 已知要复用前端组件、样式系统、字体和布局能力

如果任务更像：

- 数学 / 公式 / 几何 / 对象变换讲解 → 先考虑 `manim-video`
- 场景式 TS 动画、时间轴编排、偏 motion graphics → 先考虑 `motion-canvas`

## 先选型，再开做

视频任务默认先问这三件事：

1. 这是 **讲对象怎么变**，还是 **讲页面这一帧长什么样**？
2. 这是 **一次性演示视频**，还是 **模板化 / 批量生产视频**？
3. 主工作流是 **React/TS**，还是别的动画语言？

如果答案偏向：
- React
- 模板
- 组件复用
- 数据驱动

那就选 Remotion。

## 当前机器上已验证的基础

- Node / npm 可用
- `npx create-video@latest` 可用
- `ffmpeg` 可用
- 本地火山 TTS 可接（见 `volcengine-tts-local`）
- 飞书上传链路可接（见 `lark-drive-upload`）

## 一句话工作流

> 先做静音版，把画面逻辑跑通；再接旁白和字幕；最后渲整片并交付。

## 快速开始

### 1. 新建项目

```bash
npx create-video@latest --yes --blank --no-tailwind my-video
cd my-video
npm install
```

### 2. 本地预览

```bash
npx remotion studio
```

### 3. 抽关键帧验图

```bash
mkdir -p renders/stills
npx remotion still src/index.ts CompositionId renders/stills/frame-030.png --frame=30
npx remotion still src/index.ts CompositionId renders/stills/frame-120.png --frame=120
```

### 4. 渲整片

```bash
npx remotion render src/index.ts CompositionId renders/final.mp4
```

## 核心经验

### 1. 脚手架优先非交互
不要赌交互流程。

```bash
npx create-video@latest --yes --blank --no-tailwind my-video
```

### 2. 先 still，后整片
先抽关键帧，不要一上来渲完整视频。

### 3. 小心 Sequence 偏移减两次
常见空白页 bug：
- 顶层 `<Sequence from={SECTION}>`
- 子场景里又写 `const local = frame - SECTION`

结果就是局部帧被多减一次，后面页面看起来像空的。

### 4. 中文旁白优先走本地 TTS
短解释视频首版，优先本地火山 TTS，别先搞复杂云服务。

### 5. 字幕首版优先手写 JSON
短视频别先走自动转写，手写字幕时间段更稳。

### 6. 长渲染走后台 + 轮询
不要前台闷等。

## 默认交付路径

### A. 静音画面版
- 先完成 composition 结构
- `npm run lint`
- 抽关键帧检查信息密度、遮挡、留白、逻辑顺序

### B. 再加旁白
- 写 `narration.txt`
- 生成 `public/narration.mp3`
- 接 `<Audio src={staticFile('narration.mp3')} />`
- 用实际音频时长反推 `durationInFrames`

### C. 再加字幕
- 手写 `Caption[]`
- 做 `CaptionBar`
- 抽 2~3 张带字幕 still 图
- 检查是否压住主要内容

### D. 最后整片渲染 + 交付
- 后台渲染 MP4
- 校验时长 / 文件大小 / 可播放性
- 上传飞书并给最终链接

## 参考文件

按需加载：

- `references/selection-guide.md`：什么时候选 Remotion，什么时候别选
- `references/local-workflow.md`：本机端到端流程
- `references/pitfalls.md`：高频坑位
- `references/rules-index.md`：专题规则入口
- `templates/caption-bar.tsx`：最小字幕条模板
- `scripts/setup.sh`：环境检查

## 旧 skill 关系

- `remotion-best-practices`：保留为历史知识来源
- `remotion-video-local`：保留为历史本机 SOP

但以后 **优先加载 `remotion`**。旧 skill 只作为参考，不再作为首选入口。