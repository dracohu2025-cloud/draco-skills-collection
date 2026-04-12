# Manim 视频制作

适合把**数学、公式、几何、算法过程、对象变换**讲清楚的技能包。

如果你要做的是“这个对象怎么从 A 变到 B”“这个公式为什么成立”“这个算法每一步发生了什么”，Manim 通常比 UI 型视频框架更顺手。

## 适合场景

- 数学概念解释
- 公式推导
- 几何关系演示
- 算法执行过程可视化
- 技术机制拆解
- 架构或流程逐步搭建动画

## 典型输出

- `plan.md`：叙事和分镜
- `script.py`：Manim 场景代码
- `final.mp4`：最终视频

## 前置要求

- Python 3.10+
- Manim Community Edition
- LaTeX
- ffmpeg

先跑环境检查：

```bash
bash ./scripts/setup.sh
```

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install manim

# 草稿质量快速试跑
manim -ql script.py Scene1

# 多场景拼接
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final.mp4
```

## 什么时候别优先选它

这些情况通常更适合别的框架：

- **React 页面 / 卡片 / 仪表盘视频** → 看 [`../remotion/`](../remotion/)
- **偏 TS 的场景编排动画** → 看 [`../motion-canvas/`](../motion-canvas/)

## 目录结构

```text
manim-video/
├── README.md
├── SKILL.md
├── references/
│   ├── animations.md
│   ├── equations.md
│   ├── scene-planning.md
│   └── ...
└── scripts/
    └── setup.sh
```

## 建议阅读顺序

1. `SKILL.md`
2. `references/scene-planning.md`
3. `references/visual-design.md`
4. `references/rendering.md`
5. `scripts/setup.sh`

## 一句话总结

**Manim 最强的地方，是把“对象如何变化”讲得清楚、干净、像一支真正的解释视频。**
