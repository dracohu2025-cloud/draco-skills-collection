---
name: wechat-article-camofox
description: 使用本机部署的 camofox-browser 稳定抓取微信公众号文章链接内容，优先读取浏览器 accessibility snapshot，并对公众号页噪音做专用清洗，输出 Markdown 或 JSON。
version: 1.1.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, mp.weixin.qq.com, camofox, browser, extraction, markdown, json]
    related_skills: [ocr-and-documents, hermes-agent]
---

# WeChat Article Extraction via Camofox

当你要稳定获取 **微信公众号文章链接**（`mp.weixin.qq.com/s/...`）的正文内容时，使用这个 skill，喵。

它依赖 `camofox-browser` 作为浏览器采集层，读取页面 accessibility snapshot，再做公众号页面专用清洗，得到更干净的正文输出。

当前版本已经升级成 **方案 B：自动安装型**：首次运行会先检查本机 `camofox-browser` 是否可用；如果还没装，会尝试自动 clone 仓库并执行 `npm install`，然后再拉起服务。也就是说，用户不必再手动预装 CamouFox，只需要本机已有 `git` 和 `Node.js 18+ / npm`，喵。

## 适用场景

- 抓取微信公众号文章正文
- 输出 Markdown 或 JSON
- 普通静态抓取噪音过多，或浏览器兜底更稳时
- 后续想把公众号抓取能力接到 Hermes 或自己的脚本链路里

## 这版 skill 提供什么

- `scripts/run.py`：统一入口（推荐公开仓库用户直接使用）
- `scripts/fetch_wechat_article.py`：主提取脚本
- `scripts/publish_wechat_article_to_feishu.py`：抓取并发布到飞书原生文档（含正文图片）
- `templates/article_urls.example.txt`：示例输入
- 若装进 Hermes 本机环境，可继续提供命令入口：`wechat-article-fetch`
- 若装进 Hermes 本机环境，可继续提供命令入口：`wechat-article-to-feishu`
- 若本机已存在 `camofox-browser-start` / `status` / `stop` 管理脚本，会优先复用这些入口；若没有，Python 脚本也能直接完成自动安装与拉起
- 首次运行或服务未就绪时，脚本会在 stderr 打印阶段性进度：检查健康状态、安装依赖、clone 仓库、执行 `npm install`、启动服务、等待健康检查通过
- 依赖的 `camofox-browser` 服务管理脚本（若本机已配置）：
  - `camofox-browser-start`
  - `camofox-browser-status`
  - `camofox-browser-stop`

这次实测后又补了两条关键经验：

- **写飞书原生文档并做回读校验** 是这条 workflow 的基本要求，不是可选项
- **图片要按原文顺序插回正文**，而不是统一堆到文末

## 前提条件

1. 本机已安装 `git`
2. 本机已安装 `Node.js 18+` 与 `npm`
3. 目标链接为可公开访问的公众号文章页

可选预检查：

```bash
node --version
npm --version
git --version
```

> `camofox-browser` 本身不再要求手动预装。首次运行 `wechat-article-fetch` / `wechat-article-to-feishu` 时，脚本会自动检查；若缺失，会自动 clone `https://github.com/jo-inc/camofox-browser.git` 并执行 `npm install`，然后再尝试拉起本地服务。

## 最常用用法

### 0）抓取并直接发布到飞书原生文档

```bash
python3 scripts/run.py publish-feishu "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

这个 workflow 会执行：

- 抓取公众号文章
- 清洗正文与标题
- 自动提取正文图片并按原文顺序写进飞书原生文档正文
- 回读飞书文档做校验

如果你的任务目标里包含“放到飞书文档里”，这是优先入口。


### 1）抓取为 Markdown

```bash
python3 scripts/run.py fetch "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

如果本机还没有 `camofox-browser`，它会先自动安装；如果服务未启动，它会自动拉起服务，再继续抓取。首次运行过程中会在 stderr 持续打印阶段性进度，例如：检查健康状态、clone 仓库、执行 `npm install`、启动服务、等待健康检查通过。

### 2）输出 JSON

```bash
python3 scripts/run.py fetch "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" --format json
```

### 3）保存到文件

```bash
python3 scripts/run.py fetch "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" --save /tmp/article.md
```

### 4）附带图片列表

```bash
python3 scripts/run.py fetch "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" --format json --include-images
```

## Python 脚本直接调用

```bash
python3 scripts/fetch_wechat_article.py \
  "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" \
  --format markdown
```

## 输出说明

### Markdown

默认输出：

- 标题
- 作者 / 发布时间（若能识别）
- 正文清洗结果

### JSON

输出字段：

- `url`
- `title`
- `author`
- `published_at`
- `content_markdown`
- `images`（可选）
- `source`（固定为 `camofox_snapshot`）

## 提取策略

1. 先检查本机 `camofox-browser` 是否健康
2. 若未安装，则自动 clone `camofox-browser` 仓库并执行 `npm install`
3. 若服务未运行，则自动拉起本地服务
4. 新建隔离 tab 打开目标公众号链接
5. 读取 snapshot（必要时翻页 offset）
6. 解析标题 / 作者 / 时间 / 正文
7. 过滤公众号常见噪音：
   - 视频控件
   - 点赞 / 留言 / 关注 / 分享区
   - 扫码提示
   - 页脚互动区
   - 小程序 / 二维码 / 继续访问等提示
8. 关闭临时 tab

## 已知边界

- 这是“公众号正文提取器”，不是通用网页抽取器
- 个别文章若页面结构特殊，清洗规则可能需要补充
- 当前已支持把正文图片按页面 snapshot 顺序插回正文，并在发布飞书文档时渲染成原生图片块
- 当前也已修复一批常见的块级恢复问题：嵌套 listitem 的多余圆点、list item 内联 code 被拆行、blockquote 段落丢失、以及列表和后续正文之间的错误折行
- 解析 snapshot 时，遇到 `- list:` / `- listitem:` / `- paragraph:` / `- blockquote:` 这类容器节点，应该按子树聚合成同一个块；不要把子节点里的 `- text:`、`- code:`、`- strong:` 当成独立段落逐行吐出，否则很容易产生假圆点、额外折行和断裂的 inline code
- 序列化 Markdown 时，列表块结束后如果下一块不是列表，必须主动补空行；否则飞书/Markdown 渲染会把后续正文错误吞进上一个 list item
- 但“逐块原样恢复”仍是近似重建，不保证与手机端公众号富文本 100% 像素级一致；复杂卡片、特殊组件、极细碎图文混排仍可能需要继续补规则
- 自动安装模式仍依赖本机已有 `git` 与 `Node.js 18+ / npm`；如果这些底层依赖缺失，脚本会停止并给出明确提示
- 当前实测下，若飞书授权缺少 `space:document:delete`，则无法真正删除旧文档；稳妥替代方案是用 `docs +update --mode overwrite` 将旧文档覆盖为“已废弃，请看新版”提示

## 何时优先使用这个 skill

当用户提到：

- 微信公众号文章
- 公众号链接抓取
- mp.weixin.qq.com
- 提取公众号正文
- 微信文章转 Markdown / JSON

## 一句话总结

**这套 skill 用 camofox-browser 解决“稳稳打开页面”的问题，再用公众号专用清洗解决“拿到干净正文”的问题。**
