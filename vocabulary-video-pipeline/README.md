# vocabulary-video-pipeline

基于 [Remotion](https://www.remotion.dev) 的词汇视频自动化生成 skill。输入一个英文单词，自动生成带有中文讲解、TTS 音频和动态视觉效果的教育视频。

## 效果预览

<div align="center">
  <img src="./assets/preview-breakfast.jpg" width="45%" />
  <img src="./assets/preview-lemonade.jpg" width="45%" />
  <br><br>
</div>

## 为什么做这个 skill

面向中小学生的英文视频内容通常需要：
- 每个单词配一份中文叙事讲解
- 视觉元素要跟着音频节奏出现
- 字体、颜色、动画要统一和高质量

这个 skill 把上述流程打包成一个自动化流水线，只需给一个单词，就能走完草稿 → TTS → 渲染 → 上传 → 报告的全部流程。

## 核心特点

- **模板订单制**（Template Order System）：每个新单词自动匹配最优场景组合，库里没有时会触发新模板开发
- **TTS 节奏同步**：基于静音检测自动分割 audio beats，视觉元素与讲述节奏完美同步
- **多元模板库**：Hero 入题、词源链、氛围场景、名言引用、问答卡片、总结收尾等
- **成本透明**：每次生成自动统计 TTS 字符数与成本（约 ¥0.3 / 千字）

## 工作流

```mermaid
graph LR
    A[输入单词] --> B[diagnose 诊断]
    B --> C[生成草稿 JSON]
    C --> D[TTS 合成]
    D --> E[静音检测分 beats]
    E --> F[Remotion 渲染 MP4]
    F --> G[飞书云盘上传]
    G --> H[成本报告]
```

## 前提条件

1. 已克隆 [vocabulary-video-pipeline](https://github.com/dracohu2025-cloud/vocabulary-video-pipeline) 项目到本地
2. 已安装 Node.js、npm、Python 3
3. 已安装 Python 依赖：`pip install pydub requests`
4. 已配置火山引擎 TTS 的 `.env` 参数
5. 已安装 `lark-cli` 并登录（用于飞书上传）

## 快速开始

### 1. 配置项目路径

```bash
export VOCAB_VIDEO_PROJECT_ROOT=/path/to/vocabulary-video-pipeline
```

如果不设置，脚本会自动尝试常见路径。

### 2. 一键生成视频

```bash
python3 scripts/generate_word_video.py --word breakfast
```

运行后会自动执行：
1. 诊断单词并生成草稿
2. 合成 TTS 并分割节奏
3. 渲染视频
4. 上传飞书云盘
5. 打印成本报告

### 3. 分阶段使用

只生成草稿（方便手动修改文案）：
```bash
python3 scripts/generate_word_video.py --word breakfast --draft-only
```

只到音频节奏为止：
```bash
python3 scripts/generate_word_video.py --word breakfast --audio-only
```

跳过渲染和上传：
```bash
python3 scripts/generate_word_video.py --word breakfast --skip-render --skip-upload
```

## 模板库一览

| 场景 | 类型 | 说明 |
|------|------|------|
| `hero-word` | 入题 | 展示单词、音标、标签 |
| `origin-chain` | 词源 | 展示词汇历史演变链 |
| `meaning-compare` | 辨析 | 对比近义词或概念 |
| `full-screen-mood` | 氛围 | 情绪化场景描述 |
| `quote-page` | 引用 | 英文名句及中文翻译 |
| `answer-cards` | 问答 | 三个问题卡片式解答 |
| `ending-summary` | 总结 | 公式 + 要点 + 结语 |

## 常见问题

**Q: 生成草稿后想改文案怎么办？**
A: 草稿在项目的 `data/{word}-draft.json` 中，可以直接手动修改后重新运行 `generate_word_video.py`。

**Q: TTS 成本是多少？**
A: 使用火山引擎/豆包 TTS 2.0 时，约 ¥0.3 / 千字符。每次生成后会自动统计并打印。

**Q: 渲染一个视频要多久？**
A: 一分钟左右的视频约需 10-15 分钟，建议后台运行。

## 相关仓库

- [主项目: vocabulary-video-pipeline](https://github.com/dracohu2025-cloud/vocabulary-video-pipeline)
- [技能收藏: Draco-Skills-Collection](https://github.com/dracohu2025-cloud/draco-skills-collection)
