---
name: video-framework-selector
description: "视频生成前的统一选型入口：在 Manim / Motion Canvas / Remotion 之间做框架判断，给出理由、风险和下一步建议。遇到任何新视频任务时优先加载它。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [video, framework-selection, manim, motion-canvas, remotion, planning]
    related_skills: [manim-video, motion-canvas, remotion]
---

# Video Framework Selector

这是视频任务的 **前置 skill**。

以后只要用户说：
- 做个视频
- 做个动画
- 做个解释视频
- 用代码生成视频
- 哪个框架合适

就先加载这个 skill，再决定是否进入：
- `manim-video`
- `motion-canvas`
- `remotion`

## 目标

在真正开做之前，先回答三件事：

1. **该选哪个框架**
2. **为什么选它**
3. **选它会牺牲什么**

如果这个判断不先做，后面常见问题是：
- 用 React 硬讲几何变换，写着费劲
- 用 Manim 硬拼 UI 卡片，结果很别扭
- 用 Motion Canvas 做内容工厂，后面维护累

## 默认流程

### Step 1. 先识别视频类型
先判断用户要的更像哪一种：

#### A. 对象变换讲解
典型信号：
- 数学
- 公式
- 坐标系
- 几何
- 算法过程
- 机制解释
- “这个对象怎么从 A 变到 B”

默认候选：`manim-video`

#### B. 场景编排动画
典型信号：
- 讲解型动画
- 技术 demo
- 时间轴式分段表演
- 代码驱动 motion graphics
- TypeScript 场景动画
- 想一边写一边预览

默认候选：`motion-canvas`

#### C. 页面/组件视频
典型信号：
- React
- 卡片
- 页面
- 仪表盘
- 模板视频
- 批量生成
- 数据驱动 UI 视频
- “这一帧页面该长什么样”

默认候选：`remotion`

## Step 2. 问自己这 5 个问题

1. **主角是对象，还是页面？**
   - 对象 → Manim / Motion Canvas
   - 页面 → Remotion

2. **重点是讲清机制，还是做模板生产？**
   - 讲机制 → Manim / Motion Canvas
   - 模板生产 → Remotion

3. **作者脑子里先想的是变换、场景、还是组件？**
   - 变换 → Manim
   - 场景 → Motion Canvas
   - 组件 → Remotion

4. **团队语言是 Python，还是 TS/React？**
   - Python → Manim 更顺
   - TS/React → Motion Canvas / Remotion 更顺

5. **以后是不是要大量复用模板？**
   - 是 → Remotion 优势更大
   - 不是，重在单支视频表达 → Manim / Motion Canvas 更自然

## 快速决策

### 选 Manim，当：
- 你要讲对象怎么变
- 数学 / 公式 / 几何是核心
- 目标是“讲明白”
- 你愿意为表达力和清晰度接受更强的动画 DSL

### 选 Motion Canvas，当：
- 你要的是讲解动画，但更偏 TS 工作流
- 你想用场景和时间轴编排内容
- 你想保留代码驱动动画的味道，同时要更现代的预览体验

### 选 Remotion，当：
- 你做的是 React 组件视频
- 你要模板化、批量化、页面型视频
- 你需要复用前端组件、样式系统、字体、布局

## 输出格式

做完选型时，回答应尽量固定成这四段：

### 推荐框架
一句话给出主推荐。

### 选择理由
只给 2~4 条最关键理由，别堆术语。

### 放弃的代价
说明另外两种路线为什么这次不优先。

### 下一步
直接进入对应 skill：
- `manim-video`
- `motion-canvas`
- `remotion`

## 推荐回答模板

```md
## 推荐框架
这次建议用：**<framework>**

## 理由
- ...
- ...
- ...

## 这次不优先选另外两条的原因
- <framework B>：...
- <framework C>：...

## 下一步
进入 `<skill-name>`，先做：分镜 / 场景拆分 / 关键帧规划 / 静音版。
```

## 边界情况

### 1. 用户描述太短
比如只说“做个视频”。

先别瞎定。至少补齐：
- 是讲概念，还是做模板
- 偏数学对象，还是偏页面 UI
- 最终是单支视频，还是批量复用

### 2. 需求混合
如果同时包含：
- 数学讲解
- UI 模拟
- 模板批量生产

先抓**主任务**。不要贪三条路线全占。

### 3. 技术栈影响判断，但不该压过内容本质
比如用户会 React，不代表所有视频都该上 Remotion。
内容结构永远先于语言熟悉度。

## 一句话心法

> 先判断你在拍“对象”“场景”还是“页面”，再选 Manim、Motion Canvas、Remotion。