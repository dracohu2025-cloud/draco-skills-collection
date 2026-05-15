# Ark Agent Plan 专用 Skills 集合

## 概述

这是专为 **Ark Agent Plan** 定制的 Skills 集合，基于通用版本进行优化，充分利用 Ark Agent Plan 的原生能力，减少重复功能。

## 与通用版本的区别

| 通用版本 Skill | Ark Plan 处理方式 | 原因 |
|---|---|---|
| `video-framework-selector` | ❌ 已移除 | Agent 自带推理能力，不需要独立 skill |
| `article-to-wechat-cover` | ✅ 已重构 | 保留流程封装，生图引擎替换为原生 Seedream |
| `nano-banana-image` | ❌ 已移除 | 使用原生 Seedream 生图能力完全替代 |
| `jimeng-image` | ❌ 已排除 | 和 Seedream 功能重复 |
| 钉钉专用版本 | ❌ 已排除 | 不需要支持钉钉 |

## 已保留的 Skills（17 个）

### 📘 飞书生态工作流（7 个）

| Skill | 用途 |
|---|---|
| `ai-news-bitable-archive` | 飞书日报归档到多维表 |
| `article-to-wechat-cover` | 飞书文档 → 公众号封面图（Ark Plan 专用版，基于 Seedream） |
| `daily-ai-agent-aigc-top-news` | 每日 AI 早报 → 飞书文档 + 多维表归档 |
| `feishu-doc-to-wechat-draft` | 飞书文档 → 微信公众号草稿 |
| `feishu-lark-workflows` | 飞书文档/云盘/多维表通用操作封装 |
| `feishu-seedance-video-pipeline` | 飞书多维表驱动的 Seedance 视频产线管理 |
| `news-aggregator-skill` | 多源新闻抓取与候选池管理 |

### 🎬 视频/多媒体制作（8 个）

| Skill | 用途 |
|---|---|
| `epub2podcast` | EPUB → 双人中文播客视频（**火山引擎 TTS 专用版**，与 Seedream/Seedance 共享认证） |
| `hyperframes-explainer-video` | HyperFrames 讲解视频（HTML+GSAP+TTS） |
| `manim-video` | Manim 数学/算法动画视频 |
| `manim-video-with-tts` | Manim + 火山 TTS 中文旁白 |
| `motion-canvas` | TypeScript 场景动画 / Motion Graphics |
| `open-design-to-open-slide` | 49 套 Open Slide React 幻灯片模板 |
| `remotion` | React 页面型视频 / 批量视频 |
| `vocabulary-video-pipeline` | 英文单词教育视频流水线 |

### 🕷️ 内容抓取（2 个）

| Skill | 用途 |
|---|---|
| `wechat-article-browseruse` | BrowserUse 云浏览器抓取公众号 → 飞书 |
| `wechat-article-camofox` | Camofox 浏览器稳定抓取公众号 → 飞书 |

## Ark Agent Plan 原生能力替代说明

### ✅ 已完全覆盖的功能

| 原 Skill 功能 | Ark Plan 原生替代 |
|---|---|
| 公众号封面图生成（引擎部分） | `byted-seedream-image-generate` |
| 通用图片生成（单图/批量） | `byted-seedance-video-generate` + `byted-seedream-image-generate` |
| 视频框架选型决策 | Agent 内置推理能力 |

> **注意**：`article-to-wechat-cover` 保留了流程封装（文档读取、主题提取、尺寸规范、自动插入），只替换了生图引擎。

### ⚠️ Skill 独有价值（不可替代）

| Skill 类型 | 核心价值 |
|---|---|
| 飞书生态封装 | 飞书 API 封装、字段映射、流程编排、Cron 调度 |
| 视频工程化 | 最佳实践集合、模板、参考文档、一键流水线 |
| 特殊抓取 | 反爬适配、专用浏览器（Camofox/BrowserUse）、清洗规则 |

## 版本维护规则

1. **通用版本上游同步**：定期从通用版本同步 bugfix 和更新
2. **Ark Plan 定制优化**：仅在本目录下进行 Ark Plan 专属优化
3. **不修改通用版本**：通用版本保持原样，所有定制都在本目录下
4. **增量优化原则**：优先使用原生能力，只保留 skill 的独有价值部分

## 目录结构

```
Ark Agent Plan Version/
├── ai-news-bitable-archive/
├── daily-ai-agent-aigc-top-news/
├── epub2podcast/
├── feishu-doc-to-wechat-draft/
├── feishu-lark-workflows/
├── feishu-seedance-video-pipeline/
├── hyperframes-explainer-video/
├── manim-video/
├── manim-video-with-tts/
├── motion-canvas/
├── news-aggregator-skill/
├── open-design-to-open-slide/
├── remotion/
├── vocabulary-video-pipeline/
├── wechat-article-browseruse/
├── wechat-article-camofox/
└── README.md （本文件）
```

## 更新日志

### v1.1.0 (2026-05-15)
- 新增 `article-to-wechat-cover` Ark Plan 专用版
- 保留流程封装（文档读取、主题提取、尺寸规范、自动插入）
- 生图引擎替换为原生 Seedream
- 总 skills 数量：17 个

### v1.0.0 (2026-05-15)
- 初始版本，基于通用版本 2026-05-15 同步
- 移除 4 个重复功能的 skills
- 保留 16 个高价值 skills
- 增加本说明文档
