# HyperFrames 讲解视频工作流

用 HyperFrames 制作讲解/解释/产品介绍类视频的完整工作流。从脚本撰写、TTS 生成、分镜设计、HTML Composition 到最终渲染，覆盖全流程与常见坑点。

## 快速开始

```bash
# 1. 撰写解说脚本（script.txt）
# 2. 生成 TTS 音频
volc-tts --input script.txt --voice female --output ./narration.mp3

# 3. 分析音频时长与分段
ffprobe -v error -show_entries format=duration -of csv=p=0 narration.mp3

# 4. 初始化 HyperFrames 项目
npx hyperframes init <project-name> --non-interactive

# 5. 编写场景化 HTML（参考 SKILL.md 中的 7 场景分镜模板）

# 6. Lint 验证
npx hyperframes lint

# 7. 渲染（先 draft 验证）
npx hyperframes render --quality draft --output ./draft.mp4

# 8. 双轨交付：Web 直链 + 飞书云盘
```

## 核心架构

```
HyperFrames Registry（原子组件库）
    → LLM Scene Composer（组件编排 + 配置生成）
        → HTML Animation（runtime 按配置实例化渲染）
            → HyperFrames CLI（Headless Chrome 逐帧截图 + FFmpeg 编码）
                → 双轨交付（Web 直链 + 飞书云盘）
```

## 主要特性

- **音频驱动流水线**：TTS → 音频分析 → Timeline 生成 → 动画时序匹配
- **AI 媒体流水线**：Seedream 图片 / Seedance 视频 生成 → 本地缓存 → Composer 合成
- **Registry 组件库**：10+ 已验证动画组件，零成本到低成本集成
- **主题系统**：Dark / Cyber 等多主题支持
- **双轨交付**：飞书云盘备份 + Web 直链主入口

## 完整工作流

1. **撰写解说脚本** — 使用"小白翻译官"Persona，通俗易懂
2. **生成 TTS 音频** — 火山引擎 TTS
3. **测量音频时长与分段边界** — pydub / Whisper 分析
4. **生成 AI 媒体素材** — Seedream + Seedance
5. **初始化 HyperFrames 项目** — npx hyperframes init
6. **编写 Scene-based Composition** — HTML + GSAP + Canvas
7. **Lint 验证** — npx hyperframes lint
8. **渲染** — draft 验证 + final 输出
9. **双轨交付** — Web 直链 + 飞书云盘

## 常见坑点

- **先 TTS 后 HTML**：必须先确定音频时长再排 GSAP 时间轴
- **音画同步**：使用 Whisper 逐句转录获取精确时间戳
- **Headless 禁用 liveLoop**：通过 `navigator.webdriver` 检测禁用 RAF 预览循环
- **移除 setTimeout/CSS transition**：所有动画必须基于 `window.updateFrame(time)` 逐帧计算
- **视频时长 > 音频时长**：避免 AAC 帧对齐截断音频末尾
- **后台渲染**：长视频必须后台渲染，前台 60s 超时

## 完整文档

详细流程、代码示例、坑点解决方案请参阅 `SKILL.md`。

## 相关 Skill

- [hyperframes-workflow](../hyperframes-workflow/) — HyperFrames 统一入口
- [volcengine-tts-local](../volcengine-tts-local/) — 火山引擎 TTS 本地合成
- [gsap](../gsap/) — GSAP 动画参考
