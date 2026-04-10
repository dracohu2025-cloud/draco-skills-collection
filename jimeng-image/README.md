# 即梦图片生成

一个独立的小工具：直接用火山引擎 Ark 上的 **即梦 / Doubao Seedream** 生成图片。

它适合这些场景：
- 文生图单张
- 文生图一组连续图片
- 图生图单张
- 多张参考图生成单张图
- 批量 prompt 跑图
- 把返回的图片 URL 自动下载到本地

当前默认模型：
- `doubao-seedream-5-0-260128`

## 亮点

- **独立于 Nano Banana 2**，直接走火山引擎 Ark
- **支持单图 / 批量 / workflow 三种模式**
- **支持参考图 URL 输入**，包括单张和多张参考图
- **支持一组连续图片生成**（`sequential_image_generation=auto`）
- **零第三方 Python 依赖**，脚本主体只用标准库

## 效果示例

下面这张图是用这个项目真实生成后保存下来的示例图：

<img src="./assets/example-jimeng-image.jpg" alt="即梦生成示例图" />

## 目录结构

```text
jimeng-image/
├── README.md
├── SKILL.md
├── .env.example
├── .gitignore
├── assets/
│   └── example-jimeng-image.jpg
├── examples/
│   └── prompts.txt
└── scripts/
    ├── run.py
    ├── jimeng_image.py
    ├── jimeng_batch.py
    ├── jimeng_workflow.py
    ├── jimeng_run.py
    └── smoke-test.sh
```

## 前置要求

- Python 3.9+
- 已开通火山引擎 Ark 图像接口权限
- 环境变量里可用的 API key

至少需要：

```bash
VOLCENGINE_API_KEY=***
```

可选别名：

```bash
SEEDREAM_API_KEY=***
JIMENG_API_KEY=***
JIMENG_MODEL_NAME=doubao-seedream-5-0-260128
```

## 快速开始

### 1）准备环境变量

```bash
cd jimeng-image
cp .env.example .env
# 然后填入 VOLCENGINE_API_KEY
```

### 2）跑帮助确认 CLI 没问题

```bash
python3 scripts/run.py --help
```

### 3）最简单：文生图单张

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '星际穿越，黑洞里冲出一辆破碎的复古列车，电影大片感，强对比，动态模糊，16:9' \
  --size 2k \
  --output ./outputs/train.jpg
```

### 4）生成一组连续图片

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '生成一组共4张连贯插画，核心为同一庭院一角的四季变迁，以统一风格展现四季独特色彩、元素与氛围' \
  --sequential auto \
  --max-images 4 \
  --outdir ./outputs/four-seasons
```

### 5）图生图单张

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '生成狗狗趴在草地上的近景画面' \
  --image 'https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imageToimage.png' \
  --output ./outputs/dog.jpg
```

### 6）多张参考图生成单张图

```bash
python3 scripts/run.py \
  --mode single \
  --prompt '将图1的服装换为图2的服装' \
  --image 'https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imagesToimage_1.png' \
  --image 'https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imagesToimage_2.png' \
  --output ./outputs/outfit-swap.jpg
```

### 7）批量模式

```bash
python3 scripts/run.py \
  --mode batch \
  --input ./examples/prompts.txt \
  --outdir ./outputs/batch \
  --zip
```

### 8）workflow 模式

```bash
python3 scripts/run.py \
  --mode workflow \
  --title '海报实验' \
  --input ./examples/prompts.txt \
  --output-dir ./outputs/jobs \
  --size 2k
```

## 参数说明

| 参数 | 说明 |
|---|---|
| `--mode` | `single` / `batch` / `workflow` |
| `--prompt` | 直接传入 prompt |
| `--input` | 从文件读 prompt；批量模式按空行拆分 |
| `--image` | 参考图 URL；可重复传多次 |
| `--output` | 单图输出路径 |
| `--outdir` | 多图输出目录 |
| `--output-dir` | workflow 根目录 |
| `--model` | 模型名，默认 `doubao-seedream-5-0-260128` |
| `--size` | `2k`、`3k` 或 `WIDTHxHEIGHT`，如 `1344x768` |
| `--response-format` | `url` 或 `b64_json` |
| `--sequential` | `disabled` 或 `auto` |
| `--max-images` | 连续生成组图数量，需配合 `--sequential auto` |
| `--watermark` / `--no-watermark` | 是否加水印 |
| `--zip` | 批量或 workflow 结果打包 zip |

## 当前已验证的接口行为

我这里已经真实验证过：
- 文生图单张：可用
- 图生图单张：可用
- 连续生成 2 张图：可用

并确认当前 API 对 `size` 的要求是：
- `2k`
- `3k`
- 或 `WIDTHxHEIGHT`

像 `1K` 这种写法会直接报错，别跟接口抬杠。

## 输入参考图的边界

当前 v1 版对参考图输入的策略是：
- **只接受 http/https URL**
- 暂不直接接受本地文件路径作为参考图输入

这是故意的，不是忘了做。
因为官方示例明确展示的是 URL 形态，而本地文件直传这件事在当前 API 示例里没说清楚，硬猜只会埋雷。

## smoke test

```bash
bash scripts/smoke-test.sh
```

它会检查：
- `python3`
- `scripts/run.py --help`
- `scripts/jimeng_image.py --help`
- `VOLCENGINE_API_KEY` 是否存在

## 一句话总结

**如果你想用更便宜的火山引擎即梦 / Seedream 替代 Nano Banana 2 做图片生成，这个目录就是那把更省钱的锤子。**
