---
name: jimeng-image
description: 使用火山引擎 Ark 上的即梦 / Doubao Seedream 生成图片。支持文生图、图生图、多参考图、连续组图、批量模式与 workflow 模式。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [image-generation, jimeng, seedream, volcengine, ark, doubao]
---

# Jimeng Image

当用户想要：
- 用更便宜的即梦 / Seedream 替代 Nano Banana 2
- 直接调用火山引擎 Ark 生图
- 做文生图、图生图、多参考图生成
- 一次生成一组连贯图片
- 批量跑多个 prompt

就用这个 skill。

## 默认配置

- API：`https://ark.cn-beijing.volces.com/api/v3/images/generations`
- 默认模型：`doubao-seedream-5-0-260128`
- 认证：`VOLCENGINE_API_KEY`（也兼容 `SEEDREAM_API_KEY` / `JIMENG_API_KEY`）

## 支持能力

- 文生图单张
- 文生图一组图（`sequential_image_generation=auto`）
- 图生图单张
- 多参考图生成单张图
- 批量 prompt
- workflow 目录化输出

## 当前 v1 边界

- 参考图输入当前只支持 **URL**
- 暂不直接接受本地文件路径作为参考图输入
- 输出会自动下载到本地，不只返回 URL

## 统一入口

公开仓库建议使用：

```bash
python3 scripts/run.py --mode single --prompt '一张极具视觉冲击力的海报，黑洞，破碎列车，16:9'
```

## 推荐命令

### 文生图单张

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '星际穿越，黑洞里冲出一辆快支离破碎的复古列车，电影大片，动感，对比色，光线追踪，动态模糊，景深，16:9' \
  --size 2k \
  --output ./outputs/train.jpg
```

### 文生图组图

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '生成一组共4张连贯插画，核心为同一庭院一角的四季变迁，以统一风格展现四季独特色彩、元素与氛围' \
  --sequential auto \
  --max-images 4 \
  --outdir ./outputs/four-seasons
```

### 图生图

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '生成狗狗趴在草地上的近景画面' \
  --image 'https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imageToimage.png' \
  --output ./outputs/dog.jpg
```

### 多参考图生成

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '将图1的服装换为图2的服装' \
  --image 'https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imagesToimage_1.png' \
  --image 'https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imagesToimage_2.png' \
  --output ./outputs/outfit-swap.jpg
```

## 已验证事实

- 当前 API 接受的 `size` 是：
  - `2k`
  - `3k`
  - `WIDTHxHEIGHT`
- 文生图单张、图生图单张、连续 2 图都已真实跑通
- 返回结构里 `data` 是数组，每个元素至少包含：
  - `url`
  - `size`
- `usage.generated_images` 和 `usage.total_tokens` 可用于记录成本信息

## 验证建议

先跑：

```bash
bash scripts/smoke-test.sh
```

再跑最小真实请求：

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '一只黑白配色的几何风格小猫头像，简洁，纯色背景' \
  --size 2k
```
