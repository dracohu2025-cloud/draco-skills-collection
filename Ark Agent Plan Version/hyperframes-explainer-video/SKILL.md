---
name: hyperframes-explainer-video
description: 用 HyperFrames 制作讲解/解释/产品介绍类视频的完整工作流。从脚本撰写、TTS 生成、分镜设计、HTML Composition 到最终渲染，覆盖全流程与常见坑点。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hyperframes, video, explainer, tutorial, tts, gsap]
    related_skills: [hyperframes-workflow, volcengine-tts-local, gsap]
---

# HyperFrames 讲解视频工作流

当用户想用 HyperFrames 做一支**讲解视频**或**概念解释视频**时（无论是解释技术、产品、论文还是代码仓库），使用本 skill 指导完整的制作流程。

---

## 触发信号

- “用 HyperFrames 做一个讲解视频”
- “解释 XXX 的视频”
- “给这个 repo/文章/概念做个介绍视频”
- “做一支带 TTS 的 HyperFrames 视频”

---

## 架构选型：Registry + Composer + Theme（推荐）

不要陷入"有限模板 vs LLM 自由生成"的二元对立。推荐**中庸方案**：

```
HyperFrames Registry（原子组件库）
  ├── 文字动效: typewriter, scramble-text, fade-up, slide-in, glow-pulse
  ├── 图形元素: particle-burst, circuit-lines, grid-bg, wave-form
  ├── 布局模板: split-screen, centered-hero, card-stack
  ├── 转场效果: crossfade, slide-wipe, glitch-cut
  └── 叠加层: scanlines, noise-grain, vhs-tracking
         ↓
LLM Scene Composer（组件编排 + 配置生成）
  输入: 脚本段落 + 时间预算 + theme 配置
  输出: JSON scene-config（选哪些组件、参数、时序）
         ↓
HTML Animation（runtime 按配置实例化渲染）
```

**为什么不用 LLM 直接生成 GSAP 代码？**
- 时序漂移：LLM 写的动画 3.2s，但 TTS 分配给这个场景只有 2.8s → 画面被截断或黑屏
- 性能抽奖：低效 Canvas 代码能让 HyperFrames 截图时间从 5 分钟变成 50 分钟
- 调试地狱：动画不工作时要读 LLM 写的 200 行 GSAP 代码找 bug

**LLM 只写 JSON，不写 JS。创造力在"编排"层面释放，执行代码由人工验证过的原子组件担保。**

### Registry 组件接口规范

```js
{
  id: "scanlines",
  category: "overlay",        // overlay | text | background | transition
  integrationCost: "zero",    // zero | low | medium | high
  requiresCanvas: false,
  requiresInteraction: false, // false = 时间驱动，无需鼠标/键盘
  themeParams: {
    cyber: { opacity: 0.08, color: "#00ff41", speed: 2 },
    dark:  { opacity: 0.03, color: "#ffffff", speed: 1 }
  },
  minDuration: 0,      // 0 = 全程存在
  maxDuration: Infinity,
  mount(container, params) { /* 创建 DOM / Canvas */ },
  unmount() { /* 清理 */ }
}
```

### HyperFrames 特效集成成本矩阵

| 成本 | 特效类型 | 代表 | HyperFrames 兼容 |
|------|---------|------|-----------------|
| **zero** | CSS 动画 | scanlines, text-glitch, glow-pulse | ✅ 逐帧截图完美支持 |
| **zero** | GSAP 时间线 | typewriter, fade-up, slide-in | ✅ `tl.progress()` 精确控制 |
| **low** | Canvas 2D 自循环 | matrix-rain, particle-burst, wave-form | ✅ `requestAnimationFrame` 正常 |
| **medium** | 交互转时间驱动 | mouse-trail, hover-glitch | ⚠️ 需预定义虚拟路径 / timeline 触发 |
| **high** | Three.js / WebGL | hologram, nebula | ❌ Headless Chrome GPU 不稳定，10x 慢 |

**原则：把时间当鼠标。视频里没有"用户"，只有时间轴。所有交互必须翻译成时间驱动。**

---

## 完整工作流（约 7 步）

### Step 1: 撰写解说脚本（Script Writer Persona）

**必须用"小白翻译官"Persona：**

```markdown
你是「小白翻译官」——专门把艰深技术内容翻译成"人话"的顶级科普写手。
读者是完全没有技术背景的普通人，口头禅是"说人话"。

核心原则：
1. 禁用生造术语：专业词汇必须在同一句话里用日常语言解释
2. 像朋友聊天：用"你"、"我们"，禁止论文腔
3. 每个概念必配比喻：抽象概念落地到厨房、交通、快递等熟悉事物
4. 先给直觉，再给细节：告诉读者"这玩意本质上在干什么"
5. 一句话原则：超过两句话没让小白点头，就重写

禁止清单：
- ❌ "众所周知"、"不难看出"、"显然"
- ❌ 缩写首次出现不展开（如"LLM"必须先讲"大语言模型"）
- ❌ 堆砌定义不解释为什么关心
- ❌ 一句话超过 30 个字
```

**脚本结构（每段对应一个视觉场景）：**

通用模板（适合产品/技术介绍）：
```
片头（0-5s）—— 品牌/主题引入
理念（5-15s）—— 核心价值主张（必配比喻）
展开（15-45s）—— 技术细节/功能展示（类比为主）
对比（45-60s）—— 与旧方案的差异（用生活场景对比）
愿景（60-75s）—— 应用场景（让读者能想象自己在用）
CTA（75-90s）—— 行动号召
```

**概念解释专用模板**（适合解释 AI/ML/CS 概念，如 Diffusion Model、Attention、Embedding 等）：
```
Hook（0-8s）—— 视觉震撼开场，用粒子/光束等强特效抓住注意力
问题（8-25s）—— "为什么这个技术这么火？它到底在做什么？"
核心概念（25-55s）—— 用日常比喻解释核心机制（如"撒盐"比喻扩散）
类比强化（55-90s）—— 第二个比喻加固直觉（如"雕塑家凿石"比喻去噪）
技术细节（90-120s）—— 展示架构图/流程图，满足好奇心的技术层
震撼收尾（120-150s）—— 高潮视觉：多种风格/应用场景的快速轮播 + 金句结语
```

**概念解释视频的关键设计原则：**
- 开场必须是视觉奇观，不是文字标题（粒子重组、光束聚焦、噪声消散等）
- 每个核心概念配一个独立比喻，比喻之间不重复
- 技术细节场景用 `arch-diagram` + `code-block` 组合，但不要超过 30 秒
- 收尾必须回到"人话"，用金句总结，不要罗列技术参数

存为 `script.txt`。

典型解说视频结构：
```
片头（0-5s）—— 品牌/主题引入
理念（5-15s）—— 核心价值主张
展开（15-45s）—— 技术细节/功能展示
对比（45-60s）—— 与竞品或旧方案的差异
愿景（60-75s）—— 应用场景/未来展望
CTA（75-90s）—— 行动号召
```

存为 `script.txt`。

### Step 2: 生成 TTS 音频

使用本机火山引擎 TTS（已配置 `VOLCENGINE_TTS_*` 环境变量）：

```bash
# 加载环境变量
set -a && . ~/.hermes/.env && set +a
volc-tts --input script.txt --voice female --output ./narration.mp3
```

验证返回 `code=3000`，确保音频正常生成。

### Step 3: 测量音频时长与分段边界

这是设计时间轴的**关键依据**。先获取总时长：

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 narration.mp3
```

**方案 A（推荐）：音频驱动自动化 Pipeline**

对于需要频繁调整 TTS 或脚本的项目，建立自动化 pipeline 避免每次手动重算时间：

**1. 创建 Timeline 生成脚本** (`scripts/generate_timeline.py`)

```python
# 核心逻辑：音频分析 + 字数权重分配 → 输出 timeline.json + timeline.js
# 支持两种模式：
#   --mode audio    : pydub 检测段落边界（适合段落停顿明显的音频）
#   --mode weighted : 按脚本各 scene 字数比例分配（推荐，更稳定）

# 示例：基于字数权重生成 timeline
python3 scripts/generate_timeline.py narration.mp3 \
  --mode weighted --weights 1,3,3.5,4,1.5,1.5,1 \
  --fade 0.5 --output timeline.json
# 同时生成 timeline.js（供浏览器同步加载，避免 fetch/CORS 问题）
```

**字数权重设计原则**：
- 先按脚本段落统计每个 scene 的中文字数
- 权重 = 相对字数比例（如 Hero 67字→权重1，Architecture 181字→权重4）
- 脚本自动按比例分配音频总时长到各 scene

**简化版本（无需外部脚本，直接用 Python inline）：**

```python
from pydub import AudioSegment
import json

audio = AudioSegment.from_mp3('narration.mp3')
total_duration_sec = len(audio) / 1000

# 每个 scene 的文本
scenes_text = ["...", "...", "..."]  # 按顺序
scene_chars = [len(s.replace(' ', '').replace('\n', '')) for s in scenes_text]
total_chars = sum(scene_chars)

timeline = {"total_duration_sec": round(total_duration_sec, 2), "fps": 30, "scenes": []}
cumulative = 0

for i, (text, chars) in enumerate(zip(scenes_text, scene_chars)):
    ratio = chars / total_chars
    duration = total_duration_sec * ratio
    start = cumulative
    end = cumulative + duration
    timeline["scenes"].append({
        "id": i + 1,
        "start_sec": round(start, 2),
        "end_sec": round(end, 2),
        "duration_sec": round(duration, 2),
        "start_frame": int(start * 30),
        "end_frame": int(end * 30),
        "duration_frames": int(duration * 30)
    })
    cumulative = end

with open('timeline.json', 'w') as f:
    json.dump(timeline, f, indent=2)
```

**2. 创建动画模板** (`animations.js`)

将硬编码的 GSAP 动画抽离为**相对时间偏移**的模板：

```javascript
const ANIMATION_TEMPLATES = {
  'scene-hero': {
    elements: [
      { id: 'hero-logo', type: 'fromTo',
        from: {scale:0.8, opacity:0, y:30},
        to: {scale:1, opacity:1, y:0, duration:1, ease:'power3.out'},
        offset: 0.2 },  // 相对于 scene.visualStart 的偏移
      // ...
    ]
  },
  // ... 其他 scene
};
```

**3. HTML 中动态组装 Timeline**

```html
<script src="timeline.js"></script>   <!-- AUDIO_TIMELINE 变量 -->
<script src="animations.js"></script> <!-- ANIMATION_TEMPLATES 变量 -->
<script>
function buildTimeline() {
  const timeline = AUDIO_TIMELINE;
  const tl = gsap.timeline({ paused: true });
  
  timeline.scenes.forEach(function(scene) {
    var template = ANIMATION_TEMPLATES[scene.id];
    // scene 出现
    tl.set('#' + scene.id, { visibility: 'visible', opacity: 1 }, scene.visualStart);
    // 元素动画（相对偏移 → 绝对时间）
    template.elements.forEach(function(el) {
      var absTime = scene.visualStart + el.offset;
      tl.fromTo('#' + el.id, el.from, el.to, absTime);
    });
    // scene 淡出
    tl.to('#' + scene.id, { opacity: 0, duration: timeline.fadeDuration, ease: 'power2.in' }, scene.fadeOutAt);
  });
  
  return tl;
}

window.__timelines = window.__timelines || {};
window.__timelines['composition-id'] = buildTimeline();
</script>
```

**为什么用 `timeline.js` 而不是 `fetch('timeline.json')`？**

HyperFrames 渲染器通过无头浏览器加载本地 HTML 文件，`fetch()` 在 `file://` 协议下常因 CORS 失败，且异步加载可能导致渲染器在 timeline 构建完成前就开始捕获帧。`timeline.js` 作为同步 `<script src>` 加载，确保 `AUDIO_TIMELINE` 在 `buildTimeline()` 执行时已可用。

**后续迭代只需一步**：

```bash
# 换了新 TTS 或改了脚本，重新生成 timeline 即可，无需改 HTML
python3 scripts/generate_timeline.py new-narration.mp3 \
  --mode weighted --weights 1,3,3.5,4,1.5,1.5,1 --fade 0.5 --output timeline.json
# timeline.js 会自动同步更新
```

---

**方案 B：手动 Whisper 转录（适合需要逐句精控的场景）**

不要凭字数估算段落时长——TTS 语速不均匀，中英文混合时尤其不准。正确做法是用 **Whisper 逐句转录**获取精确时间戳：

```bash
whisper narration.mp3 --model tiny --language zh --word_timestamps False --output_format json --output_dir .
```

然后提取每句的起止时间：

```python
import json
with open('narration.json') as f:
    data = json.load(f)
for seg in data['segments']:
    print(f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}")
```

根据转录结果，把脚本按语义分组，确定每个 Scene 的音频边界。

**但对于大多数项目，"比例法"已足够精确**——中文 TTS 语速相对稳定，按字数比例分配的误差通常 < 0.5 秒，对视频渲染无影响。Whisper 方案留给需要逐字精确对齐的场景。

### Step 4: 生成 AI 媒体素材（Seedream + Seedance）

**这是概念解释视频的"视觉冲击力"核心来源。**在编写 HTML 之前，先规划好 AI 生成的图片和视频素材，避免边做边发现缺素材。

**素材清单规划模板（每个 Scene 一行）：**

| Scene | 类型 | 数量 | 用途 | Prompt 要点 |
|-------|------|------|------|------------|
| Hook | Seedream | 1 | 开场主视觉 | 强调光影震慨、颜色鲜艳 |
| 问题 | Seedream | 2-3 | 工具/产品卡片 | 风格化、一致性 |
| 核心概念 | Seedream | 1-2 | 比喻对象图 | 清晰、高画质、自然光线 |
| 类比 | Seedream | 2 | 对比对象图 | 对比强烈、风格统一 |
| 技术 | 无 | 0 | 架构图用 Registry 组件 | 不需要 AI 图片 |
| 收尾 | Seedream | 4-6 | 风格轮播 | 多种美学、色彩丰富 |
| 背景 | Seedance | 2-3 | 全局/场景背景视频 | 循环、无界边、暗色调 |

**成本控制：**
- Seedream ~¥0.8/张（2k 分辨率，~16k tokens）
- Seedance ~¥2.3/5s（480p，~50k tokens）
- 6 scene 视频建议预算：10-15 张图 + 2-3 段视频 = **~¥15-25**

**批量生成策略：**

```bash
# ✅ 正确：后台并行生成多张图
for i in 1 2 3 4 5 6; do
  python3 scripts/run.py --mode single --prompt "$prompts[$i]" \
    --size 2k --output ./scene${i}.jpg > /tmp/jimeng_${i}.log 2>&1 &
done
wait

# ❌ 错误：使用批量模式传多个 prompt
# Seedream 的 batch 模式会将文件中的多行 prompt 合并为一张图，而不是每行一张
```

**关键坑：**
- `execute_code` 中的 `subprocess` 不会自动继承 shell 环境变量，需要在 terminal 中直接执行
- Seedream 批量模式将文本文件中的每行合并为单一 prompt，而非每行生成一张图
- 敏感词（如"大卫雕塑"等含有审查风险的词）可能导致生成失败，需要简化 prompt

### Step 5: 初始化 HyperFrames 项目

```bash
npx hyperframes init <project-name> --non-interactive
cp narration.mp3 <project-name>/
```

### Step 5: 编写 Scene-based Composition

使用 **7 场景分镜模板**（已验证可复用）：

| 场景 | 时长 | 视觉元素 | 动画效果 |
|------|------|----------|----------|
| **Hero** | 0-5s | 大 Logo + 副标题 | 文字缩放出现 + 发光线延伸 |
| **Philosophy** | 5-15s | 一句话理念 + 代码块 | 标题淡入、代码窗口弹出 |
| **Architecture** | 15-28s | 4 层卡片堆叠 | 逐层从下到上展开 |
| **Core Tech** | 28-45s | 左右双面板 | 左右分别滑入 |
| **Differentiation** | 45-57s | 特性徽章矩阵 | 徽章逐个弹出 |
| **Vision** | 57-70s | 内容类型图标 | 图标飞入汇聚 |
| **CTA** | 70-85s | 行动按钮 + 链接 | 链接弹出、保持可见到结束 |

**HTML 规范检查清单：**
- [ ] 根节点 `data-duration="总时长"`
- [ ] `<audio class="clip" data-start="0" data-duration="总时长" data-track-index="0">`
- [ ] GSAP timeline `paused: true`、注册到 `window.__timelines['composition-id']`
- [ ] 背景/装饰元素**不加** `autoAlpha: 0`（第 0 帧黑屏缺陷）
- [ ] 内容元素 `visibility:hidden; opacity:0` 用 GSAP 控制入场
- [ ] 确定性逻辑：无 `Date.now()`、`Math.random()`、网络请求

核心设计模式：

1. **深色科技风默认主题**
   - 背景：`#050508` 或更深
   - 强调色：`#00f0ff` (cyan) + `#ff2a6d` (pink) 双色调
   - 代码色：`#39ff14` (neon green)

2. **视觉冲击力必备叠加层（用户极度敏感的大面积空白）**
   当用户反馈"元素太小、只占画面 60%、大面积空着"时，立即应用以下叠加层和放大策略：
   
   **全局叠加层（必填）：**
   - **扫描线 overlay**：CSS repeating-linear-gradient，横向线条，通透度 0.04-0.08，增加 CRT 线性质感
   - **暗角 vignette**：旷光籽缩小（feathered vignette），边缘渐黑，中央重点突出
   - **中央光晕 bloom**：大径 600px 渐变，半透明 radial-gradient，色彩与当前 scene 主题色相匹配
   - **动态粒子垂直梯度**：顶部向下渐变渐暗（元素消失区域）

   **CSS 叠加层示例：**
   ```css
   .scanlines-overlay {
     position: fixed; inset: 0; pointer-events: none; z-index: 999;
     background: repeating-linear-gradient(
       to bottom,
       transparent 0px,
       transparent 2px,
       rgba(0,255,65,0.04) 2px,
       rgba(0,255,65,0.04) 3px
     );
   }
   .vignette-overlay {
     position: fixed; inset: 0; pointer-events: none; z-index: 998;
     background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.6) 100%);
   }
   .bloom-overlay {
     position: fixed; inset: 0; pointer-events: none; z-index: 997;
     background: radial-gradient(circle at 50% 50%, rgba(0,240,255,0.12) 0%, transparent 60%);
   }
   ```

   **元素尺寸放大策略（针对 1920×1080 canvas）：**
   - Hero 标题：140px → **200px**，配双层 drop-shadow glow
   - 段落文本：20px → **28px**，最多 3 行为一组，组间行高 1.8
   - 卡片/面板：420px → **600-700px**，左右子元素对比追加
   - Canvas 绘图：1400px → **1800px**，模型名称 72px → **160px**，架构框 200px → **260px**
   - 公式/代码式：40px → **56px**，网格底边距 40px → **80px**
   - 原则：**每个元素应该占据画面 75-85% 可见面积**，只留少量边距

3. **Scene 切换机制**
   每个场景是一个绝对定位的 `div`，通过 GSAP 控制 `opacity` 和 `visibility`：
   ```js
   // 场景 A 退出
   tl.to('#scene-a', { opacity: 0, duration: 0.5, ease: 'power2.in' }, 14.0);
   // 场景 B 进入（先设置 visible，再动画 opacity）
   tl.set('#scene-b', { visibility: 'visible', opacity: 1 }, 15.0);
   tl.fromTo('#scene-b-title', { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.8 }, 15.3);
   ```

3. **GSAP Timeline 必须 paused 并注册**
   ```js
   window.__timelines = window.__timelines || {};
   const tl = gsap.timeline({ paused: true });
   // ... 所有动由 ...
   window.__timelines['composition-id'] = tl;
   ```

4. **音频元素**
   ```html
   <audio id="narration" class="clip"
     data-start="0" data-duration="85" data-track-index="0" data-volume="1.0"
     src="narration.mp3"></audio>
   ```

5. **背景装饰**
   - 网格线、渐变光晕、扫描线等背景元素**不加** `class="clip"`
   - 这些元素默认就该可见，不用 `autoAlpha: 0` 做入场动画

6. **纯文字/图标 DOM 元素**
   - 不需要 `class="clip"`
   - 只有 `<video>` `<audio>` `<img>` `<iframe>` 等媒体元素才需要

7. **根节点必须带 `data-duration`**
   ```html
   <div id="stage" data-composition-id="xxx" data-start="0" data-duration="85" data-width="1920" data-height="1080">
   ```

### Step 6: Lint 验证

```bash
npx hyperframes lint
```

必须 **0 errors, 0 warnings** 才能渲染。常见警告：
- `root_composition_missing_data_duration` → 给根节点加 `data-duration`

### Puppeteer 渲染关键最佳实践（针对多场景 HTML + Canvas 动画）

当项目使用自定义 HTML 组合（非 HyperFrames CLI 模板）时，Puppeteer 渲染需要额外注意以下几点：

**1. 图片预加载等待**

在 `page.goto()` 之后、开始截图之前，必须等待所有 `<img>` 元素完成加载。否则 Puppeteer 截图时图片可能尚未渲染或显示为破图/空白。

```javascript
await page.evaluate(() => {
  return Promise.all(
    Array.from(document.querySelectorAll('img')).map(img => {
      if (img.complete) return Promise.resolve();
      return new Promise((resolve) => {
        img.addEventListener('load', resolve, { once: true });
        img.addEventListener('error', resolve, { once: true });
        setTimeout(resolve, 3000); // 超时兜底
      });
    })
  );
});
```

**2. 场景预热（Scene Pre-warming）**

在正式渲染开始前，切换每个场景一次并触发其初始化逻辑（Canvas 初始化、字体加载、图片缓存等）。这能避免第一次截图时因资源未准备导致的空白/异常帧。

```javascript
for (let s = 0; s < sceneIds.length; s++) {
  await page.evaluate((idx) => {
    document.querySelectorAll('.scene').forEach(el => el.classList.remove('active'));
    document.getElementById(sceneIds[idx]).classList.add('active');
    // 触发场景特有的 Canvas 初始化
    if (window.drawNoiseCanvas) window.drawNoiseCanvas(0.5);
    if (window.ps1) { window.ps1.init(); window.ps1.render(); }
  }, s);
  await sleep(100);
  await page.screenshot({ path: '/dev/null', type: 'jpeg', quality: 1 }); // 空截图触发渲染
  await sleep(50);
}
```

**3. 每帧手动驱动场景特效**

Headless Chrome 中 CSS transition 和 GSAP timeline 不会自动播放。所有动画效果（图片模糊、粒子位移、噪声强度等）必须在渲染循环的 `page.evaluate()` 中手动计算并应用。

```javascript
// 示例：Scene 3 的图片模糊 + 噪声 Canvas 驱动
const progress = Math.min((time - sceneStart) / (sceneEnd - sceneStart), 1);
const img = document.getElementById('diffusion-img');
if (img) img.style.filter = `blur(${progress * 15}px) brightness(${1 - progress * 0.5})`;
if (window.drawNoiseCanvas) window.drawNoiseCanvas(progress);
```

**4. 单次 evaluate 更新所有状态**

每帧只发一次 `page.evaluate()`，在其内部完成场景切换、音频同步、Canvas 更新、CSS 变化等所有操作。多次 evaluate 会显著降低渲染速度。

**5. 用代码特效替代视频背景**

Seedance 等 AI 视频生成成本高、分辨率可能不足、循环不自然。当背景只需要动态视觉元素时，用 Canvas 2D 粒子系统替代：
- 成本：几乎为零（CPU 渲染）
- 质量：可无限循环、无边界缝隙
- 控制：粒子数量、颜色、运动轨迹全可调
- 适合：暗色背景上的漂浮粒子、光影效果等

```javascript
// 与视频背景的 HTML 对比
// 视频背景：<video class="bg-video" loop muted><source src="bg.mp4"></video>
// 代码特效：<canvas class="particle-canvas" id="canvas6"></canvas>
```

**6. 粒子特效多样性设计 —— 避免视觉疲劳**

当同一类 Canvas 特效（如粒子系统）需要在多个 Scene 中重复出现时，**仅调整颜色、数量或大小是不够的**。用户会在第 2-3 次看到时产生"又是这个"的疲劳感。

**正确做法：为每个场景设计物理行为完全不同的粒子系统。**以下是已验证的三种设计模式：

| 模式 | 物理行为 | 视觉感受 | 适用场景 |
|------|---------|---------|---------|
| **Spiral** 螺旋向心 | 粒子从屏幕边缘随机位置出发，受向心力和扰动力驱动向中心螺旋目标位置聚集 | 从混沌分散到有序聚集 | Hook/开场："从虚无中凝结" |
| **Bloom** 绽放生长 | 粒子从中心小范围内聚集，获得向外的初速度（像爆炸/烟花），然后被吸引回目标位置，摩擦力逐渐减速 | 像墨水滴入水中扩散后凝结 | 核心概念："从噪声中雕塑而出" |
| **Orbit** 轨道环绕 | 粒子在椭圆轨道上运动，各有不同的轨道半径、角速度、轨道倾角和 z 轴正弦波动，带发光拖尾 | 像星环/电子云一样优雅环绕 | 终章："成品展示" |

**设计原则：**
- 不同场景的粒子系统必须是**独立的 class**，而不是通过参数分支
- 物理模型差异要足够大：向心 vs 离心 vs 圆周运动，用户能一眼看出区别
- 颜色搭配也应该区分：每个场景使用不同的主色调，增强"这是另一个场景"的知觉
- 粒子数量可以根据场景重要性调整：开场 1500 粒、核心 1500 粒、终章 800 粒（更精致、不抢内容风头）

### 非 HyperFrames CLI 渲染（Puppeteer 手动渲染）

当项目不使用 `npx hyperframes render` CLI 时，可以用 Puppeteer 手动逐帧截图 + FFmpeg 合成。适用于：
- 需要更精细的渲染控制（如每帧更新 Canvas 状态）
- HyperFrames CLI 未安装或不适用的场景
- 需要混合多种渲染技术的复杂项目

**Puppeteer 渲染脚本核心逻辑：**

```javascript
const puppeteer = require('puppeteer');

async function render() {
  const browser = await puppeteer.launch({
    headless: 'new',
    // Linux headless 环境下需要标准安全参数（参见 Puppeteer 文档中的 headless 运行配置）
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto('file:///path/to/scenes.html', { waitUntil: 'networkidle2' });
  
  // 模拟点击启动播放（浏览器自动播放策略可能阻止音频）
  await page.click('body');
  await page.evaluate(() => new Promise(r => setTimeout(r, 500)));
  
  const TOTAL_FRAMES = Math.ceil(81.41 * 30); // duration * fps
  for (let frame = 0; frame < TOTAL_FRAMES; frame++) {
    const currentTime = frame / 30;
    
    // 更新页面状态
    await page.evaluate((time) => {
      document.getElementById('narration').currentTime = time;
      updateScene(time);
    }, currentTime);
    
    // 等待渲染安定
    await page.evaluate(() => new Promise(r => setTimeout(r, 30)));
    await page.screenshot({ path: `frames/frame_${String(frame).padStart(5, '0')}.png` });
  }
  
  await browser.close();
  
  // FFmpeg 合成：将帧序列与音频混合为最终视频
  // 命令示例：ffmpeg -y -framerate 30 -i frames/frame_%05d.png -i audio.mp3 
  //   -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow 
  //   -c:a aac -b:a 192k -shortest output.mp4
}
```

**性能警示：场景间渲染速度差异极大**

| 场景类型 | 特征 | 渲染速度 | 示例 |
|---------|------|---------|------|
| 静态内容 | 无动画、无 Canvas | ~500 帧/分钟 | 文字卡片、架构图 |
| CSS 动画 | GSAP/transition | ~300 帧/分钟 | 文字飞入、淡出 |
| Canvas 2D 自循 | 粒子、波形 | ~150 帧/分钟 | matrix-rain、particle-burst |
| Canvas 粒子重组 | 每帧更新位置 + 重绘 | ~35 帧/分钟 | 粒子从混沌到有序的组装 |
| WebGL / Three.js | GPU 加速 | 不推荐 | 在 headless Chrome 中不稳定，可能 10x 慢 |

**关键经验：**
- 粒子重组类场景（每帧更新上千个粒子位置并重绘）会将渲染速度降低 10-15 倍
- 如果总帧数较大，建议分批渲染：静态场景快速过，粒子场景留足时间
- Puppeteer 24.x+ 中 `page.waitForTimeout()` 已移除，必须用 `page.evaluate(() => new Promise(r => setTimeout(r, ms)))`
- 音频文件路径必须严格匹配，渲染脚本中的路径与实际文件位置不一致会导致 FFmpeg 编码失败

---

### Step 7: 渲染（HyperFrames CLI 方式）

**draft 先验证**：
```bash
npx hyperframes render --quality draft --output ./draft.mp4
```

**关于 draft vs final 的经验：**
- MVP/demo 视频的 draft 质量已足够。85s 720p draft 产出约 4.5MB/442kbps，画质清晰、音画同步。
- 不必执迷 "先 draft 再 final"的两步流程。lint + validate + ffprobe 通过即可当 final 交付。

**长视频必须后台渲染**：
- 85s 视频（2550 帧 @ 30fps）3 workers 下需 3-4 分钟，前台 `terminal()` 默认 60s 超时必导致进程被杀。
- 正确做法：用 `terminal(background=true, timeout=300)` 启动渲染，然后用 `process(action="wait", timeout=60)` 轮询进度，主动汇报百分比（0% → 30% → 60% → 90% → 100%）。
- 用户对"可见的进度更新"反馈很好，不要沉默等待。

**渲染完成后验证：**
```bash
ffprobe -v error -show_entries format=duration -of json ./draft.mp4
# 确认：时长 ≈ 预期值，视频流 h264，音频流 aac
```

### Step 8: 双轨交付（已验证必须）

**必须同时做两件事**：

1. **上传飞书云盘**（备份）：
```bash
cd <project-dir>
lark-cli drive +upload --file ./draft.mp4 --name "video.mp4"
# 返回 file_token，但链接可能因权限无法直接打开
```

   **获取正确的飞书云盘文件链接**：
   - 错误格式：`https://www.feishu.cn/drive/file/{token}` → 会跳转登录页
   - **正确格式**：用 `drive.files.list` API 获取文件元数据中的 `url` 字段：
     ```bash
     lark-cli api GET /open-apis/drive/v1/files --params '{"folder_token":"<root_folder_token>"}'
     # 返回中找到文件，url 字段为：https://{tenant}.feishu.cn/file/{file_token}
     ```
   - 示例：`https://g1mu6da08l.feishu.cn/file/YdslbgYqGogZrGxicAZcxo0Nnns`
   - 注意路径是 `/file/` 而非 `/drive/file/`

2. **部署 Web 直链**（主入口，必须能直接点击播放）：
```bash
sudo cp ./draft.mp4 /var/www/hermes.aigc.green/media/video.mp4
# 链接: https://hermes.aigc.green/media/video.mp4
```

**禁止只给本地路径、禁止只给飞书链接。必须给出可直接访问的 Web 直链。**

飞书链接打不开的原因：`drive/v1/metas/batch_query` 返回的 `url` 字段为空字符串，无法通过 API 生成公开可访问链接。用户无法直接打开。

---

## 已验证的坑

| 问题 | 现象 | 解决 |
|------|------|------|
| 先写 HTML 再生成 TTS | 视频结束了音频还在播 | **先 TTS → 测时长 → 再写 HTML** |
| 凭字数估算段落时长 | 后面几页音画不同步 | **Whisper 逐句转录获取精确时间戳** |
| **volc-tts-batch --concat 拼接** | 段间插入 0.3-0.8s 间隙，7 段累积偏移数秒，最后两段音频几乎丢失 | **用 ffmpeg concat demuxer 拼接：`ffmpeg -f concat -safe 0 -i files.txt -c copy out.mp3`** |
| **Headless 环境下 RAF 与 render.js 冲突** | HTML 中的 `requestAnimationFrame` 循环（live preview/auto-play）与 Puppeteer 逐帧 `updateFrame(time)` 争夺 DOM 状态，导致画面错乱/闪烁 | **通过 `navigator.webdriver` 检测禁用 liveLoop：`const isHeadless = navigator.webdriver || /Headless/.test(navigator.userAgent); if (!isHeadless) { liveLoop(); }`** |
| **使用 setTimeout / CSS transition 驱动动画** | Headless 渲染中 timing 不确定，动画状态与 `updateFrame(time)` 不同步 | **所有动画必须基于 `window.updateFrame(time)` 的 `time` 参数逐帧计算，彻底移除 setTimeout 和 CSS transition** |
| 用文件时长累加作边界（即使总时长正确） | 每段 TTS 首尾有约 0.2-0.8s 静音，按单段文件时长累加会导致画面比旁白提前/滞后出现 | **用 Whisper 分析拼接后的完整音频，以实际语音起止作为 scene 边界；或用 pydub `detect_nonsilent` 检测非静音段落二次验证** |
| **AAC 帧对齐截断音频末端** | ffmpeg `-shortest` 混音时，AAC 编码器按 1024-sample 帧对齐，最后 0.02~0.04s 音频被硬切，导致最后一句话尾音丢失 | **混音前用 `ffmpeg -af "apad=pad_dur=1"` 给音频加 1s 静音 padding；同时确保视频时长 > 音频原始时长，`-shortest` 以视频为准截断 padding 而非语音** |
| **视频比音频短导致音频被截断** | 渲染 85s 视频但音频 85.3s，`-shortest` 以视频为准截断音频 | **渲染时多加 1~2 秒余量（如音频 85s 则渲染 87s），确保视频始终长于音频原始时长** |
| 缺少诊断渲染 | 直接渲染完整视觉效果后发现不对齐，浪费大量时间 | **先做诊断版：纯色背景+硬切+时间戳，确认对齐后再加视觉效果** |
| 修改时序后忘改 data-duration | lint 报错 / 音频被截断 | **同步更新 stage 和 audio 的 `data-duration`** |
| 前台直接 render | 60s 超时，进程被杀 | **后台模式 + 轮询进度** |
| 飞书链接格式错误 | 打不开/跳转登录 | 用 `drive.files.list` 获取正确的 `https://{tenant}.feishu.cn/file/{token}` 格式 |
| lark-cli 发送文件消息失败 | 缺少 scope `im:message.send_as_user` | 执行 `lark-cli auth login --scope "im:message.send_as_user im:message"` 重新授权 |
| lark-cli 上传绝对路径 | `unsafe file path` 报错 | **cd 到目录后用 `./filename`** |
| Puppeteer 24.x `waitForTimeout` 移除 | `TypeError: page.waitForTimeout is not a function` | **用 `page.evaluate(() => new Promise(r => setTimeout(r, ms)))` 替代** |
| 音频路径不一致 | FFmpeg 编码失败：`No such file or directory` | **渲染脚本中引用的音频路径必须与文件实际位置严格一致** |
| 飞书 tenant domain 未知 | 无法构造正确的飞书云盘链接 | **浏览器访问 `https://www.feishu.cn/file/{token}`，从重定向 URL 提取 tenant（如 `g1mu6da08l.feishu.cn`）** |
| 缺少 `data-duration` | lint 警告 / 无限时长 | **根节点加 `data-duration`，且必须与 audio 的 `data-duration` 一致** |
| 第 0 帧全黑 | 所有元素被 `autoAlpha: 0` | **背景层不加 `autoAlpha: 0`** |
| draft 质量不够的担心 | 过于执迷 final render | **MVP/demo 中 draft 已足够。lint + validate + ffprobe 通过即可交付** |
| 音频分析不能完全依赖 pydub | pydub 检测的段落边界与脚本 scene 结构不对齐（TTS 句内暇息被误判为段落分隔） | **采用 "音频分析 + 字数权重" 混合策略，或直接用字数比例分配** |
| `fetch('timeline.json')` 失败 | Headless 浏览器中 CORS 拒绝或异步时序问题 | **用 `<script src="timeline.js">` 同步加载，将 JSON 数据内联为 JS 变量** |
| Chrome `Target closed` 崩溃 | 渲染过程中突然终止，错误信息模糊 | **检查 Swap 使用率（`free -h`），杀掉残留的 chrome-headless 进程，清理后重试** |
| **TTS 读错数字** | "2017年"被 TTS 读成类似"2011" | **数字写为汉字："二零一七" 或 "公元二零一七 年"，可用空格分开调整语速；也可写为"公元 二零一七 年"让 TTS 逐字清晰读出；Unicode "〇"（U+3007）效果不稳定，建议用普通汉字"零"** |
| **图片在截图时未加载** | Scene 中的 `<img>` 显示为破图/空白/模糊 | **在 `page.goto()` 后等待所有 img complete，用 Promise.all 包裹 load/error 事件 + 3s 超时拦底** |
| **同一粒子特效重复使用** | 3 个场景都用同一种螺旋粒子，用户反馈"短短几分钟内就不惊艳了" | **必须为每个场景设计物理行为完全不同的粒子系统（见下方"粒子特效多样性设计"）** |
| **视频背景成本高/质量差** | Seedance 背景视频短、分辨率低、循环不自然 | **用 Canvas 2D 粒子系统替代视频背景，成本近乎为零、可无限循环、参数全可控** |
| **TTS 音频与新脚本不匹配** | 修改脚本后（如去掉模型名称），旧音频仍然读出旧内容 | **脚本变更后必须重新生成 TTS，旧音频不能重复使用** |
| **Feishu API 无法获取文件分享链接** | 所有分享端点返回 404，`metas/batch_query` 返回的 url 为空 | **通过浏览器访问 `https://www.feishu.cn/file/{token}` 提取 tenant domain，或使用 Web 直链作为主要交付方式** |

### 音频-视频精确同步（关键 Pipeline）

当用户反馈"TTS 和视频节奏不匹配"或"最后一句话被截断"时，按以下步骤系统修复：

**1. TTS 生成与拼接**
- ❌ `volc-tts-batch --concat`：段间插入 0.3-0.8s 间隙，7 段累积偏移可达数秒
- ✅ **ffmpeg concat demuxer**：
  ```bash
  cat > list.txt << 'EOF'
  file '001.mp3'
  file '002.mp3'
  ...
  EOF
  ffmpeg -f concat -safe 0 -i list.txt -c copy perfect-concat.mp3
  ```

**2. 精确边界检测（必须用 Whisper，不能凭文件时长）**
```python
import whisper
model = whisper.load_model("base")
result = model.transcribe("perfect-concat.mp3", language="zh")
for seg in result["segments"]:
    print(f"[{seg['start']:.3f}s - {seg['end']:.3f}s] {seg['text']}")
```
- 按语义将句子分组到 scenes
- **Scene 边界 = 实际语音起止，不是文件边界**
- 用 pydub `detect_nonsilent` 二次验证：
  ```python
  from pydub.silence import detect_nonsilent
  segments = detect_nonsilent(audio, min_silence_len=300, silence_thresh=-45)
  ```

**3. 诊断先行策略**
在恢复复杂视觉效果前，先创建**诊断版本**：
- 纯色背景（不同 scene 用不同颜色）
- 硬切（无淡入淡出）
- 左上角显示时间戳 + Scene 编号
- 让用户确认画面切换与旁白是否同步
- **确认对齐后再加完整视觉效果**，避免视觉复杂度干扰判断

**4. 防止 AAC 截断音频末端**
```bash
# 混音前给音频加 1s 静音 padding
ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -af "apad=pad_dur=1" -c:a aac -b:a 192k -shortest output.mp4
```
- `apad` 给音频末尾加 padding，确保 AAC 帧对齐不会截断最后音节
- 同时**渲染视频时长 > 音频原始时长**（如音频 85s → 渲染 87s），`-shortest` 以视频为准截断 padding 而非语音

**5. 渲染时长必须大于音频原始时长**
- 为什么：即使音频拼接完整无间隙，AAC 编码器在末尾仍可能截断 0.02~0.05s
- 解决：渲染多渲染 1~2 秒余量，让 `-shortest` 截断的是 padding 而非最后一句话
- 验证：混音后用 `ffprobe -show_entries format=duration` 确认视频时长 ≈ 音频时长（差异 < 0.1s为合格），最后一句语音频完整保留

**5. Headless 环境禁用 liveLoop**
```javascript
const isHeadless = navigator.webdriver || /Headless/.test(navigator.userAgent);
if (!isHeadless) { liveLoop(); }  // 只在真实浏览器中启动 RAF 预览循环
```
- Puppeteer 逐帧 `updateFrame(time)` 与 HTML 中的 `requestAnimationFrame` 循环会争夺 DOM 状态
- 必须通过 `navigator.webdriver` 检测，在 headless 环境中阻止 RAF 自动启动

**6. 彻底移除 setTimeout / CSS transition**
```javascript
// ❌ 错误：setTimeout 驱动
setTimeout(() => { el.style.opacity = 1; }, 1000);

// ✅ 正确：基于 updateFrame(time) 的 time 参数逐帧计算
const progress = Math.min(1, Math.max(0, (sceneT - 1.0) / 0.8));
el.style.opacity = String(easeOut(progress));
```
- Headless 渲染中 timing 不确定，setTimeout/CSS transition 与 `updateFrame(time)` 不同步
- 所有动画状态必须从 `window.updateFrame(time)` 的 `time` 参数推导

### 音画不同步的诊断与修复

当用户反馈"页面切换了但音频还在讲上一页"时：

1. **用 Whisper 转录音频获取精确时间戳**（不要用 pydub silence detection，因为句内暇歇和段落暇歇容易混淆）
2. **对照脚本分组**，确定每个 Scene 对应的音频起止
3. **调整 GSAP timeline**：让淡出发生在音频结束后 0.3-0.5s，下一个 Scene 出现在音频结束后 0.5-0.8s
4. **同步更新** `stage` 和 `audio` 元素的 `data-duration`
5. **重新 lint 和渲染**

---

## 常见视觉元素快速复用（Registry 组件）

不再硬编码 HTML/CSS，从 Registry 导入组件：

```js
import { registry, mountScene, getThemeParams } from './registry-components/index.js';

// 根据 Theme 获取参数
const theme = 'cyber';
const sceneConfig = {
  components: [
    { id: 'scanlines', params: getThemeParams('scanlines', theme) },
    { id: 'matrix-rain', params: { ...getThemeParams('matrix-rain', theme), opacity: 0.3 } },
    { id: 'text-glitch', params: { selector: '.hero-title', ...getThemeParams('text-glitch', theme) } },
    { id: 'glow-pulse', params: { selector: '.hero-subtitle', ...getThemeParams('glow-pulse', theme) } }
  ]
};

// 挂载整个场景
const mounted = mountScene(document.body, sceneConfig, theme);

// 视频结束后清理
// unmountAll(mounted);
```

### 已验证的 Registry 组件

| 组件 | 类别 | 效果 | 集成成本 |
|------|------|------|---------|
| `scanlines` | overlay | CRT 扫描线叠加 | zero |
| `noise-grain` | overlay | 动态噪点粒度 | zero |
| `text-glitch` | text | RGB 色差偏移 + 抖动 | zero |
| `glow-pulse` | text | 霓虹呼吸 text-shadow | zero |
| `typewriter` | text | 逐字出现 + 光标闪烁 | zero |
| `matrix-rain` | background | Canvas 2D 字符瀑布 | low |
| `particle-burst` | background | 粒子爆发 + 拖尾 | low |
| `circuit-lines` | background | 自动生长的电路连线 | low |
| `wave-form` | background | 音频频谱柱状图 | low |
| `crossfade` | transition | 交叉淡入淡出 | zero |
| `slide-wipe` | transition | 横向滑入滑出 | zero |
| `glitch-cut` | transition | 故障切换 + 色彩偏移 | low |

### 传统原生元素（仍可用，但建议封装为组件）

```html
<!-- 代码窗口 -->
<div class="code-window">
  <div><span class="tag">&lt;div</span> <span class="attr">data-start</span>=<span class="code-text">"0"</span><span class="tag">&gt;</span></div>
</div>

<!-- 层叠卡片 -->
<div class="arch-card">
  <h3>标题</h3>
  <p>描述</p>
</div>

<!-- 特性徽章 -->
<div class="badge">GSAP</div>

<!-- 分隔发光线 -->
<div class="glow-line"></div>
```

---

## 一句话原则

> 先跑 TTS 确定时长，再排 GSAP 时间轴；后台渲染不沉默，交付必给 Web 直链。
