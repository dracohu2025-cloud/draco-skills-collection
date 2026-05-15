---
name: wechat-article-browseruse
description: 使用 BrowserUse 云浏览器 + Playwright CDP 抓取微信公众号文章，并可直接发布到飞书原生文档。
version: 0.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, mp.weixin.qq.com, browseruse, browser-use, playwright, extraction, markdown, json]
---

# WeChat Article Extraction via BrowserUse

当你要抓取 **微信公众号文章链接**（`mp.weixin.qq.com/s/...`）并且想试一条不依赖本机 CamoFox 服务的新链路时，用这个 skill。

## 当前目录提供什么

- `scripts/run.py`：统一入口
- `scripts/fetch_wechat_article.py`：抓取并输出 Markdown / JSON
- `scripts/publish_wechat_article_to_feishu.py`：抓取并发布到飞书原生文档
- `scripts/smoke-test.sh`：基础环境检查
- `tests/`：回归测试

## 前提条件

### 1）准备 BrowserUse API key

支持两个环境变量名，任选其一：

```bash
export BROWSER_USE_API_KEY=...
# 或
export BROWSERUSE_API_KEY=...
```

### 2）安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 3）如果要发布到飞书

请先安装并登录 `lark-cli`，并确保当前用户身份具备文档导入/读取权限。

## 最常用用法

### 抓取为 Markdown

```bash
python3 scripts/run.py fetch \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

### 抓取为 JSON

```bash
python3 scripts/run.py fetch \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --format json \
  --include-images
```

### 发布为飞书原生文档

```bash
python3 scripts/run.py publish-feishu \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

### 发布到指定飞书文件夹

```bash
python3 scripts/run.py publish-feishu \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --folder-token <folder_token>
```

## 参数说明

### `fetch`

- `--format markdown|json`
- `--include-images`
- `--save PATH`
- `--proxy-country hk`
- `--timeout-seconds 240`
- `--wait-ms 8000`

### `publish-feishu`

- `--folder-token <token>`
- `--json`
- `--proxy-country hk`
- `--timeout-seconds 240`
- `--wait-ms 8000`

## 输出字段

JSON 输出包含：

- `url`
- `title`
- `author`
- `published_at`
- `content_markdown`
- `images`
- `source`

发布结果包含：

- `title`
- `doc_id`
- `doc_url`
- `source_url`
- `validated`
- `doc_preview`

## 一句话总结

**这套 skill 用 BrowserUse 提供远端浏览器，用 Playwright CDP 做稳定 DOM 提取，并可把结果一键发布成飞书原生文档。**
