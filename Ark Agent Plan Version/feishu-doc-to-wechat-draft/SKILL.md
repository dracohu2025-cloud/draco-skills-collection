---
names:
  - feishu-doc-to-wechat-draft
name: feishu-doc-to-wechat-draft
aliases:
  - 飞书文档到微信草稿箱
  - 飞书文档微信草稿箱
  - lark-wechat-draft
description: 从飞书/Feishu 文档直接生成微信公众号草稿内容（支持预览、默认样式、dry-run 发布），基于现有 wechat-draft-publisher 流程的独立封装。
version: 0.1.0
author: Draco
license: MIT
metadata:
  hermes:
    tags: [feishu, lark, wechat, draft, markdown, publisher, preview]
---

# 飞书文档 → 微信草稿箱

这是一个**独立可运行**的 skill 封装：把飞书文档内容抓取为 Markdown，按公众号样式渲染，并支持
- 生成 HTML 预览（`render-preview-feishu-doc-default`）
- dry-run 组装草稿 payload（`publish-feishu-doc-default`）

> 说明：这是在保留旧 `wechat-official-account-draft-publisher` 能力的前提下，新增的“从飞书文档入库”方向，不会覆盖旧版本。

## 目录结构

```text
feishu-doc-to-wechat-draft/
├── scripts/
│   ├── run.py                  # 本地 CLI 入口
│   └── wechat_draft_publisher/ # 独立迁移后的核心逻辑（load/render/pipeline/cli）
├── examples/
│   └── default-publish-style.yaml
├── tests/
│   └── test_integration_example_doc.py
├── requirements.txt
└── .env.example
```

## 安装与依赖

```bash
cd ~/.hermes/skills/productivity/feishu-doc-to-wechat-draft
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

当前渲染链路除 `PyYAML`、`markdown-it-py` 外，还需要 `Pygments`。

原因：代码块现在采用**服务端语法高亮**，而不是只靠简单的纯文本换行包装。这样发布到微信公众号草稿箱后，代码块才能更接近 Doocs 的真实实现效果。

## 基础用法（示例文档）

示例文档：
`https://g1mu6da08l.feishu.cn/docx/H0TZdmw3GoW2JSxGBFacw2jdnV8?from=from_copylink`

### 1) 生成预览 HTML

```bash
python3 scripts/run.py render-preview-feishu-doc-default \
  --doc "https://g1mu6da08l.feishu.cn/docx/H0TZdmw3GoW2JSxGBFacw2jdnV8?from=from_copylink" \
  --output /tmp/example-feishu-to-wechat-preview.html
```

### 2) 预览校验成功后，生成草稿 payload（dry-run）

```bash
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://g1mu6da08l.feishu.cn/docx/H0TZdmw3GoW2JSxGBFacw2jdnV8?from=from_copylink" \
  --thumb-media-id DRY_RUN_MEDIA_ID \
  --dry-run
```

返回 JSON 中会包含 `payload`，可直接用于确认是否满足微信要求（标题、摘要、封面 ID、正文 HTML）。

### 新增经验：dry-run 也必须传 `--thumb-media-id`

这次真实联调再次确认：

- `publish-feishu-doc-default --dry-run`
- **并不会**自动跳过封面校验

如果不传：
- `--thumb-media-id`

会直接报：

```text
ValueError: thumb_media_id is required in dry-run mode
```

所以 dry-run 的最小正确写法应固定为：

```bash
python3 scripts/run.py publish-feishu-doc-default \
  --doc "<飞书文档URL>" \
  --author "DracoVibeCoding" \
  --thumb-media-id DRY_RUN_MEDIA_ID \
  --dry-run
```

也就是说：
- **dry-run 用假的 `thumb_media_id` 占位即可**
- 但参数本身不能省

### 新增排障经验：公众号正文默认全左对齐

用户明确要求公众号草稿内容默认全左对齐。当前 doocs/grace 发布链路应满足：
- `justify=false`
- 正文不出现 `text-align: justify`
- 正文不出现 `text-align: center`
- 段落、标题、图注、分割线都显式或继承左对齐

注意：此前当前文档并不是两端对齐；`doocs` 默认 `justify=false`。真正容易造成“看起来没左齐”的残留是标题默认样式里的 `display: table; margin: ... auto` 和图注/星号分割线的居中样式。

### 新增排障经验：飞书有序列表常导出成全 `1.`

飞书/Lark 文档导出的 Markdown 可能把每个有序列表项都写成 `1.`；如果列表项中间夹了截图、引用块，Markdown 渲染会把它们拆成多个单项列表，推到微信公众号后台后序号看起来全是 `1.`。

当前链路已做两层修复：
- `normalize_lark_markdown()` 会把跨图片/引用块的连续步骤重编号，例如 `1,2,3...15`。
- renderer 会保留 Markdown `<ol start="N">` 的起始序号，并把它转成微信更稳的显式 `<span class="md-ordered-index">N.</span>`，避免依赖微信后台的 `<ol>` 默认样式。

验收时固定检查：
- 正文 HTML 中 `md-ordered-index` 不应全是 `1.`。
- `lark-image://` 残留应为 0。

## 真实发布

### 重要排障经验：公众号 access_token 缓存必须按 AppID 隔离

这次真实联调踩到一个很隐蔽的坑：

- 如果 token cache 固定写到同一个文件（例如 `~/.cache/wechat-draft-publisher/access_token.json`）
- 机器上又曾经给别的公众号拿过 token
- 后续发布时就可能误复用“别的 AppID 对应的 token”

表面现象会非常迷惑：
- `draft/add` 看起来返回成功
- 也拿到了一个 `media_id`
- 但当前公众号草稿箱里根本看不到这条草稿
- 再用当前号去 `draft/get` 这个 `media_id`，会得到 `invalid media_id`

稳妥做法：
- token cache 文件必须按 `appid` 分开，例如：
  - `~/.cache/wechat-draft-publisher/access_token_<APPID>.json`
- 当用户反馈“明明返回成功但草稿箱里没有”时，优先检查：
  1. `draft/batchget` 是否真能列出草稿
  2. `draft/get` 是否能读取刚返回的 `media_id`
  3. 本机 token cache 是否串用了别的公众号 token
- 修复后，建议删掉旧的通用 cache 文件，再重新取 token 并重发一次

### 新增排障经验：优先使用 stable_token，必要时 force_refresh

这次继续联调时又踩到一个新的真实坑：

- 即使 `appid/appsecret` 没错
- 传统 `GET /cgi-bin/token` 也能返回 `access_token`
- 但后续调用 `material/add_material`、`draft/add` 等接口时，微信仍可能返回：

```text
40001 invalid credential, access_token is invalid or not latest
could get access_token by getStableAccessToken
```

这类报错在当前公众号环境里，不能只理解成“密钥错了”，更常见的根因是：
- 当前号要求使用 `POST /cgi-bin/stable_token`
- 而且有时 `force_refresh=False` 仍会拿到一个**不是 latest** 的 token
- 于是上传封面图、创建草稿都会失败

稳妥策略：

1. **默认优先改用 stable token 接口**

```http
POST https://api.weixin.qq.com/cgi-bin/stable_token
Content-Type: application/json

{
  "grant_type": "client_credential",
  "appid": "...",
  "secret": "...",
  "force_refresh": true
}
```

2. 如果报错里明确出现：
   - `invalid credential`
   - `not latest`
   - `could get access_token by getStableAccessToken`

   那就不要继续重试旧 token；直接切到：
   - `stable_token`
   - `force_refresh=true`

3. 对于“上传封面 → 发草稿”的一次性发布链路，宁可每次正式发布时都重新取一次最新 stable token，也不要过度相信本地缓存。

4. 修完后立即做最小验证：
   - 先验证 `get_access_token()` 是否成功
   - 再验证 `upload_cover_image(...)` 是否成功
   - 最后再发整篇文章

### 建议更新实现

如果现有代码仍是：
- 优先读本地 cache
- 然后请求 `GET /cgi-bin/token`

则建议改成：
- 直接 `POST /cgi-bin/stable_token`
- 在正式发布路径中优先 `force_refresh=true`
- 成功后再写回按 AppID 隔离的 cache

这样能显著减少“本地看着拿到 token 了，但微信后续接口仍判你不是 latest”的问题。

### 新增经验：本地 Markdown 直发 `publish-default` 时，frontmatter 不是可选项

这次继续联调又踩到一个很容易忽略的坑：

- 用 `publish-default --input /path/to/article.md` 直接发布本地 Markdown 时
- 即使正文第一行已经是 `# 从飞书文档一键发布到微信公众号`
- 如果文件没有 YAML frontmatter，发布仍会失败，报：

```text
ValueError: title is required
```

根因是当前 `load_article(...)` 的取值规则是：
- `title` / `author` / `digest` / `cover_image` / `source_url`
- **只从 frontmatter 里读取**
- 不会从正文里的 `# 一级标题` 自动回填 `title`

也就是说，下面这种文件**不能**直接用于 `publish-default`：

```md
# 文章标题

正文……
```

稳妥做法是至少补上：

```yaml
---
title: 文章标题
author: DracoVibeCoding
---
```

然后再接正文 Markdown。

如果只是临时重发一篇本地稿，可以先在 `/tmp` 里生成一个带 frontmatter 的发布副本，再执行：

```bash
python3 scripts/run.py publish-default \
  --input /tmp/article_publishable.md \
  --thumb-media-id "已有封面素材ID"
```

### 新增经验：用户说“草稿箱没看到”时，不要只信 `media_id`

这次排查也再次证明：

- 即使 CLI 已返回 `draft_media_id`
- 也不应该只凭这个就断定“已经进草稿箱了”

更稳的收尾动作应是：

1. 记录返回的 `draft_media_id`
2. 立刻用当前公众号的最新 `access_token` 调 `draft/batchget`
3. 确认列表里确实能看到：
   - 对应 `media_id`
   - 对应 `title`
   - 合理的 `update_time`

也就是把“微信接口说成功”升级成“当前公众号后台可列出这条草稿”。

尤其当用户明确反馈“后台没看到新推送”时，优先排查：
- 是否其实发的是另一篇文档
- 是否复用了旧 `thumb_media_id`
- 是否命令只做了 dry-run
- 是否成功返回了 `media_id`，但当前号的 `draft/batchget` 根本列不出来

需要正式发布到微信草稿箱时，请在环境变量中提供：

### 新增经验：没有现成 `thumb_media_id` 时，先本地做一个临时封面再发

这次把新的飞书文档直推公众号草稿箱时，真实踩到的第一道坎仍然是：

```text
ValueError: cover_image or thumb_media_id is required for publish
```

也就是说：
- `publish-feishu-doc-default` 真发草稿时
- **必须提供其一**：
  - `--thumb-media-id`
  - `--cover-image`

如果手头没有现成封面素材，最省事的办法是：

1. 先跑一次预览，确认标题：

```bash
python3 scripts/run.py render-preview-feishu-doc-default \
  --doc "<飞书文档URL>" \
  --author "DracoVibeCoding" \
  --output /tmp/feishu_wechat_preview.html
```

2. 用本机 `ffmpeg` 直接生成一张临时封面 PNG

这台机器上没有 `PIL`，但有 `ffmpeg`，下面这类命令可直接出图：

```bash
ffmpeg -y \
  -f lavfi -i color=c='#FA5151':s=900x383:d=1 \
  -vf "drawbox=x=28:y=28:w=844:h=327:color=white@0.10:t=fill,\
       drawtext=fontfile=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc:text='文章标题':fontcolor=white:fontsize=46:x=(w-text_w)/2:y=130,\
       drawtext=fontfile=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc:text='DracoVibeCoding':fontcolor=white@0.92:fontsize=24:x=(w-text_w)/2:y=220" \
  -frames:v 1 /tmp/wechat_cover.png
```

3. 再真实发布：

```bash
python3 scripts/run.py publish-feishu-doc-default \
  --doc "<飞书文档URL>" \
  --author "DracoVibeCoding" \
  --cover-image /tmp/wechat_cover.png
```

适用场景：
- 你只是想快速把飞书文档推进草稿箱
- 还没有设计好的正式封面
- 本机没装 Pillow，但有 `ffmpeg`

### 新增经验：发布后别只信返回值，要立刻 `draft/get` 回查

这次成功发布后，又额外做了一步验证：

1. 用 `stable_token` 重新取最新 token
2. 调微信：
   - `cgi-bin/draft/get`
3. 用返回结果核对：
   - `title`
   - `author`
   - `thumb_media_id`
   - `media_id`

这样才能确认：
- 草稿是真的进了当前公众号草稿箱
- 不是只拿到一个“看起来成功”的返回值

这次真实联调又踩到一个非常容易误判的问题：

- 终端里曾经保留过旧的 `draft_media_id`
- 或者误把“上一条文章的发布结果”当成“当前这条文章已经重新发布”
- 如果这时只看控制台打印，特别容易误以为“新版已经推送到草稿箱”

更稳的做法是：**每次说“已经发到草稿箱”之前，都立即用微信 `draft/batchget` 回查一次**，确认当前公众号后台真的能列出目标标题。

推荐最小验证链路：

1. 记录本次发布返回的 `draft_media_id`
2. 重新取一次最新 `stable_token`
3. 调用：

```http
POST https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=ACCESS_TOKEN
Content-Type: application/json

{
  "offset": 0,
  "count": 10,
  "no_content": 1
}
```

4. 在返回的 `item[].content.news_item[]` 里同时核对：
   - `title`
   - `author`
   - `thumb_media_id`
   - `media_id`

如果用户反馈“草稿箱里没看到新稿”，优先不要争论；直接重新做这一步回查。

### 新增排障经验：用 `publish-default` 发布本地 Markdown 时，缺 frontmatter 会直接报 `title is required`

这次还有一个非常具体、很容易再次遇到的坑：

- 本地临时文章文件如果只是纯 Markdown 正文
- 没有 YAML frontmatter
- 而又直接走 `publish-default --input article.md`

那么 `load_article()` 读不到：
- `title`
- `author`
- `digest`
- `cover_image`

此时发布链路会在校验阶段直接报：

```text
ValueError: title is required
```

稳妥做法：

1. 对本地 Markdown 发布稿，至少补最小 frontmatter：

```yaml
---
title: 从飞书文档一键发布到微信公众号
author: DracoVibeCoding
---
```

2. 然后再执行：

```bash
python3 scripts/run.py publish-default \
  --input /tmp/article_publishable.md \
  --thumb-media-id YOUR_THUMB_MEDIA_ID
```

3. 如果只是想快速重发一篇“当前会话里已经整理好的临时 Markdown”，最稳的做法是：
   - 从旧发布结果中提取可复用的 `thumb_media_id`
   - 先给临时 Markdown 补 frontmatter
   - 再真实发布
   - 最后立刻 `draft/batchget` 回查

需要正式发布到微信草稿箱时，请在环境变量中提供：

如果用户反馈“公众号草稿箱里的 code block 看起来不对”，优先检查下面两件事，而不是先盲目改 CSS：

1. **有没有对 `<code>` 内容做二次 HTML 转义**
   - Markdown 渲染器通常已经把代码内容 escape 过一轮。
   - 如果后处理又把 `&` / `<` / `>` 再整体替换一遍，就会把 `&quot;` 变成 `&amp;quot;`。
   - 这会直接导致公众号里的引号、尖括号和特殊字符显示异常。

2. **有没有真正做服务端语法高亮**
   - 如果只是把代码按行切开，再包成若干 `<span style="display:block">...`，外壳看起来像代码块，但底层并不接近 Doocs。
   - 更稳妥的做法是：
     - 先从 `<code>` 里取出已 escape 的内容
     - 反解回 raw code
     - 用服务端高亮器（当前实现用 `Pygments`）生成带 inline style 的 token HTML
     - 再按 Doocs 的思路保留空格和换行
   - 非行号模式：保留换行、空格；行号模式：按行高亮并生成独立行号列，同时裁掉代码块末尾的单个空行，避免多出一个尾部空白行号。

实践上，这类问题的根因通常是**渲染链路错误**，不是单纯“主题颜色不一致”。

### 新增经验：公众号里的 code block 横向滚动，滚动容器必须优先放在 `<pre>`

这次真实发布后又踩到一个非常关键的兼容性坑：

- 在桌面浏览器里，把 code block 的横向滚动从外层 `<pre>` 挪到内部 `<code>`，表面上仍然可能看起来“能滚”
- 但在**微信公众号文章 WebView**里，这样的结构很容易失效
- 结果就是：
  - 长命令 / 长 YAML / 长 Python 行被右侧裁切
  - 用户无法左右滑动查看完整代码

### 触发问题的坏结构

不要把外层改成：

```html
<pre style="overflow: hidden; ...">
  ...
  <code style="overflow-x: auto; white-space: pre; min-width: max-content; ...">
```

这个结构在普通浏览器里可能还能工作，但在微信文章环境里不够稳。

### 更稳的公众号结构

应优先保持：

```html
<pre style="overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; ...">
  ...
  <code style="white-space: pre; min-width: max-content; ...">
```

也就是：
- **`<pre>` 负责横向滚动**
- `<code>` 只负责承载内容与内边距，不要再承担主要滚动职责

### 和 Mac code block 共存时的建议

如果你还要保留 Doocs-like 的 Mac 顶部样式（红黄绿 dots / 顶部 header 感）：

1. 可以继续把顶部 dots 作为 `pre` 内部的独立块放在前面
2. 但**不要**因此把 `pre` 改成 `overflow: hidden`
3. 更不要把“真正的横滑职责”完全交给内部 `code`
4. 推荐保留：
   - `overflow-x: auto; overflow-y: hidden;`
   - `-webkit-overflow-scrolling: touch;`
5. 同时让 `code` 保留：
   - `white-space: pre`
   - `min-width: max-content`
   - `word-break: normal`
   - `overflow-wrap: normal`

### 建议新增的回归测试

至少补一条针对公众号横滑的测试：

- Mac code block 开启时：
  - 断言 `<pre>` 上仍有 `overflow-x: auto`
  - 断言存在 `-webkit-overflow-scrolling: touch`
  - 断言不再出现 `overflow: hidden` 这种会吞掉横滑的结构

一句话记忆：**在微信公众号里，code block 的横向滚动容器应优先是 `<pre>`，不是内部 `<code>`。视觉细节可以继续优化，但不要为 Mac 顶部样式牺牲 `pre` 的横滑能力。**

需要正式发布到微信草稿箱时，请在环境变量中提供：

```bash
export WECHAT_APP_ID="<AppID>"
export WECHAT_APP_SECRET="<AppSecret>"
```

再执行：

```bash
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://g1mu6da08l.feishu.cn/docx/H0TZdmw3GoW2JSxGBFacw2jdnV8?from=from_copylink"
```

## 运行测试（使用示例文档）

```bash
source .venv/bin/activate
pytest -q tests/test_integration_example_doc.py
```

成功后可复用示例输出，确认新 skill 封装链路可用。

## 新增经验：运行时 skill 副本可能落后于 standalone 项目，导致已修复的渲染 bug 回归

这次真实联调又踩到一个很蠢、但非常容易再次出现的坑：

- 对外真正用于执行发布命令的入口，可能在：
  - `~/.hermes/skills/productivity/feishu-doc-to-wechat-draft/scripts/run.py`
- 但你持续迭代、测试、修 bug 的 canonical 项目代码，可能在：
  - `/home/ubuntu/projects/draco-skills-collection/feishu-doc-to-wechat-draft/`

如果两边代码漂移，就会出现非常迷惑的现象：
- standalone 项目里 code block bug 已经修好
- tests 也都通过
- 但真正发布到微信公众号草稿箱时，又跑回旧版 renderer
- 结果就是典型 regression：
  - code block 样式丢失
  - 代码被压成一行
  - 横向滚动/换行行为退回旧逻辑

### 这次的真实根因

运行时副本里仍是旧逻辑，例如：
- `display: -webkit-box`
- `white-space: nowrap`
- 没有后来的 `white-space: pre + min-width: max-content + pre 负责横向滚动`
- 没有服务端高亮与 `<br/>` 保留换行的修复

而 standalone 项目里已经是修复后的版本。

### 稳妥做法

不要只靠“记得同步文件”。更稳的是：

1. 把运行时 wrapper 改成**优先导入 canonical standalone 项目**
2. 只有当 standalone 项目不存在时，才 fallback 到 skill 副本自身

例如 `scripts/run.py` 应优先类似这样做：

```python
ROOT = Path(__file__).resolve().parent
CANONICAL_ROOT = Path("/home/ubuntu/projects/draco-skills-collection/feishu-doc-to-wechat-draft/scripts")
IMPORT_ROOT = CANONICAL_ROOT if CANONICAL_ROOT.exists() else ROOT
sys.path.insert(0, str(IMPORT_ROOT))
```

### 发布前必须做的核验

当用户反馈“这个 bug 明明修过，为什么又回来了”时，优先不要先怀疑微信；先查：

1. 当前发布命令到底调用的是哪一个 `run.py`
2. 实际 import 到的 `renderer.py` 路径是哪一个
3. 发布产出的 HTML 里是否还残留旧特征，例如：
   - `white-space: nowrap`
   - `display: -webkit-box`
4. 修复版 HTML 里是否已经具备新特征，例如：
   - `white-space: pre`
   - `min-width: max-content`
   - `overflow-x: auto; overflow-y: hidden`
   - `-webkit-overflow-scrolling: touch`

一句话记忆：**如果 skill 既有运行时副本，又有 standalone canonical 项目，就不要让运行入口默认吃本地副本；否则回归只是时间问题。**

## 新增经验：standalone 项目与运行时 skill 副本可能漂移，发布前必须核对真正执行的那份代码

这次真实回归排查踩到了一个很隐蔽但很致命的坑：

- 本机同时存在两份 `feishu-doc-to-wechat-draft`：
  1. **运行时 skill 副本**：
     - `~/.hermes/skills/productivity/feishu-doc-to-wechat-draft/`
  2. **standalone 项目副本**：
     - `/home/ubuntu/projects/draco-skills-collection/feishu-doc-to-wechat-draft/`
- 之前修好的 code block 渲染修复其实已经在 standalone 项目里
- 但真正发布微信公众号草稿时，调用的是 `~/.hermes/skills/.../scripts/run.py`
- 结果运行时副本里的 `renderer.py` 仍然是旧版，于是把 **white-space: nowrap / display: -webkit-box** 这些老逻辑又带回去了，导致：
  - code block 样式回退
  - 所有代码挤成一行
  - 用户以为“之前修好的 bug 又 regression 了”

### 这类问题的本质

不是微信随机抽风，也不是测试全白费。

是因为：
- **测试跑的是 A 副本**
- **真正发布跑的是 B 副本**
- A 和 B 已经漂移

这类问题一旦出现，单看 HTML/CSS 症状会很像“神秘回归”，但真正根因是 **执行入口与源码来源不一致**。

### 发布前必须做的核对

如果这台机器上同时存在：
- Hermes 运行时 skill 副本
- 一个可公开/可测试的 standalone 项目副本

那么在重新发布公众号草稿箱前，必须先确认以下三件事：

1. **当前命令到底执行哪一份**

例如本技能实际发布命令是：

```bash
python3 ~/.hermes/skills/productivity/feishu-doc-to-wechat-draft/scripts/run.py ...
```

那就说明真正生效的是：
- `~/.hermes/skills/productivity/feishu-doc-to-wechat-draft/scripts/wechat_draft_publisher/*.py`

而不是 `/home/ubuntu/projects/...` 那份。

2. **对关键文件做 diff，而不是凭印象说“之前修过”**

对于这次 code block 回归，至少应对拍：

```bash
diff -u \
  ~/.hermes/skills/productivity/feishu-doc-to-wechat-draft/scripts/wechat_draft_publisher/renderer.py \
  /home/ubuntu/projects/draco-skills-collection/feishu-doc-to-wechat-draft/scripts/wechat_draft_publisher/renderer.py
```

重点看是否还残留这些旧逻辑：
- `display: -webkit-box`
- `white-space: nowrap`
- 缺少 `min-width: max-content`
- 缺少 `overflow-x: auto; overflow-y: hidden`
- 缺少 `-webkit-overflow-scrolling: touch`

3. **修完后要重新验证“运行时副本产出的 HTML”**

不要只测 standalone 项目。

应直接用运行时 skill 重新生成 preview / payload，并检查是否满足：

- **不存在**：
  - `white-space: nowrap`
  - `display: -webkit-box`
- **存在**：
  - `white-space: pre`
  - `min-width: max-content`
  - `overflow-x: auto; overflow-y: hidden`
  - `-webkit-overflow-scrolling: touch`

### 对本技能尤其重要的回归信号

如果用户反馈：
- code block 又像没样式
- 所有 code 挤在一行
- 明明之前修过，怎么又坏了

优先不要先怪微信。

先检查：
1. 当前发布到底跑的是哪份 skill
2. `renderer.py` 是否还是旧副本
3. 运行时 preview HTML 里是否又出现 `white-space: nowrap`

### 建议的稳妥流程

以后凡是这类“standalone + 运行时副本共存”的技能，公众号真实发布前建议固定做：

1. 跑测试（standalone 项目）
2. 对关键文件做 diff（standalone vs runtime skill）
3. 必要时把修复同步到 `~/.hermes/skills/...`
4. 用 **运行时 skill** 重新生成 preview HTML
5. 再真实发布
6. 最后用 `draft/get` 回查最终草稿里的 HTML 关键片段

一句话记忆：**在这台机器上，发布是否成功，不只取决于你“修过哪份代码”，更取决于“命令实际执行的是哪份代码”。**

## 新增经验：飞书“分行编号说明块”的保真转换

飞书文档里经常出现一种视觉上很像有序列表、但抓回来的 Markdown 实际还只是普通段落的结构，例如：

```md
简单说，它解决三个核心问题：
**1. 图片自动处理**
说明正文……
**2. 格式完整保留**
说明正文……
**3. 排版风格统一**
说明正文……
```

如果直接交给 Markdown 渲染器，或者只做“标题+正文硬拼成同一行”的粗暴重写，都会出问题。常见症状包括：
- 折行节奏丢失
- `1 / 2 / 3` 不再保留原本的段落层次
- “标题”和“说明正文”被压成一行，公众号里看起来非常拥挤
- 回滚或重构后容易出现 regression：非 code 部分恢复了，但编号说明块的折行又丢了

更稳的做法，是在 `normalize_lark_markdown(...)` 阶段先做结构正规化：

1. 识别独占一行的 `**1. 标题**`
2. 把其后一段正文吸附到该条目上
3. 连续多项时，重写成真正的 markdown ordered list
4. **不要**把正文直接拼回标题同一行；应保留为 list item 内的独立段落

也就是优先转成：

```md
1. **图片自动处理**

   说明正文……

2. **格式完整保留**

   说明正文……

3. **排版风格统一**

   说明正文……
```

而不是：

```md
1. **图片自动处理** 说明正文……
2. **格式完整保留** 说明正文……
3. **排版风格统一** 说明正文……
```

这样 MarkdownIt 会自然产出“一个 `<li>` 内含多个 `<p>`”的结构，后续 HTML 渲染才能既保留有序列表语义，又保留段落边界。

### 额外坑：renderer 也可能把段落再次压扁

即使 normalize 已经产出了正确的多段 list item，渲染层仍然可能把它破坏掉。

这次真实踩到的坑是：
- `_rewrite_ordered_lists()` 如果把整个 `<li>...</li>` 内容塞回一个 inline `<span class="md-ordered-text">...</span>`
- 那么 list item 内原本独立的多个 `<p>` 会被再次 inline 化
- 最终又回到“折行丢失”的错误效果

稳妥做法：
- ordered list 的重写容器应使用 block-level 容器（如 `<section class="md-ordered-text">...</section>`）
- 编号和正文可以做左右布局，但正文容器必须允许内部保留块级段落
- 不要假设 `item.strip()` 后塞进一个 `<span>` 就是安全的

### 建议补的回归测试

至少补两类测试：

1. `normalize_lark_markdown(...)` 回归测试
   - 输入：`**1. 标题**` + 下一行正文 + `**2. 标题**` + 下一行正文
   - 断言：normalize 后出现
     - `1. **标题**\n\n   正文`
   - 断言：不再保留旧的“标题一行、正文紧跟下一行但未入列表”的松散结构

2. renderer 回归测试
   - 输入：包含“多段 list item”的 markdown ordered list
   - 断言：输出中 ordered item 的正文容器是 block-level，而不是单个 inline span
   - 断言：HTML 中仍能看到 list item 内部的多个段落节点

这次实际补上的测试方向包括：
- `tests/test_lark_markdown_normalization.py`
- `tests/test_ordered_list_start_and_code_theme.py`

### 新增经验：编号项内部的列表和补充说明，也必须保留在同一个 ordered item 里

这次继续联调又发现一个很容易遗漏的结构坑：

飞书原始 Markdown 里像下面这种内容：

```md
**2. 微信公众号凭证**
登录微信公众平台，在「开发」-「基本配置」里获取：
- AppID
- AppSecret（只显示一次，记得保存）
同时把你的服务器 IP 添加到「IP 白名单」，否则调用接口会报错。
```

如果 normalize 只把 `**2. 微信公众号凭证**` 变成 ordered item 标题，却没有把：
- 说明段落
- bullet 列表
- 列表后的补充说明

一起缩进并吸附进同一个 list item，就会在公众号里出现：
- 编号单独一行
- bullet 列表像掉出该编号项
- 后续补充说明再次断层
- 视觉上像多出错误编号或额外折行

更稳的正规化目标应是：

```md
2. **微信公众号凭证**

   登录微信公众平台，在「开发」-「基本配置」里获取：
   - AppID
   - AppSecret（只显示一次，记得保存）

   同时把你的服务器 IP 添加到「IP 白名单」，否则调用接口会报错。
```

### 对 `strong-numbered block` 的更稳处理规则

在 `_convert_strong_numbered_blocks(...)` 里，建议采用下面的策略：

1. 识别 `**2. 标题**` 这类独占一行的强编号标题
2. 重写成：
   - `2. **标题**`
3. 然后继续吸收其后续 block，直到遇到以下任一边界：
   - 下一个 `**3. 标题**` 这类强编号标题
   - 独占一行的普通 strong 小标题（例如 `**方法一：...**`）
   - 新的 section 边界（如 `#` / `##` / `<hr>`）
4. 吸收 block 时，**保留原 block 结构**，不要只拼接纯文本：
   - 普通段落继续保留为段落
   - `- ...` 保留为 item 内部 bullet list
   - 代码块继续保留为 item 内部 code block
   - 列表后的补充说明继续保留为 item 内的独立段落

这意味着：
- 对 `2. 微信公众号凭证`，后面的说明 + bullets + IP 白名单说明，都应继续属于同一个 ordered item
- 但对 `3. 封面图的 media_id`，遇到 `**方法一：...**` 时必须停止吸收，让方法标题和后续步骤重新成为 item 外的独立块

### 建议新增/更新的回归测试

除了“标题 + 下一行正文”的测试，还应覆盖：

1. **编号项内部 bullets 不掉出 item**
   - 输入：`**2. 微信公众号凭证**` + 段落 + bullet 列表 + 补充说明
   - 断言：normalize 后 bullets 和补充说明仍缩进在同一个 `2.` item 内

2. **编号项遇到独立 strong 小标题时及时断开**
   - 输入：`**3. 封面图的 media_id**` 后面跟 `**方法一：...**`
   - 断言：`方法一` 不会被吞进 `3.` item 的正文段里

3. **最终 HTML 中 2/3 两个编号项连续且不重复错号**
   - 断言：`2. 微信公众号凭证` 与 `3. 封面图的 media_id` 都在同一 ordered list 体系内
   - 断言：`2.` 项内部包含 bullets 与补充说明
   - 断言：`3.` 项之后的方法标题和方法步骤是编号项外的独立块

### 一句话经验

飞书抓回来的文本“看起来有结构”，不代表 Markdown 语义已经完整；而且就算 normalize 修对了，renderer 也可能把结构再次压扁。发布到公众号前，必须同时检查：**语义结构有没有补对，渲染后处理有没有把它破坏掉。对于编号项，既要避免把后续内容吞过头，也要避免只收标题不收其内部 bullets / 补充说明。**

## 新增经验：嵌套无序列表不能再用正则硬拆 `<ul><li>`

这次真实发布又踩到一个 renderer 层面的坑：

- 飞书文档里明明是有层级的无序列表，例如：
  - `- Hermes：`
    - `- 模型：...`
    - `- 宿主：...`
- 但发布到公众号后，子列表被压坏成：
  - 外层 bullet 里直接夹着残缺的 `<ul>` / `<li>`
  - HTML 结构错位
  - 视觉上就变成“父级 bullet 和子级 bullet 混成一坨”

根因不是 normalize，而是 renderer 旧逻辑对无序列表做了这种事：
- 用正则匹配整个 `<ul ...>(...)</ul>`
- 再用正则找内部 `<li ...>(...)</li>`
- 这种写法对**嵌套列表**天然不可靠，因为正则不懂树结构，遇到子级 `<ul>` 时会在第一个 `</li>` / `</ul>` 处把层级拆坏

稳妥做法：
- 对无序列表改成**树形解析**，不要再用正则硬拆 HTML
- 例如先把片段包成 root，再用 XML/HTML 树遍历
- 只对 `ul.md-ul` 做递归重写
- 每个 bullet item 用 block 容器承载正文和子列表，别再用只适合单段文本的 `<p>` 包整个 item

这次实际修复采用的是：
- `xml.etree.ElementTree` 解析当前 HTML 片段
- 递归重写 `ul.md-ul`
- `md-bullet-item` 改成 block 级 `<section>`
- `md-bullet-text` 允许继续包住下一层 `md-list md-list-unordered`

建议补的回归测试至少包括：
1. 输入一段二级无序列表 markdown
2. 断言输出里：
   - 至少出现两层 `md-list md-list-unordered`
   - 不再残留原始 `<ul class="md-ul">`
   - 不再残留原始 `<li class="md-li">`
   - 父级文本和子级列表都同时保留

一句话记忆：**无序列表一旦有嵌套，就必须按树处理；用正则拆 `<ul>/<li>` 迟早会炸。**