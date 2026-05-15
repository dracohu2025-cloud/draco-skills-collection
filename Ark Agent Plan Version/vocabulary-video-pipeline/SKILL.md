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
diagnose → 推荐模板 + 生成草稿 JSON（强制包含 origin-chain）
    ↓
generate_audio_beats → TTS + 静音检测 + 节奏数据 + 尾部静音填充
    ↓
Director signoff → 校验 beats/视觉/音频匹配，不通过则阻断
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
5. 已安装 Python 依赖：`pip install pydub`

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

### 强制跳过 Director 校验（不推荐）

```bash
python3 scripts/generate_word_video.py --word breakfast --skip-director
```

## 目录结构

```
vocabulary-video-pipeline/
  SKILL.md                          # 本文件
  README.md                         # 面向外部用户的说明
  scripts/
    generate_word_video.py          # 统一入口脚本（6步流程）
    director_validate.py            # Director 校验器
    generate_audio_beats.py         # TTS + 静音检测
    diagnose_word.py                # 模板诊断引擎
    tts_cost_report.py              # 成本统计
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

- 不要念 PPT：不能是"第一点…第二点…"的生硬拼凑
- 必须是连贯的、有起承转合的叙事性讲解
- 视觉元素只是配合音频节奏出现的辅助，而不是被念出来的标签

## 强制约束

### 1. 每个单词必须包含 origin-chain

`diagnose_word.py` 会在任何策略下自动插入 `origin-chain`。如果某个单词的词源不明确，可以写它的派生历史或语义演变，不能空着。

### 2. Director 校验是必经之门

`director_validate.py` 在渲染之前执行，校验以下内容：

- **词源强制**：检查是否包含 `origin-chain`
- **beats 数量**：按场景类型验证 beats 数量是否匹配（如 ending-summary = points + 2）
- **关键词匹配**：检查 beats 文案中是否包含对应的 point/card/node 关键词
- **音频时长**：确保每个 scene 的音频时长 ≥ lastBeat.endFrame + 40帧
- **防止词源重复**：若已存在 `origin-chain`，`ending-summary` 的 beats 中禁止再出现"拉丁语""源自古英语""词根""演变"等词源关键词（避免叙事断裂）

未通过 Director signoff 的 draft，pipeline 会被强制中断，不会进入渲染。

### 3. TTS 截断已自动防护

`generate_audio_beats.py` 会自动给每个 scene 的 MP3 追加静音尾部，`player.tsx` 与 `Root.tsx` 的时长计算也已统一为 `lastBeat.endFrame + 40`。
所以只要草稿正确，不需要手动调整就能避免截断。

## 已知陷阱

### TTS 语言必须是 `zh-CN`

火山引擎 Seed-TTS 2.0 在不指定 `language` 时，可能会默认输出**繁体中文**发音（如把"吗"读成"嗎"、"话"读成"話"）。

**修复方式**：在调用火山 TTS API 的 `audio` 参数中显式指定：

```json
{
  "audio": {
    "voice_type": "...",
    "language": "zh-CN"
  }
}
```

已在 `generate_audio_beats.py` 中固定此参数。如果未来换用其他 TTS 服务，也需要确认有类似的 Simplified Chinese 锁定机制。
