# Draco Skills Collection

这是一个面向公开使用的技能 / 小工具集合仓库，主要收录围绕内容生产、飞书协作、微信公众号发布，以及多媒体自动化的可复用项目。

这里的每个目录，尽量都朝着“下载后就能独立运行”的方向整理，而不是只保留一层内部包装。

## 目前收录了什么

- [`wechat-article-camofox/`](./wechat-article-camofox/)：稳定抓取微信公众号文章，自动安装 CamouFox 依赖，输出 Markdown / JSON / 飞书文档
- [`article-to-wechat-cover/`](./article-to-wechat-cover/)：从飞书文档或 Markdown 自动生成微信公众号封面图
- [`feishu-doc-to-wechat-draft/`](./feishu-doc-to-wechat-draft/)：把飞书文档一键转成微信公众号草稿
- [`epub2podcast/`](./epub2podcast/)：把 EPUB 电子书变成双人中文播客与最终视频

---

## 1. wechat-article-camofox

把一篇微信公众号文章链接，自动抓成更干净的 Markdown、JSON，或者直接发布为飞书原生文档。

### 它解决什么问题

普通网页抓取经常会把公众号页面的这些内容一起带下来：

- 留言区
- 关注区
- 扫码提示
- 弹层按钮
- 点赞 / 分享 / 推荐区
- 图片位置错乱、列表断裂、额外折行

这个工具会先自动准备 `camofox-browser`，再读取结构化 snapshot 和图片信息，最后做公众号专用清洗，所以结果更适合直接继续编辑或归档。

### 效果预览

<img src="./wechat-article-camofox/assets/wechat-article-camofox-flow.svg" alt="wechat-article-camofox 工作流预览" />

### 快速开始

```bash
cd wechat-article-camofox

# 抓成 Markdown
python3 scripts/run.py fetch "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"

# 抓成 JSON
python3 scripts/run.py fetch "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx" --format json

# 直接发布到飞书原生文档
python3 scripts/run.py publish-feishu "https://mp.weixin.qq.com/s/xxxxxxxxxxxxxxxx"
```

更多详情查看：

- [`wechat-article-camofox/README.md`](./wechat-article-camofox/README.md)

---

## 2. article-to-wechat-cover

把一篇飞书文档或本地 Markdown 文章，自动生成成适合微信公众号使用的横幅封面图。

### 亮点

- 固定输出 `2.35:1` 的公众号封面比例
- 先理解文章主题与语气，再生成封面图
- 复用 OpenRouter + Nano Banana / Gemini Flash Image 出图
- 可选上传飞书云盘，或直接上传为微信封面素材拿到 `thumb_media_id`

### 效果预览

<img src="./article-to-wechat-cover/assets/example-wechat-cover.jpg" alt="article-to-wechat-cover 示例封面图" />

### 快速开始

```bash
cd article-to-wechat-cover
python3 scripts/run.py from-feishu-doc \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --output ./wechat-cover.jpg
```

更多详情查看：

- [`article-to-wechat-cover/README.md`](./article-to-wechat-cover/README.md)

---

## 3. feishu-doc-to-wechat-draft

将飞书（Feishu/Lark）文档一键转换为微信公众号草稿，支持图片自动上传、样式渲染和本地预览。

### 亮点

- 从飞书文档 URL 直接生成微信草稿
- 支持 Doocs 风格渲染
- 自动下载飞书图片并上传到微信素材库
- 发布前可先生成 HTML 预览确认效果

### 快速开始

```bash
cd feishu-doc-to-wechat-draft
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/run.py render-preview-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --output /tmp/preview.html
```

更多详情查看：

- [`feishu-doc-to-wechat-draft/README.md`](./feishu-doc-to-wechat-draft/README.md)

---

## 4. epub2podcast

把电子书 EPUB 转成双人中文播客脚本、分段音频、Smart Slide，以及最终 MP4 视频。

### 适合什么场景

- 想把长文 / 电子书内容变成更易传播的播客视频
- 需要中文双人讲述风格
- 想自动生成封面页、信息图页、分栏页等多种 slide 版式

### 效果预览

<table>
  <tr>
    <td width="50%" valign="top">
      <img src="./epub2podcast/assets/example-slide-cover.png" alt="epub2podcast 示例封面页" />
      <p><strong>封面页风格</strong><br/>适合放在视频开头，用来介绍书名、主题和整体气质。</p>
    </td>
    <td width="50%" valign="top">
      <img src="./epub2podcast/assets/example-slide-infographic.png" alt="epub2podcast 示例信息图页" />
      <p><strong>信息图风格</strong><br/>适合在视频中段解释观点、拆解结构，或者展示一个主题的关键信息。</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <img src="./epub2podcast/assets/example-slide-split-layout.png" alt="epub2podcast 左右分栏版式示例" />
      <p><strong>左右分栏版式</strong><br/>适合做“引言 + 分点展开”的讲述页。</p>
    </td>
    <td width="50%" valign="top">
      <img src="./epub2podcast/assets/example-slide-card-layout.png" alt="epub2podcast 三卡片版式示例" />
      <p><strong>三卡片版式</strong><br/>适合把一个主题拆成多个并列重点。</p>
    </td>
  </tr>
</table>

发布状态：**v0.1.0 early standalone release**

更多详情查看：

- [`epub2podcast/README.md`](./epub2podcast/README.md)

---

## 这个仓库适合怎么用

### 如果你主要做公众号内容

推荐组合：

1. 先用 `wechat-article-camofox` 把公众号文章抓下来
2. 用 `article-to-wechat-cover` 生成封面图
3. 用 `feishu-doc-to-wechat-draft` 发布到公众号草稿箱

### 如果你主要做长内容再加工

推荐看：

- `epub2podcast`

它更适合把书籍、长文、系列内容转成播客视频。

---

## 使用建议

不同目录的依赖并不完全相同，请进入对应目录阅读 README 再执行。

通常会涉及的基础工具包括：

- Python 3
- `git`
- Node.js / `npm`
- `lark-cli`
- 某些项目所需的 API key 或第三方服务配置

---

## 一句话总结

**如果你想把“抓内容、改内容、配封面、发公众号、做播客”这些流程逐步自动化，这个仓库就是一组可以直接拿来用、也可以继续扩展的起点。**
