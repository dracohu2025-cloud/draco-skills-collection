# 视频框架选型器

一个开工前先刹车的技能包。

它本身不负责渲视频；它负责先把方向选对：**这次该用 Manim、Motion Canvas，还是 Remotion。**

## 它解决什么问题

很多视频项目一开始就选错框架，后面越做越别扭：

- 用 Remotion 硬讲对象变换
- 用 Manim 硬拼页面卡片
- 用 Motion Canvas 硬扛模板化内容工厂

这个目录的作用很简单：**先判断你在拍“对象”“场景”还是“页面”，再决定后续工具。**

## 适合什么时候用

当你遇到这些需求时，先看这里：

- 做个视频
- 做个动画
- 做个解释视频
- 用代码生成视频
- 不确定该选哪个视频框架

## 核心输出

它默认产出 4 件事：

1. 推荐框架
2. 为什么选它
3. 另外两条这次为什么不优先
4. 下一步该进入哪个具体 skill

## 快速判断

- **对象变换 / 数学 / 几何 / 算法过程** → 优先看 [`../manim-video/`](../manim-video/)
- **场景编排 / TS 动画 / 时间轴驱动讲解** → 优先看 [`../motion-canvas/`](../motion-canvas/)
- **React 页面 / 组件视频 / 模板化批量生产** → 优先看 [`../remotion/`](../remotion/)

## 推荐阅读顺序

1. `references/decision-table.md`
2. `references/question-checklist.md`
3. `references/handoff-map.md`
4. 确认方向后，再进入对应框架目录

## 目录结构

```text
video-framework-selector/
├── README.md
├── SKILL.md
└── references/
    ├── decision-table.md
    ├── question-checklist.md
    └── handoff-map.md
```

## 一句话总结

**先选框架，再开做。这个目录不是加一道流程，而是少走很多弯路。**
