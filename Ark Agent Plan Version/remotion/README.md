# Remotion 视频制作

适合 **React 组件视频、页面型视频、模板化视频、批量生产视频** 的技能包。

如果你要做的是：页面、卡片、仪表盘、图表、数据驱动内容、组件复用，那 Remotion 通常比对象动画框架更自然。

## 适合场景

- React 组件驱动视频
- UI / 页面 / 卡片 / 仪表盘演示
- 模板化解释视频
- 批量生成的视频内容工厂
- 需要复用现有前端组件与样式系统的项目

## 前置要求

- Node.js
- npm
- ffmpeg

## 快速开始

```bash
npx create-video@latest --yes --blank --no-tailwind my-video
cd my-video
npm install
npx remotion studio
```

## 推荐工作流

1. 先做静音版，把画面逻辑跑通
2. 抽关键帧 still 验图
3. 再接旁白和字幕
4. 最后渲整片

抽关键帧：

```bash
mkdir -p renders/stills
npx remotion still src/index.ts CompositionId renders/stills/frame-030.png --frame=30
npx remotion still src/index.ts CompositionId renders/stills/frame-120.png --frame=120
```

整片渲染：

```bash
npx remotion render src/index.ts CompositionId renders/final.mp4
```

## 什么时候别优先选它

- **数学 / 公式 / 对象变换讲解** → 看 [`../manim-video/`](../manim-video/)
- **偏 TS 的场景编排动画** → 看 [`../motion-canvas/`](../motion-canvas/)

## 目录结构

```text
remotion/
├── README.md
├── SKILL.md
├── references/
│   ├── selection-guide.md
│   ├── local-workflow.md
│   ├── pitfalls.md
│   └── rules-index.md
├── templates/
│   └── caption-bar.tsx
└── scripts/
    └── setup.sh
```

## 建议阅读顺序

1. `SKILL.md`
2. `references/selection-guide.md`
3. `references/local-workflow.md`
4. `references/pitfalls.md`
5. `templates/caption-bar.tsx`

## 一句话总结

**如果你想做的是“页面这一帧长什么样”，而且以后还想批量复用同一套结构，优先看 Remotion。**
