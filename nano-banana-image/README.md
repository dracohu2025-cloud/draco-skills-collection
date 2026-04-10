# Nano Banana 2 图片生成

一个独立的小工具：直接用 OpenRouter + Gemini 3.1 Flash Image（也就是很多人嘴里的 Nano Banana 2）生成图片。

它和 `article-to-wechat-cover` 是两条线：
- `article-to-wechat-cover` 先读文章，再自动提炼主题并生成公众号封面
- **这个工具只管图片生成本身**，你给 prompt，它负责出图

适合这些场景：
- 快速做样图、插图、头图、横幅图
- 需要单张、批量、多任务工作流三种模式
- 想把自然语言 prompt 自动整理成结构化 JSON prompt 再发给图像模型
- 生成后顺手上传到飞书云盘

## 效果预览

下面这张图，就是通过这条 Nano Banana 2 出图链路生成的示例横幅：

<img src="./assets/example-generated-banner.jpg" alt="Nano Banana 2 生成示例图" />

## 亮点

- **独立于文章封面工具**，不依赖 `article-to-wechat-cover`
- **默认模型就是 Gemini 3.1 Flash Image**
- **支持单张 / 批量 / workflow 三种模式**
- **默认启用 JSON Prompt Mode**，减少 prompt 漂移
- **支持预设模板**：通用、公众号封面、产品头图、海报、落地页 Hero
- **可选上传飞书云盘**
- **零第三方 Python 依赖**，脚本主体只用标准库

## 目录结构

```text
nano-banana-image/
├── README.md
├── SKILL.md
├── .env.example
├── assets/
│   └── example-generated-banner.jpg
├── examples/
│   └── prompts.txt
└── scripts/
    ├── run.py
    ├── nano_banana_image.py
    ├── nano_banana_batch.py
    ├── nano_banana_workflow.py
    ├── nano_banana_run.py
    └── smoke-test.sh
```

## 前置要求

### 1）基础环境

- Python 3.9+
- 能访问 OpenRouter

### 2）环境变量

至少需要：

```bash
OPENROUTER_API_KEY=***
```

推荐同时配置：

```bash
OPENROUTER_IMAGE=google/gemini-3.1-flash-image-preview
```

如果你要上传飞书，还需要本机已安装并登录 `lark-cli`。

## 快速开始

### 1）先准备环境变量

```bash
cd nano-banana-image
cp .env.example .env
# 然后自己填上 OPENROUTER_API_KEY
```

### 2）跑帮助确认脚本没问题

```bash
python3 scripts/run.py --help
```

### 3）最简单：单张出图

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '一只未来香蕉机器人坐在图书馆里读书，温暖光线，干净插画风格，细节丰富' \
  --aspect-ratio 1:1 \
  --output ./outputs/banana-reader.png
```

### 4）做一张 16:9 横幅图

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '一个 AI 工作台界面漂浮在深色空间中，蓝绿色科技感，适合产品发布页头图' \
  --template landing-hero \
  --aspect-ratio 16:9 \
  --output ./outputs/hero.png
```

### 5）批量出图

`examples/prompts.txt` 里用空行分隔多个 prompt：

```bash
python3 scripts/run.py \
  --mode batch \
  --input ./examples/prompts.txt \
  --outdir ./outputs/batch \
  --zip
```

### 6）workflow 模式

```bash
python3 scripts/run.py \
  --mode workflow \
  --title '四张产品头图实验' \
  --input ./examples/prompts.txt \
  --output-dir ./outputs/jobs \
  --aspect-ratio 16:9 \
  --template landing-hero
```

### 7）生成后自动上传飞书

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '一个现代 AI 团队协作场景，简洁、专业、科技感' \
  --upload-feishu
```

## JSON Prompt Mode

这个工具默认不会把原始 prompt 生吞硬塞给模型。

它会先把你的 prompt 组织成结构化 JSON，字段包括：
- subject
- scene
- style
- composition
- lighting
- palette
- negative constraints
- must include / must avoid

这样做的好处很直接：
- 可复用
- 可审查
- 更适合批量任务
- 同一类图更稳，不容易一会儿像海报一会儿像截图

如果你就想裸奔，直接加：

```bash
--raw-prompt
```

## 常用参数

| 参数 | 说明 |
|---|---|
| `--mode` | `single` / `batch` / `workflow` |
| `--prompt` | 直接传单条 prompt |
| `--input` | 从文件读取 prompt；批量模式按空行拆分 |
| `--output` | 单图输出路径 |
| `--outdir` | 批量输出目录 |
| `--output-dir` | workflow 根目录 |
| `--aspect-ratio` | 支持 `1:1`、`16:9`、`21:9`、`2.35:1` 等 |
| `--template` | `auto` / `generic` / `wechat-cover` / `product-hero` / `poster` / `landing-hero` |
| `--raw-prompt` | 关闭 JSON Prompt Mode |
| `--upload-feishu` | 生成后上传飞书云盘 |
| `--dump-json-spec` | 导出最终 JSON 规格 |
| `--must-include` | 强制出现的视觉元素，逗号分隔 |
| `--must-avoid` | 强制避免的视觉元素，逗号分隔 |

## 输出结果

成功后通常会输出：

```bash
output=...
bytes=...
mime_type=...
model=...
provider=...
aspect_ratio=...
```

如果上传飞书，还会多出：

```bash
feishu_token=...
feishu_url=...
```

## smoke test

先别急着打模型，先跑这个：

```bash
bash scripts/smoke-test.sh
```

它会检查：
- Python 是否可用
- `scripts/run.py --help` 是否正常
- `scripts/nano_banana_image.py --help` 是否正常
- 是否看得到 `OPENROUTER_API_KEY`

## 常见问题

### 1）为什么我明明写了 PNG，最后出来是 JPG？

模型返回什么 MIME type，就该尊重什么。硬把 JPEG 内容装进 `.png` 后缀，只会制造烂摊子。

### 2）为什么默认还要做 JSON 包装？

因为纯自然语言 prompt 在批量场景里太飘。演示时看着灵，复用时就容易翻车。

### 3）这和 `article-to-wechat-cover` 有什么关系？

它们共用同一条 Nano Banana 2 出图底层，但职责不同：
- `article-to-wechat-cover`：文章理解 + prompt 生成 + 封面图工作流
- `nano-banana-image`：纯图片生成器

## 一句话总结

**如果你只想把 Nano Banana 2 当成一把干净利落的出图锤子来用，这个目录就是。**
