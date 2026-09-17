# Archived skill: wechat-article-browseruse

Original path: `productivity/wechat-article-browseruse`

Consolidation reason: BrowserUse extraction is one backend for WeChat article ingestion.

---

---
name: wechat-article-browseruse
description: 使用 BrowserUse 云浏览器 + Playwright CDP 抓取微信公众号文章，并可直接发布到飞书原生文档。
version: 0.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, mp.weixin.qq.com, browseruse, browser-use, playwright, extraction, markdown, json]
    related_skills: [wechat-article-camofox, lark-native-doc-workflow]
---

# WeChat Article Extraction via BrowserUse

当你要抓取 **微信公众号文章链接**（`mp.weixin.qq.com/s/...`）并且想试一条不依赖本机 CamoFox 服务的新链路时，用这个 skill。

它的思路很直接：

1. 用 **BrowserUse 云浏览器** 拉起远端浏览器
2. 通过 **Playwright CDP** 连进去
3. 打开公众号文章页
4. 直接读取 `#js_content` / `#img-content` 的 HTML、文本和图片
5. 在本地把 HTML 转成 Markdown，并返回结构化结果

这条链路是 **确定性 DOM 提取**，不是让 LLM 自由发挥摘要正文，所以结果更稳，成本也更可控。

## 适用场景

- 想验证 BrowserUse 能不能稳定打开微信公众号文章
- 想绕开本机浏览器服务，改用云端浏览器
- 想拿到 Markdown / JSON / 图片列表
- 想把旧的 CamoFox 抓取链路做一个 BrowserUse 版本平替

## 当前提供的文件

- `scripts/fetch_wechat_article.py`：主抓取脚本
- `scripts/publish_wechat_article_to_feishu.py`：抓取并发布到飞书原生文档
- `tests/test_fetch_wechat_article.py`：抓取与清洗测试
- `tests/test_publish_wechat_article_to_feishu.py`：发布流程测试

## 前提条件

### 1）准备 API Key

脚本支持这两个环境变量名字，任意一个都行：

```bash
export BROWSER_USE_API_KEY=...
# 或
export BROWSERUSE_API_KEY=...
```

### 2）安装 Python 依赖

```bash
source venv/bin/activate
python -m pip install browser-use-sdk playwright beautifulsoup4 markdownify
```

## 最常用用法

### 0）直接抓取并发布到飞书原生文档

```bash
python ~/.hermes/skills/productivity/wechat-article-browseruse/scripts/publish_wechat_article_to_feishu.py \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

如果要直接放进指定飞书文件夹：

```bash
python ~/.hermes/skills/productivity/wechat-article-browseruse/scripts/publish_wechat_article_to_feishu.py \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --folder-token <folder_token>
```

这个 workflow 会：

- 用 BrowserUse 抓取公众号文章
- 保留正文图片
- 先把正文清理成适合导入的 Markdown
- 通过 `lark-cli drive +import --type docx` 导入成飞书原生文档
- 回读飞书文档做校验

### 1）抓成 Markdown

```bash
python ~/.hermes/skills/productivity/wechat-article-browseruse/scripts/fetch_wechat_article.py \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

### 2）抓成 JSON

```bash
python ~/.hermes/skills/productivity/wechat-article-browseruse/scripts/fetch_wechat_article.py \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --format json
```

### 3）把图片一起塞回正文 Markdown，并额外返回图片列表

```bash
python ~/.hermes/skills/productivity/wechat-article-browseruse/scripts/fetch_wechat_article.py \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --format json \
  --include-images
```

### 4）保存到文件

```bash
python ~/.hermes/skills/productivity/wechat-article-browseruse/scripts/fetch_wechat_article.py \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --save /tmp/wechat-article.md
```

## 参数说明

### 抓取脚本 `fetch_wechat_article.py`

- `--format markdown|json`：输出格式，默认 `markdown`
- `--include-images`：正文里保留图片，并在 JSON 中返回 `images`
- `--save PATH`：保存到文件
- `--proxy-country hk`：BrowserUse 代理国家码，默认 `hk`
- `--timeout-seconds 240`：BrowserUse 浏览器会话超时，最大 240
- `--wait-ms 8000`：额外等待懒加载内容的时间

### 发布脚本 `publish_wechat_article_to_feishu.py`

- `--folder-token <token>`：把原生文档导入到指定飞书文件夹
- `--json`：输出完整 JSON 结果，而不是只打印 doc_url
- `--proxy-country hk`：沿用抓取脚本的代理国家码
- `--timeout-seconds 240`：沿用抓取脚本的浏览器会话超时
- `--wait-ms 8000`：沿用抓取脚本的懒加载等待时间

## 默认策略

- 默认代理地区：`hk`
- 默认额外等待：`8000ms`
- 默认 source 标记：`browseruse_cdp_html`

之所以默认 `hk`，是因为它对公众号页这类中文内容站更靠谱；实测比盲开默认线路更稳。

## 输出字段

JSON 输出包含：

- `url`
- `title`
- `author`
- `published_at`
- `content_markdown`
- `images`
- `source`

## 实现细节

抓取脚本会：

1. 校验 URL 是否是 `mp.weixin.qq.com/s/...`
2. 读取 BrowserUse API key
3. 创建 BrowserUse 云浏览器
4. 用 Playwright `connect_over_cdp()` 接入
5. 等待 `#js_content` 或 `#img-content`
6. 提取：
   - 标题：`#activity-name` / `h1` / `document.title`
   - 作者：`#js_name` 等常见节点
   - 发布时间：`#publish_time`
   - 正文 HTML / 文本 / 图片列表
7. 用 `BeautifulSoup` 清理噪音节点
8. 用 `markdownify` 转成 Markdown，并做后处理
9. 关闭远端浏览器会话

发布脚本会额外做两步：

10. 去掉正文里重复的顶层 H1，并在开头补上原文链接
11. 将整理后的 Markdown 临时写入本地文件，再通过 `lark-cli drive +import --type docx` 导入为飞书原生文档，随后回读校验

## 已知边界

- 这是 **正文抓取器 / 发布器**，不是通用网页抽取器
- 目前作者字段优先拿公众号账号名，不保证一定是文内署名作者
- 复杂图文混排、特别花的样式，转 Markdown 后仍可能有轻微格式损失
- 发布到飞书时依赖当前 `lark-cli` 用户身份具备 `docs:document:import` 与文档读取相关 scope
- 导入路径当前走 `drive +import`，因此本地临时文件必须以相对路径喂给 `lark-cli`；脚本内部已经处理了这个坑

## 何时优先用它

当你提到：

- BrowserUse 抓公众号
- 微信公众号文章 BrowserUse 版
- 不想走 CamoFox，想走云浏览器
- 想验证 BrowserUse 对公众号页是否稳定

## 一句话总结

**这套 skill 用 BrowserUse 提供远端浏览器，用 Playwright CDP 做稳定 DOM 提取，并可把结果一键发布成飞书原生文档。**
