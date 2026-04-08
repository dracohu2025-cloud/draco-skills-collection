# 微信公众号文章抓取与飞书发布

把一篇微信公众号文章链接，直接变成更干净的 Markdown、JSON，或者一篇飞书原生文档。

这个工具不是简单抓原始 HTML，而是先用 `camofox-browser` 打开真实页面，读取结构化 snapshot 和图片信息，再做公众号专用清洗，所以更适合处理：正文区、图片顺序、列表、引用块、折行这些问题。

![wechat-article-camofox 工作流预览](./assets/wechat-article-camofox-flow.svg)

## 适合谁用

- 想把公众号文章稳定保存成 Markdown / JSON 的人
- 想把公众号文章快速搬到飞书原生文档里继续编辑的人
- 想要一条“自动安装依赖 + 自动抓取 + 自动清洗”的链路，而不是自己手动拼浏览器抓取脚本的人

## 这套工具的亮点

- **自动安装 CamouFox 抓取层**：首次运行会自动检查 `camofox-browser`，缺失时自动 clone 仓库并执行 `npm install`
- **自动启动本地浏览器服务**：服务没起来会自动拉起，不需要先手动跑一轮
- **抓取时有阶段性进度输出**：会持续提示健康检查、安装依赖、启动服务、等待服务就绪这些阶段
- **结构化正文清洗**：不是只抓一坨 HTML，而是基于 snapshot 做标题、段落、列表、引用块、图片块重建
- **修复常见公众号排版问题**：包括多余圆点、列表和正文粘连、inline code 被拆行、blockquote 丢块等
- **支持飞书发布**：可以直接创建飞书原生文档，并回读校验结果

## 工作流长什么样

```text
公众号文章链接
  ↓
自动检查 camofox-browser 是否健康
  ↓
缺失时自动 clone + npm install
  ↓
自动启动 camofox-browser
  ↓
读取 snapshot + images
  ↓
过滤公众号噪音、重建图文块
  ↓
输出 Markdown / JSON / 飞书文档
```

## 前置要求

### 基础环境

需要机器上已有：

- Python 3.9+
- `git`
- Node.js 18+
- `npm`

检查命令：

```bash
python3 --version
git --version
node --version
npm --version
```

### 如果你要发布到飞书

需要本机已经安装并登录 `lark-cli`。

例如：

```bash
npm install -g @larksuiteoapi/lark-cli
lark-cli login
```

## 安装

```bash
git clone https://github.com/dracohu2025-cloud/draco-skills-collection.git
cd draco-skills-collection/wechat-article-camofox
```

这个项目的运行时依赖主要是 Python 标准库 + 外部命令行工具，所以**抓取本身不需要额外 pip 安装第三方包**。

如果你想跑测试：

```bash
pip install -r requirements.txt
```

## 快速开始

### 1）统一入口：抓成 Markdown

```bash
python3 scripts/run.py fetch \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

### 2）统一入口：抓成 JSON

```bash
python3 scripts/run.py fetch \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --format json
```

### 3）统一入口：带图片信息一起输出

```bash
python3 scripts/run.py fetch \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --format json \
  --include-images
```

### 4）统一入口：直接发布到飞书原生文档

```bash
python3 scripts/run.py publish-feishu \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

### 5）保存到本地文件

```bash
python3 scripts/run.py fetch \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --save /tmp/article.md
```

## 首次运行时你会看到什么

如果机器上还没有 `camofox-browser`，脚本会在 stderr 里持续输出进度，例如：

```text
[wechat-article-camofox] Checking camofox-browser health on :9377
[wechat-article-camofox] camofox-browser is not healthy yet; bootstrapping now
[wechat-article-camofox] Installing camofox-browser dependencies
[wechat-article-camofox] Installing camofox-browser: cloning repo into ...
[wechat-article-camofox] Installing camofox-browser: running npm install (first run may take a while)
[wechat-article-camofox] Starting camofox-browser service
[wechat-article-camofox] Waiting for camofox-browser health check to pass
[wechat-article-camofox] camofox-browser is healthy
```

如果服务已经可用，通常只会看到：

```text
[wechat-article-camofox] Checking camofox-browser health on :9377
[wechat-article-camofox] camofox-browser is healthy
```

## 输出结果说明

### Markdown

默认会输出：

- 标题
- 作者 / 发布时间（如果能识别）
- 清洗后的正文
- 按正文顺序插回去的图片块

### JSON

主要字段包括：

- `url`
- `title`
- `author`
- `published_at`
- `content_markdown`
- `images`
- `source`

### 飞书发布结果

发布成功后会返回：

- `doc_id`
- `doc_url`
- `validated`
- `doc_preview`

## 批量处理用法

仓库里附带了一个示例 URL 列表：

- `templates/article_urls.example.txt`

你可以这样批量抓取：

```bash
while IFS= read -r url; do
  [ -z "$url" ] && continue
  python3 scripts/run.py fetch "$url" --format json
  echo "-----"
done < templates/article_urls.example.txt
```

如果你只想批量保存成 Markdown：

```bash
mkdir -p /tmp/wechat-articles
n=1
while IFS= read -r url; do
  [ -z "$url" ] && continue
  python3 scripts/run.py fetch "$url" --save "/tmp/wechat-articles/$n.md"
  n=$((n + 1))
done < templates/article_urls.example.txt
```

## 常见问题

### 1）为什么第一次运行比较慢？

因为首次运行可能会自动：

- clone `camofox-browser`
- 执行 `npm install`
- 下载 CamouFox 相关浏览器依赖

这是一次性成本，后面通常会快很多。

### 2）如果提示缺少 `git` 或 `npm` 怎么办？

这个工具会直接报清晰错误。先把这些基础依赖装好，再重新运行即可。

### 3）为什么有时仍然会看到极个别排版不完美？

因为公众号富文本结构并不统一。当前版本已经修掉一批高频问题，但复杂卡片、非常特殊的混排、少数嵌套结构，仍可能需要继续补规则。

### 4）飞书发布为什么不能直接删除旧文档？

这取决于飞书授权 scope。若授权里没有 `space:document:delete`，工具无法硬删除旧文档，只能用覆盖废弃提示的方式规避误用。

## 文件结构

```text
wechat-article-camofox/
├── README.md
├── SKILL.md
├── .env.example
├── requirements.txt
├── assets/
│   └── wechat-article-camofox-flow.svg
├── scripts/
│   ├── run.py
│   ├── fetch_wechat_article.py
│   └── publish_wechat_article_to_feishu.py
├── templates/
│   └── article_urls.example.txt
└── tests/
    └── test_fetch_wechat_article.py
```

## 相关说明

- `README.md`：面向普通用户的使用说明
- `SKILL.md`：面向 Hermes skill 场景的技能说明
- `scripts/run.py`：统一入口，适合公开仓库直接使用
- `scripts/fetch_wechat_article.py`：核心抓取脚本
- `scripts/publish_wechat_article_to_feishu.py`：飞书发布 workflow

## 一句话总结

**如果你想把公众号文章稳定抓下来，并尽量少踩页面结构和排版坑，这个工具就是一条更省心的自动化链路。**
