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

## 注意事项

- 生成草稿后，你可以手动修改 `data/{word}-draft.json` 中的文案再继续
- TTS 成本约 ¥0.3 / 千字，每次生成后会自动统计
- 视频渲染时间较长（一分钟视频约 10-15 分钟），建议后台执行
