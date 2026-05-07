# open-design-to-open-slide

![open-design-to-open-slide workflow preview](./assets/workflow-preview.svg)

把 **Open Design** 的视觉模板，转换成 **Open Slide** 可运行的 React 幻灯片模板。

一句话：**借 Open Design 的审美和页面范式，用 Open Slide 的 React runtime 重新实现。**

## 适合做什么

- 把 Open Design 里的设计系统改造成 Open Slide 模板
- 做 16:9 的演示模板套件
- 做 20 页一组的可复用 PPT/Slide album
- 给 Agent 生成内容时提供稳定版式
- 用截图和 contact sheet 做模板验收

## 不做什么

- 不引入 Open Design runtime
- 不复制 Open Design daemon / agent adapter / web app
- 不把单文件 HTML 直接塞进 Open Slide
- 不绑定某个私有部署环境

## 标准 20 页结构

| 页码 | 页面 |
|---|---|
| 01 | Cover |
| 02 | Agenda |
| 03 | Problem / Context |
| 04 | Framework |
| 05 | Content |
| 06 | Metrics / Data |
| 07 | Timeline / Roadmap |
| 08 | Diagram / Architecture |
| 09 | Closing / CTA |
| 10 | Section Divider |
| 11 | Quote / Key Insight |
| 12 | Comparison |
| 13 | Process / Workflow |
| 14 | Matrix / 2×2 |
| 15 | Table / Spec |
| 16 | Case Study |
| 17 | Checklist |
| 18 | Risks / Tradeoffs |
| 19 | FAQ / Appendix |
| 20 | Thank You / Contact |

## 核心原则

| 层 | 做法 |
|---|---|
| 视觉 | 从 Open Design 提取色彩、字体、卡片、图表节奏 |
| 结构 | 保留页面 archetype，不照搬 HTML |
| 实现 | 用 Open Slide `Page[]` + React primitives |
| 验收 | 构建、截图、hash、空白检测、contact sheet |

## 最容易踩的坑

### 1. 把 Open Design 当 runtime 引进来

别这么干。这样会变成两个系统糊在一起，后期维护很丑。

正确做法：只移植设计语言和页面结构。

### 2. 扩展 9 页到 20 页时白屏

常见原因是新增页面引用了旧文件里不存在的全局变量，比如：

```ts
const dark = isDarkBg(t.bg)
```

如果 `dark` 只在某个函数里定义，新增页面可能构建通过但运行白屏。坏得很隐蔽。

### 3. 只看构建成功

构建成功只说明 TypeScript/打包过了，不代表页面能看。

必须截图验收。

## 快速使用

看完整流程：[`SKILL.md`](./SKILL.md)

最小工作流：

```bash
# 1. 建一个 Open Slide deck 目录
mkdir -p slides/od-example-suite

# 2. 写 index.tsx，导出 20 个 Page
# export default [Cover, Agenda, ..., ThankYou]

# 3. 构建
pnpm build

# 4. 截图检查
chromium --headless=new --no-sandbox \
  --window-size=1920,1080 \
  --screenshot=/tmp/od-example.png \
  "http://127.0.0.1:5173/s/od-example-suite?p=1"
```

## 输出物

通常产出：

- `slides/od-xxx-suite/index.tsx`
- 20 页 Open Slide 模板
- 每页截图
- cover sheet
- full contact sheet

## 适合人群

- 想做 agent-native slide 模板的人
- 想把优秀 HTML 设计系统沉淀成 React slide primitives 的人
- 想批量生成演示页，但不想每次从空白页开始的人
