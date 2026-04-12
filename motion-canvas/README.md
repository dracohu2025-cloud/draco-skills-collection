# Motion Canvas 视频制作

适合 **TypeScript 场景动画、时间轴编排、讲解型 motion graphics、代码驱动演示** 的技能包。

它介于 Manim 和 Remotion 之间：

- 比 Manim 更贴近 TS / 前端工作流
- 比 Remotion 更强调场景、时间轴和动画编排

## 适合场景

- 技术解释视频
- 机制 walkthrough
- 时间轴式演示
- 动画 UI mockup
- 代码高亮讲解
- 需要一边写一边预览的 TS 动画项目

## 前置要求

- Node.js
- npm

## 快速开始

```bash
npx @motion-canvas/create@latest
cd <project>
npm install
npm start
```

## 它擅长什么

- 把一个复杂主题拆成多个场景
- 用 `yield*`、`all()`、`sequence()` 编排节奏
- 用 TypeScript 写代码驱动动画
- 在本地实时预览、快速调 timing

## 什么时候别优先选它

- **数学 / 公式 / 几何 / 强对象变换** → 看 [`../manim-video/`](../manim-video/)
- **React 组件视频 / 模板化批量生成** → 看 [`../remotion/`](../remotion/)

## 目录结构

```text
motion-canvas/
├── README.md
├── SKILL.md
├── references/
│   ├── core-concepts.md
│   ├── patterns.md
│   └── selection-guide.md
├── templates/
│   ├── project-starter.ts
│   └── scene-starter.tsx
└── scripts/
    └── setup.sh
```

## 建议阅读顺序

1. `SKILL.md`
2. `references/core-concepts.md`
3. `references/patterns.md`
4. `templates/scene-starter.tsx`

## 一句话总结

**如果你脑子里想的是“场景怎么排、时间轴怎么走、这一段怎么演”，Motion Canvas 往往很顺。**
