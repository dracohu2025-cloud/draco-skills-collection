---
name: vocabulary-video-pipeline
description: 基于 Remotion 的词汇视频自动化生成 skill。输入一个英文单词，自动跑完诊断、TTS 音频、节奏分割、视频渲染、飞书上传和成本汇报。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [video, remotion, vocabulary, tts, education, feishu]
---

# vocabulary-video-pipeline

基于 Remotion 的词汇视频自动化生成流水线。输入一个英文单词，自动生成带中文讲解、TTS 音频和动态视觉效果的教育视频。

## 使用场景

- 生成面向中小学生的英文单词解释视频
- 需要一键从单词到视频的自动化流程
- 需要 TTS 音频与视觉动画节奏完美同步

## 工作流

```
输入单词
    ↓
diagnose → 推荐模板 + 生成草稿 JSON
    ↓
generate_audio_beats → TTS + 静音检测 + 节奏数据
    ↓
Remotion render → MP4
    ↓
Feishu upload + 成本报告
```

## 快速使用

### 前提

1. 已克隆 [vocabulary-video-pipeline](https://github.com/dracohu2025-cloud/vocabulary-video-pipeline) 项目到本地
2. 已安装 Node.js、npm、Python 3
3. 已配置 `.env` 中的火山引擎 TTS 参数
4. 已安装 `lark-cli` 并登录（用于飞书上传）

### 配置环境变量

```bash
export VOCAB_VIDEO_PROJECT_ROOT=/path/to/vocabulary-video-pipeline
```

若不设置，脚本会自动搜索常见路径。

### 生成视频

```bash
python3 scripts/generate_word_video.py --word breakfast
```

### 只生成草稿

```bash
python3 scripts/generate_word_video.py --word breakfast --draft-only
```

### 只生成音频和节奏

```bash
python3 scripts/generate_word_video.py --word breakfast --audio-only
```

### 跳过某些步骤

```bash
python3 scripts/generate_word_video.py --word breakfast --skip-render --skip-upload
```

## 目录结构

```
vocabulary-video-pipeline/
  SKILL.md                          # 本文件
  README.md                         # 面向外部用户的说明
  scripts/
    generate_word_video.py          # 统一入口脚本
  assets/
    preview-*.jpg                   # 效果预览图
```

## 模板库

| 场景 | 类型 | 用途 |
|------|------|------|
| `hero-word` | 入题 | 展示单词、音标、标签 |
| `origin-chain` | 词源 | 展示词汇历史演变 |
| `meaning-compare` | 辨析 | 对比近义词 |
| `full-screen-mood` | 氛围 | 情绪化场景描述 |
| `quote-page` | 引用 | 英文名句 + 中文翻译 |
| `answer-cards` | 问答 | 三问答卡片 |
| `ending-summary` | 总结 | 公式 + 要点 + 结语 |

## 关键经验：草稿内容需要人工/LLM 填充

`npm run diagnose:word` 只会生成一个带有 `props` 和 `beats` 空壳的骨架 JSON。在执行 TTS 和渲染之前，必须填充以下内容：

1. **每个 scene 的 `props`**：标题、副标题、卡片文案、颜色等
2. **每个 scene 的 `beats`**：这是 TTS 的口播稿，必须是 **流畅的叙事讲解**，不是碎片化的要点列表

### 推荐实际步骤

```bash
# 1. 生成草稿骨架
python3 scripts/generate_word_video.py --word breakfast --draft-only

# 2. 手动或请 LLM 填充 data/breakfast-draft.json 中的 props 和 beats

# 3. 再继续执行完整流程
python3 scripts/generate_word_video.py --word breakfast
```

### TTS 口播稿风格要求

- 不要念 PPT：不能是“第一点…第二点…”的生硬拼揅
- 必须是连贯的、有起承转合的叙事性讲解
- 视觉元素只是配合音频节奏出现的辅助，而不是被念出来的标签

## 常见坑位（Pitfalls）

### 1. ending-summary 的 beats 必须与视觉 point 严格一一对应
`ending-summary` 页面通常会展示 3 个带颜色的要点卡片（如“希望之光 / 日常之美 / 相信的力量”）。**TTS 口播稿不能绕开这些标签去讲别的例子**（比如“雨后的彩虹 / 陌生人的善意 / 深夜的水饺”），否则观众会看到文字 A 却听到语音讲 B，产生强烈的错位感。

**正确做法**：
- beat 1：解释公式 / 核心词义
- beat 2~4：逐字对应三个 point（每个 point 一句话）
- beat 5：closing 收尾句

### 2. 结尾 closing 句容易被“截断”
如果 ending-summary 的最后一个 beat 结束得太靠近场景末尾，Remotion 的场景切换会在语音完全落定前就切走，导致收尾听起来像被掐掉。

**正确做法**：
- 确保 closing 句有足够长的 `endFrame`（通常让静默检测自然分配即可）
- 如果仍被截断，检查 `player.tsx` 中 `sceneDurations` 的尾帧 padding 是否充足

## 注意事项

- TTS 成本约 ¥0.3 / 千字，每次生成后会自动统计
- 视频渲染时间较长（一分钟视频约 10-15 分钟），建议后台执行
