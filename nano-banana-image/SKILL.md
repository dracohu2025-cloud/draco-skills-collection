---
name: nano-banana-image
description: 独立的 Nano Banana 2 / Gemini 3.1 Flash Image 图片生成 skill。支持单图、批量、workflow、JSON Prompt Mode、飞书上传；不依赖文章封面生成流程。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [image-generation, google, gemini, nano-banana, nano-banana-2, openrouter, feishu]
---

# Nano Banana 2 Image

当用户想要：
- 单独用 Nano Banana 2 / Gemini 3.1 Flash Image 生成图片
- 不经过“文章理解 → 封面图”的那套流程
- 做通用插图、海报、产品头图、banner、公众号头图
- 批量跑多个 prompt
- 生成后上传飞书

就用这个 skill。

## 这是什么

这是一个**独立图片生成 skill**，核心职责只有一件事：
给 prompt，调用 OpenRouter 上的 `google/gemini-3.1-flash-image-preview` 出图。

它和 `article-to-wechat-cover` 的边界很明确：
- `article-to-wechat-cover` 偏工作流，先读文章，再提炼主题，再出图
- `nano-banana-image` 偏底层出图器，直接把 prompt 变成图

## 默认能力

- 单图生成
- 批量生成
- workflow 目录化生成
- JSON Prompt Mode
- 模板化 prompt（wechat-cover / product-hero / poster / landing-hero）
- 飞书上传
- 自定义 aspect ratio

## 依赖环境变量

至少需要：
- `OPENROUTER_API_KEY`

推荐：
- `OPENROUTER_IMAGE=google/gemini-3.1-flash-image-preview`

可选：
- `GEMINI_API_KEY`

## 统一入口

公开仓库里优先用：

```bash
python3 scripts/run.py --mode single --prompt '一只香蕉机器人坐在图书馆里读书'
```

本地 Hermes skill 脚本路径：
- `scripts/nano_banana_image.py`
- `scripts/nano_banana_batch.py`
- `scripts/nano_banana_workflow.py`
- `scripts/nano_banana_run.py`

## 推荐命令

### 单图

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '一个现代 AI 工作台界面，深色背景，蓝绿色科技风，适合 SaaS 头图' \
  --template landing-hero \
  --aspect-ratio 16:9 \
  --output ./outputs/hero.png
```

### 批量

```bash
python3 scripts/run.py \
  --mode batch \
  --input ./examples/prompts.txt \
  --outdir ./outputs/batch \
  --zip
```

### workflow

```bash
python3 scripts/run.py \
  --mode workflow \
  --title '产品头图实验' \
  --input ./examples/prompts.txt \
  --output-dir ./outputs/jobs \
  --aspect-ratio 16:9
```

### 上传飞书

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '一个未来感 AI 控制中枢，适合横幅头图' \
  --upload-feishu
```

## JSON Prompt Mode

默认开启。

逻辑是：
1. 读入自然语言 prompt
2. 做轻量解析
3. 合并模板默认值
4. 生成结构化 JSON spec
5. 把 JSON 作为 authoritative image spec 发给模型

这样做比纯 prompt 更稳，尤其在：
- 批量任务
- 多次复现
- 同一视觉体系延展

如果用户明确要原始 prompt，才加：

```bash
--raw-prompt
```

## 验证建议

先跑：

```bash
bash scripts/smoke-test.sh
```

再跑最小真实生成：

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '一只未来香蕉机器人在图书馆里读书，温暖光线，插画风格' \
  --output /tmp/nano-banana-demo.png
```

## 完成标准

满足下面几点，才算这条链路真的可用：
- `scripts/run.py --help` 正常
- `scripts/nano_banana_image.py --help` 正常
- 能成功调用 OpenRouter 返回图片
- 输出文件 MIME type 与文件内容一致
- 若启用飞书上传，能返回有效 `feishu_url`
