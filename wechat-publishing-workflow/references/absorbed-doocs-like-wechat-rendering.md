# Archived skill: doocs-like-wechat-rendering

Original path: `productivity/doocs-like-wechat-rendering`

Consolidation reason: Doocs-like rendering is the styling layer of WeChat draft publishing.

---

---
name: doocs-like-wechat-rendering
description: 为 Markdown→微信公众号/微信草稿箱发布工具实现 Doocs-like 可配置渲染层：profile/theme/HR/callout/preview/CLI 一体化。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, markdown, doocs, rendering, cli, preview]
    related_skills: [wechat-official-account-draft-publisher, standalone-skill-package-bootstrap, test-driven-development]
---

# Doocs-like WeChat Rendering

适用场景：
- 你在做 Markdown → 微信公众号 HTML / 草稿箱发布工具
- 用户希望“尽量接近 Doocs 渲染效果”
- 需要把样式能力做成 CLI 可配置参数，而不是写死在 renderer 里

## 推荐实现结构

把“渲染配置”单独抽到一个模块，例如 `rendering.py`：

- `RenderOptions` dataclass
- `resolve_render_options(...)`
- `VALID_PROFILES / VALID_THEMES / VALID_CODE_THEMES / VALID_HR_STYLES`
- `build_css_vars(options)`
- `css_var_style(options)`

这样 renderer / preview / pipeline / CLI 都共用同一套配置源，避免参数散落和不一致。

## 推荐的第一版可配置项

至少支持：
- `profile`: `default | doocs | classic | minimal`
- `theme`: `default | grace | simple`
- `code_theme`: `dark | light | github-dark-dimmed | github-light | one-dark | vitesse-light | vitesse-dark`
- `hr_style`: `dash | star | underscore`
- `heading_style`: `solid | left-bar | underline | minimal`
- `caption_mode`: `title-first | alt-first | title-only | alt-only | hidden`
- `primary_color`（支持命名预设，如 `classic-blue` / `vitality-orange` / `emerald-green` 等）
- `font_family`
- `font_size`
- `line_height`

如果目标是尽量贴近 **Doocs 源码级表现**，不要只把这些参数映射成“看起来差不多”的值；应尽量对齐 Doocs 实际配置源：
- `fontSizeOptions`: 更小=14px，稍小=15px，推荐=16px，稍大=17px，更大=18px
- `colorOptions` 里的真实 hex（例如活力橘是 `#FA5151`，不是近似橙色）
- `fontFamilyOptions` 里的真实字体栈（尤其无衬线）
- `defaultStyleConfig` 的真实默认项：Doocs 默认 `isMacCodeBlock = true`、`isShowLineNumber = false`、`legend = alt`，且 `codeBlockTheme = codeBlockThemeOptions[23]`，实际对应的是 `github`，不是 `github-dark`
- `theme-css/default.css` 与 `theme-css/grace.css` 里的标题倍率（如 grace 下 h2 为 `1.3 * font-size`）
- `defaultStyleConfig.codeBlockTheme` 的真实默认值：Doocs 当前默认并不是 `github-dark`，而是 `codeBlockThemeOptions[23]` 对应的 `github`

经验：字号对齐不能只把 `<p>` 改成 15px；应让文章容器统一持有 `font-family/font-size/line-height`，列表、表格、图注、自定义 bullet block 等尽量走 `inherit`，否则会出现“有的段落 15px、有的块退回 16px”的大小不一问题。- `justify`
- `indent_first_line`
- `mac_code_block`
- `code_line_numbers`
- `footnote_links`

经验：不要只把参数接进 CLI；要把它们完整打通到：
1. `render_markdown`
2. `write_preview_document` / `render_preview_document`
3. `build_draft_from_markdown_file`
4. `publish_markdown_file`

否则 preview 和 publish 的效果会漂移。

## CLI 设计建议

除了原有命令（如 `validate / render-preview / publish`），建议增加：

### `list-styles`
第一阶段至少输出 JSON，列出当前支持的：
- profiles
- themes
- code_themes
- hr_styles
- callouts

如果要继续向 Doocs 面板对齐，推荐升级成 **两层输出**：

1. **基础枚举层**
   - `profiles`
   - `themes`
   - `code_themes`
   - `heading_styles`
   - `color_presets`
   - `caption_modes`
   - `footnote_links`

2. **UI 语义层**
   - `ui.colors[key] = {label, hex}`
   - `ui.heading_styles[key] = {label}`
   - `ui.caption_modes[key] = {label}`
   - `ui.toggles[key] = {label, default}`

3. **完整 UI schema 层**（前端可直接消费）
   - `ui_schema.version`
   - `ui_schema.sections[]`
   - 每个 section 至少包含：
     - `key`
     - `label`
     - `control`（如 `segmented | select | toggle | color-grid`）
     - `bind`
     - `default`
     - `recommended`
     - `options`
     - `aliases`（可选）

4. **配置文件/JSON 兼容层**（建议补上）
   - CLI 支持 `--style-config <json|yaml>`
   - CLI 支持 `--style-json '{...}'`
   - 允许使用 Doocs UI 语义值，而不只接受内部枚举值，例如：
     - `theme_colors: 活力橙`
     - `theme_colors: 活力橘`（可额外兼容常见同义写法，映射到 `vitality-orange`）
     - `font: 无衬线`
     - `font_size: 稍小`
     - `heading_style: 左侧竖线`
     - `heading_style: 默认`
     - `caption_mode: title 优先`
     - `caption_mode: 不显示`
     - `mac_code_block: 开启`
   - 建议支持若干 wrapper key：`style / styles / render / rendering / values`
   - 配置文件里可能会混入 `meta` 之类非样式字段；解析后要过滤，只保留合法 style keys，再传给 `resolve_render_options(...)`，否则会因为意外字段报 `unexpected keyword argument`
   - CLI 显式参数应覆盖 config 文件里的值
   - 建议同时提供一份 `examples/doocs-ui-config.example.json`，用中文 label/开关值做真实示例，并用它实际跑一遍 preview / publish 验证链路

经验：当用户目标不是“命令行参数够用”，而是“做成和 Doocs 类似的配置面板”，`list-styles` 不应只返回字符串数组，而应直接返回可渲染 UI 的 schema。进一步地，如果要把 schema 真正接到 UI 或外部配置文件，还应补上 `--style-config/--style-json` 输入层，并接受中文 label/开关语义。

如果用户已经反复验收并最终确定了一套满意的公众号样式，建议把它落成单独的默认配置文件（如 `default-publish-style.yaml`），后续发布直接复用，避免每次手工重复传参；同时让 CLI 显式参数仍可覆盖默认配置。

经验：如果 `list-styles` / `ui_schema` 面向外部 UI 或验收脚本消费，不要对这些枚举统一用 `sorted(...)`。Doocs 面板的顺序本身带有 UI 语义，至少要固定以下顺序：
- heading level styles：`default → color-only → border-bottom → border-left → custom`
- heading styles：`solid → left-bar → underline → minimal`
- caption modes：`title-first → alt-first → title-only → alt-only → hidden`
- color presets：优先保留 Doocs 源码声明顺序，而不是字母排序

进一步建议把“默认模式”做成真正可发现的 CLI 入口：
- `publish` 默认自动加载默认样式文件
- 额外提供显式命令：`publish-default`、`render-preview-default`
- `list-styles` 返回：
  - `default_publish_style_config`
  - `default_commands`
- 测试覆盖：
  - `publish --dry-run` 默认吃到默认样式
  - `publish-default` 默认吃到默认样式
  - `render-preview-default` 默认吃到默认样式

## Callout 支持做法

如果底层 Markdown 渲染器没有现成支持 GFM/Obsidian callout，可先在 Markdown 渲染前做预处理。

目标支持：
- `> [!NOTE]`
- `> [!TIP]`
- `> [!IMPORTANT]`
- `> [!WARNING]`
- `> [!CAUTION]`
- `> [!INFO]`

### 实用做法
1. 用正则匹配 callout block
2. 把它转换成安全的 HTML 片段，例如：
   - `<section class="md-callout md-callout-tip" data-callout="tip">...`
3. 再交给 Markdown 渲染器
4. 在后处理阶段对这些 class 注入 inline style

### 关键经验
如果你要把预处理后的 HTML 再交给 `markdown-it-py`，需要允许 HTML 透传：
- `MarkdownIt("commonmark", {"html": True, ...})`

否则 callout HTML 会被转义掉。

## HR 样式建议

把 `<hr>` 的最终样式交给统一函数，例如 `_hr_open(hr_style, border, primary)`：
- `dash`: 虚线分割
- `star`: 更装饰性的样式类名（至少输出单独 class，便于 preview 再增强）
- `underscore`: 短实线分隔

经验：先保证 **class 和配置链路** 正确，再逐步增强视觉细节。

## Digest 提取的坑

如果渲染后 `<p>` 标签带了 class/style，原来的摘要正则 `r"<p>(.*?)</p>"` 会失效。

应改为更宽松版本：
- `r"<p(?:\s+[^>]*)?>(.*?)</p>"`

否则摘要可能退化为“从整段 HTML 抽文本”，把标题、引用、代码全混进去，导致回归。

## 预览页建议

preview HTML 不要只塞正文，建议额外提供：
- 手机卡片/文章容器外壳
- profile-specific CSS
- theme-specific CSS
- 对 callout / code / h2 / hr 的二次增强
- 对 `md-pre-mac`、`md-code-line-number`、`md-figure-caption`、`md-link-footnotes` 的额外预览样式

原则：
- 发布到微信的正文尽量用 inline style 保稳定
- preview 页面可额外叠加 CSS，让本地预览更接近最终期望风格
- 但不要只信本地 preview；列表、编号、外链脚注这类结构必须以“真实公众号草稿箱验收”为准

## 测试建议（很重要）

至少补这些测试：
1. renderer 支持 `profile + theme` class
2. renderer 支持 `callout + hr_style`
3. preview 输出包含对应 profile/theme 样式
4. pipeline 输出 payload 时保留渲染 class
5. CLI `render-preview` 接受 profile/theme 参数
6. CLI `list-styles` 输出所有可用 preset
7. digest 仍然从首段正文生成，而不是误取标题

## 推荐工作顺序

1. 先写失败测试：新增 `hr_style`、`list-styles`、callout
2. 让测试真实失败
3. 再补 `RenderOptions` / renderer / preview / pipeline / CLI 链路
4. 跑局部测试
5. 跑全量测试，检查 digest 等旧行为是否回归

## 基于 Doocs 源码对齐时的关键发现

如果目标从“Doocs-like”升级为“尽量按 Doocs 源码语义对齐”，要特别注意下面这些点：

1. **字号选项的真实值**（来自 Doocs 源码 `packages/shared/src/configs/style.ts`）
   - 更小 = `14px`
   - 稍小 = `15px`
   - 推荐 = `16px`
   - 稍大 = `17px`
   - 更大 = `18px`

2. **真正决定观感的不是把 `15` 传进去，而是字号继承体系**
   - Doocs 把 `--md-font-size` 注入容器，再让大量正文元素继承。
   - 如果你像临时实现那样只给 `<p>` 单独写 `font-size: 15px`，而列表、表格、caption、span、blockquote 内文本等没有统一继承，就会出现“有的块像 15px，有的块像 16px”的漂移。
   - 结论：应优先把 `font-family / font-size / line-height` 放到文章容器层，让 `p/li/table/figcaption/blockquote p` 等尽量继承，而不是到处局部硬编码。

3. **Doocs 的 heading 大小是跟随 `--md-font-size` 按比例计算的**
   - `default` 主题大致是：
     - `h1 = 1.2 * font-size`
     - `h2 = 1.2 * font-size`
     - `h3 = 1.1 * font-size`
   - `grace` 主题大致是：
     - `h1 = 1.4 * font-size`
     - `h2 = 1.3 * font-size`
     - `h3 = 1.2 * font-size`
     - `h4 = 1.1 * font-size`
   - `simple` 主题也不是简单复用 default：
     - `h1 = 1.4 * font-size`
     - `h2 = 1.3 * font-size`
     - `h3 = 1.2 * font-size`
     - 同时带有 `border-radius: 8px 24px 8px 24px`（h2）和 `line-height: 2.4em`（h3）等额外细节
   - 如果你自己拍脑袋写 `1.7em / 1.12em / 0.96em` 这类值，最终视觉会和 Doocs 拉开距离。

4. **Doocs 的标题样式是“按级别配置”的，不是单一全局开关**
   - 源码里 `headingStyles` 支持 `h1 ~ h6` 各自单独选择。
   - “各级标题样式=默认” 的真实含义是：每个级别都回退到主题 CSS 本身，而不是只切一个全局 `heading_style`。
   - 如果用户要求和 Doocs 面板一致，应考虑从单个 `heading_style` 升级为 `heading_styles` 映射。
   - 实战补充：为了兼容旧 CLI / 旧 API 的单个 `heading_style` 入口，又尽量贴近 Doocs 面板语义，可以做这样的回退：
     - `heading_styles[level]` 显式存在时，永远以该级别值为准
     - 否则若全局 `heading_style` 为：
       - `left-bar` → 回退成各级 `border-left`
       - `underline` → 回退成各级 `border-bottom`
       - `minimal` → 回退成各级 `color-only`
       - `solid` → 仅让 `h2` 维持 Doocs 默认主题里的“实底标题块”语义，其它级别回各主题默认样式
   - 这样既能兼容旧参数，又不会出现“只有 h2 变了，h1/h3-h6 完全不跟”的割裂体验。
   - CLI / `list-styles` / UI schema 里不要把这些选项按字母排序后直接输出；更接近 Doocs 面板的做法是保留源码语义顺序，例如：
     - heading level styles: `default → color-only → border-bottom → border-left → custom`
     - 兼容旧入口的 heading style: `solid → left-bar → underline → minimal`
     - caption modes: `title-first → alt-first → title-only → alt-only → hidden`
     - color presets 也应按 Doocs `colorOptions` 原始顺序输出，而不是 `sorted(...)`

5. **颜色和字体栈要按 Doocs 原值对齐，不要只做近似**
   - Doocs 中“活力橘”实际值是 `#FA5151`，不是常见近似橙红。
   - 无衬线字体栈在 Doocs 中是：
     `-apple-system-font,BlinkMacSystemFont, Helvetica Neue, PingFang SC, Hiragino Sans GB, Microsoft YaHei UI, Microsoft YaHei, Arial, sans-serif`
   - 如果用户明确要求“按 Doocs 命名和标准”，这些设计 token 应尽量直接对齐源码。

6. **grace / simple / default 都不能只靠少量变量模拟**
   - Doocs 的主题系统是：`base.css + default.css + grace.css/simple.css + heading styles + custom CSS` 逐层叠加。
   - 仅仅用几项颜色/阴影变量模拟 `grace/simple`，只能做到“风格相似”，做不到“源码语义对齐”。
   - 特别是 `default.css` 里还有一批容易漏掉的基础 token：
     - `a { color: #576b95; text-decoration: none; }`
     - `strong { color: var(--md-primary-color); font-size: inherit; }`
     - `code { font-size: 90%; color: #d14; background: rgba(27, 31, 35, 0.05); padding: 3px 5px; border-radius: 4px; }`
     - `hr` 是细实线 + `transform: scale(1, 0.5)`，不是虚线
     - 默认图片是 `margin: 0.1em auto 0.5em; border-radius: 4px`
6. **grace / simple / default 的真实差异包含很多“小而关键”的 CSS 细节**
   - Doocs 的主题系统是：`base.css + default.css + grace.css/simple.css + heading styles + custom CSS` 逐层叠加。
   - 仅仅用几项颜色/阴影变量模拟 `grace`，只能做到“风格相似”，做不到“源码语义对齐”。
   - 进一步对齐时，优先盯这些最影响观感的细节：
     - `default`：
       - code block 默认主题实际更接近 `github`（不是 `github-dark`）
      - `pre.code__pre`：`font-size: 90%`, `margin: 10px 8px`, `border-radius: 8px`, `padding: 0 !important`, `line-height: 1.5`
      - `pre > code`：`display: -webkit-box`, `padding: 0.5em 1em 1em`, `background: none`, `white-space: nowrap`, `margin: 0`
      - 默认主题 code block 边界更接近：`border: none; box-shadow: none`，不要为了“更明显”额外补外边框或阴影
      - 如果叠加 `mac_code_block=true`，推荐由 `pre` 承担窗口顶部留白（如 `padding: 38px 16px 16px`），`code` 本身回退成 `padding: 0`，避免双重 padding 让顶部/左右留白过厚
      - 如果同时开启 `code_line_numbers=true`，处理前要先裁掉代码块末尾单个换行；否则很容易多渲染出一个“尾部空白行号”
      - **不要对 Markdown 渲染器输出的 `<code>` inner HTML 再做一轮整体 HTML escape**。像 `&quot;` 若再次 escape，会变成 `&amp;quot;`，这正是公众号里代码块看起来“字符发脏/不对劲”的常见根因。
      - 如果你的发布链路是纯服务端（没有浏览器端再跑 highlight.js），应在服务端直接完成高亮，并输出带 inline style 的 token HTML；否则只会得到“整块纯文本 + 人工换行”，与 Doocs 的源码级实现差距很大。
      - 纯服务端实现时，可直接参考 Doocs `packages/core/src/utils/languages.ts` 的 `highlightAndFormatCode(...)` 语义：**先从已 escape 的 code 内容反解回 raw code，再做高亮，再按 Doocs 的思路保留空格/换行**（非行号模式下换行→`<br/>`，空格→`&nbsp;`；行号模式按行高亮并生成独立行号列）。
      - Doocs 当前 `code()` 渲染器（`packages/core/src/renderer/renderer-impl.ts`）会输出 `<pre class="hljs code__pre"> + mac-sign SVG + <code class="language-...">...</code>`。若你做纯服务端复刻，可不必 1:1 复刻 class，但最好保留这三个语义层：
        1. 外层 `pre` 承担背景/圆角/横向滚动；
        2. 顶部单独的 Mac sign 区块（更接近 Doocs 的是一个独立 `span/svg`，不是简单绝对定位三个小圆点）；
        3. `code` 只承载高亮后的 token HTML。
      - 更贴近 Doocs 的 Mac code block 内边距层级是：`pre` 本身 `padding: 0`，Mac sign 单独 `padding: 10px 14px 0`，`code` 再承担正文内边距（如上/左右/下留白）。这样公众号里通常比“全部 padding 堆在 pre 上 + dots 绝对定位”更稳，也更接近 Doocs 观感。
      - **不要额外发明“bash/shell 一律深色、python 一律浅色”之类的启发式终端皮肤。** 若目标是贴近 Doocs，代码块背景应优先由 `code_theme` 决定；在常用 `github + mac_code_block=true` 配置下，更接近 Doocs 的是“浅色代码块 + Mac 三色圆点”，而不是再叠一个自定义 terminal 标题栏。
      - 若你对飞书/Lark 导出的 Markdown 做“`**1. 标题** + 下一行正文` → 真正有序列表”这类规范化转换，**必须确保转换失败时完整回退，不要吞掉后面的 fenced code opening fence（如 ```bash）**。一旦 fence 被误吃，后续正文很容易被卷进 code block，形成大面积串位。
      - 排查这类问题时，**不要只看飞书抓回来的原始 `doc.markdown`**；还要检查进入渲染器前的 `article.content_markdown`。很多结构错乱并不发生在抓取阶段，而发生在你自己增加的 normalize / rewrite 规则里。
      - 若你实现了“把原生 `ol/ul` 改写成微信稳定列表 block”的后处理，务必同时做到两件事：
        1. 真的把 `<ol ...>` / `<ul ...>` 在 HTML 后处理链路里接上；
        2. 保留 `<ol start="N">` 的起始编号语义。否则很容易出现有些列表走自定义稳定渲染、有些又漏回原生 HTML，或者 2/3/4 号列表被错误重排回 1 开始。
- inline `code`：`color: #d14`, `background: rgba(27,31,35,0.05)`, `padding: 3px 5px`, `border-radius: 4px`
       - `a`：`color: #576b95; text-decoration: none`（不要额外加 bottom border）
       - `strong`：使用 `var(--md-primary-color)`，不是正文色
       - `hr`：不是虚线，应是细实线 + `transform: scale(1, 0.5)` 的做法
       - `img`：`margin: 0.1em auto 0.5em; border-radius: 4px`
       - `figure`：`margin: 1.5em 8px`; `figcaption`：`color: #888; font-size: 0.8em`
       - `blockquote > p`：应额外收敛到 `display: block; font-size: 1em; color: inherit; margin: 0`
       - `li`：默认主题更接近 `margin: 0.2em 8px`
       - `th/td`：`1px solid #dfdfdf`, `padding: 0.25em 0.5em`, `word-break: keep-all`
     - `grace`：
       - `h3` 有 `border-bottom: 1px dashed var(--md-primary-color)`
       - blockquote italic + inset code shadow + image shadow + table shadow 都是关键识别点
     - `simple`：
       - `h2`：`border-radius: 8px 24px 8px 24px`
       - `h3`：`line-height: 2.4em`，带轻边框与轻背景
       - `h4/h5/h6` 也有 `border-radius: 6px` 这类小差异

## 常见失误

- 只改 renderer，忘了 preview/pipeline/CLI
- callout 预处理后没开启 HTML 透传
- 只用 `commonmark` preset，忘了显式开启 `table` rule，导致 Markdown 表格原样输出成段落文本
- 没处理 `blockquote` / `li` 内部嵌套 `<p>` 的默认外边距，发布到微信后容易出现“多出一行/空一行”的观感
- 仅在本地 preview 看起来正常，但微信公众号正文里原生 `ul/li` 仍可能被渲染成“空 bullet + 正常 bullet 交替”；更稳妥的做法是把无序列表改写成显式 bullet block（如 `<p><span>•</span><span>文本</span></p>`）来绕开微信的列表兼容问题
- 微信公众号里的原生 `ol/li` 也可能出现“空编号 + 正常项交替”；有序列表同样建议改写成显式 numbered block（如 `<p><span>1.</span><span>文本</span></p>`）来保证稳定
- 想做图注格式时，直接依赖普通 Markdown 图片输出不够灵活；更稳妥的做法是先把 `![alt](src "title")` 预处理成 `<figure + figcaption占位>`，再按 `title-first / alt-first / title-only / alt-only / hidden` 在后处理阶段统一决策
- 想做“微信外链转底部引用”时，不要只改 `<a>` 样式；应在后处理阶段收集外链、正文替换为引用标记、文末统一追加 footnotes 区块
- **飞书文档导出的“伪列表/伪分段”很容易骗过 Markdown 解析器。** 典型形态包括：
  - `**1. 标题**` 独占一行，下一行才是正文
  - `**方法一：...**` 后面紧跟多个 `1.` 步骤
  - 列表项结束后，下一行其实是普通说明句，但因为前面少了空行，被 Markdown 吸进上一个 `li`
  处理建议：在进入 Markdown 渲染前，先做一层 **block boundary normalization**，主动补空行、拆分 standalone strong 标题、把需要的伪列表升级成真正列表。
- **给飞书导出的 `**1. 标题**` 做自动列表升级时，要特别小心 fenced code。** 如果标题下一行紧跟的是 `````bash` / `````python` 之类围栏代码块，千万别把 opening fence 吃掉；否则命令正文会掉回普通段落，而后续说明文本反而会被串进 code block。稳妥做法是：若标题后第一段正文为空或被 ` ``` ` / 新标题 / 新列表打断，就回退，不做这次列表升级。
- **更稳妥的 Feishu 粗体编号块归一化规则**：把 `**2. 微信公众号凭证**` 这类“独占一行的粗体编号标题”升级成真正的 ordered list item 时，不要只吃掉下一行正文；应尽量把后续同属该编号项的块级内容一并收进去（例如说明段、bullet 列表、列表后的补充说明）。但同时要在这些边界前及时停止，避免过度吞并：
  - 下一个 `**3. ...**` 这类粗体编号标题
  - 独占一行的粗体小标题（如 `**方法一：...**` / `**方法二：...**`）
  - 新的章节标题（`#` / `##` ...）
  - `<hr />` 之类显式分隔块
  经验上，正确做法更接近“保留该编号项内的 block structure”，而不是把所有后续文本压成 `2. **标题** 正文` 单行。
- **如果 `2. 编号项` 下面还有 bullet 列表与补充说明，它们往往应该留在同一个编号项里。** 例如：
  - `2. **微信公众号凭证**`
  - 说明句
  - `- AppID`
  - `- AppSecret`
  - `同时把你的服务器 IP ...`
  这整块更适合归为同一个 ordered item；否则在微信里常会表现成“2. 标题”后又冒出额外编号/层级断裂。
- **排查“直接渲染正常，但完整发布链路异常”时，不要只看抓取回来的 raw markdown。** 像飞书→微信链路里，`doc_meta['markdown']` 往往还是原始抓取结果，真正送进渲染器的是 `article.content_markdown`（已经过 normalize）；很多 bug 就藏在这层 normalize 里。定位时要同时对拍：
  - raw fetched markdown
  - normalized article markdown
  - `render_markdown(...)` 直出 HTML
  - 完整 publish/dry-run payload HTML
- **Shell / Bash 代码块的“Doocs 味儿”不只在三色圆点。** 如果用户给了终端窗口参考图，往往还期待：
  - 深色终端底色（接近 `#24292f`）
  - 亮色正文（接近 `#e6edf3`）
  - 顶部居中的小标签（如 `terminal`）
  - Mac dots 与标题层级正确，不被代码覆盖
  这些可以在服务端 HTML 里直接补上，无需等浏览器端 CSS 再加工。
- `hr_style` 只进 CLI，没进 render function
- 预览页增强了，但发布 HTML 没同步 class
- 样式注入后导致摘要提取正则失效
- **飞书/Lark 导出的 Markdown 经常“视觉上分行、语义上没分块”**。典型症状：
  - `**1. 标题**`、下一行正文、再下一行 `**2. 标题**` 这类结构，看起来像编号说明，但 Markdown 解析时会被压成一个普通段落
  - 列表项后面的说明句、下一段粗体小标题（如“方法二/方法三”）如果缺少空行，很容易被继续吸进上一个 `ul/ol/li`
  - 结果就是：有序列表丢失、正文被揉平，甚至后面的块级元素看起来像“串位”
- 处理这类飞书内容时，**在进入 renderer 前先做结构归一化（normalization）**，比事后修 HTML 更稳。实战可复用两条规则：
  1. 把 `**1. 标题**` + 下一行正文，批量改写成真正的 Markdown 有序列表项：`1. **标题** 正文`
  2. 给“独占一行的粗体小标题”和“列表结束后的普通说明段”主动补空行，强制切断块级结构，避免被前一个列表或段落吞进去
- 如果文章里有大量命令行示例，**shell/bash 代码块建议单独走 terminal-style 视觉分支**，不要和普通代码块完全同皮：
  - 终端类语言可识别为：`bash/sh/shell/zsh/console/terminal`
  - 保留 Mac 三色圆点
  - 终端块背景改为深色（如 `#24292f`），正文改浅色（如 `#e6edf3`）
  - 可选加居中小标题（如 `terminal`），更接近 Doocs / 截图类教程的直觉观感
- **判断问题出在“源 Markdown 结构”还是“后处理渲染”** 的最快方法：
  1. 先打印飞书抓回来的原始 markdown 片段
  2. 再直接看 `MarkdownIt(...).render(chunk)` 的原始 HTML
  3. 最后再看你自己 decorate/post-process 后的 HTML
  这样能快速分辨：到底是飞书导出没给够语义，还是你后处理把结构搞串了

- 样式注入后导致摘要提取正则失效

## 本次实战新增经验（Feishu → 微信草稿箱）

### 1. 先修“结构语义”，再修“像不像 Doocs”

如果源内容来自飞书/Lark，很多问题并不是 CSS 不够像 Doocs，而是 **Markdown 语义先坏了**。

这次实战确认：
- `**2. 微信公众号凭证**` 这类“粗体编号标题”后面的说明、bullet 列表、补充说明，必须在 normalize 阶段收拢成 **同一个 ordered list item**。
- `**3. 封面图的 media_id**` 这种标题项后面的“方法一 / 方法二 / 方法三”又必须 **及时断开**，否则会把整坨方法说明吞进同一条 list item 里，导致公众号里出现额外编号、折行错乱、代码块前串位。

推荐规则：
- 对 `**N. 标题**`：优先升级成真正的 `N. **标题**` ordered item。
- 后续块默认继续归入该 item，直到遇到：
  - 下一个 `**N. 标题**`
  - standalone strong 子标题（如 `**方法一：...**`）
  - 新 section heading / hr / fenced code 等明确块边界
- 对需要继续留在同一 item 内的内容（普通说明、bullet、补充说明），不要压平为一行；要保留为 item 内的多段 block。

### 2. ordered list 的 HTML 后处理不能把多段内容压扁

如果你把原生 `<ol><li>...</li></ol>` 改写成微信更稳定的 block 结构：
- **不要**把整个 `li` 内容塞进一个 inline `<span>`
- 应使用 block 容器（如 `<section class="md-ordered-item"> + <section class="md-ordered-text">`）承载内容
- 这样 list item 内的标题段、正文段、bullet 子块才不会被压成一行

这是这次“折行丢失 / 多余编号”问题的真实放大器之一。

### 3. 微信 access_token：stable_token 可能必须 force_refresh=true

实战中，公众号草稿箱发布并不总能稳定使用旧的 `/cgi-bin/token` 结果。

本次验证到：
- `/cgi-bin/stable_token` 可用
- 某些公众号环境下，即便 stable_token 也可能要求 **`force_refresh=true`** 才会被微信接受为“latest”
- 否则会遇到：
  - `40001 invalid credential, access_token is invalid or not latest`

建议：
- 对公众号草稿发布链路，优先使用 `stable_token`
- 若环境已经出现 “not latest” 错误，直接切到 `force_refresh=true`
- 如果 token 一直要求 latest，缓存反而可能制造问题；宁可每次重新取 stable token，也不要盲信旧缓存

### 4. code block 要想像 Doocs，关键不是 Mac dots，而是“服务端高亮 + 正确保空格换行”

如果目标是接近 Doocs 的 code block：
- 不能只做浅色背景 + Mac 三色圆点
- 还必须有：
  - 服务端高亮 token HTML
  - 非行号模式下保留 `<br/>`
  - 空格转 `&nbsp;`
  - 行号模式下使用独立行号列

这次对照 Doocs 源码确认：
- Doocs 的关键逻辑在 `packages/core/src/utils/languages.ts` 的 `highlightAndFormatCode(...)`
- 其核心语义是：
  - 先高亮
  - 再把 span 间空格移入 span 内
  - 再处理换行和空格保留
  - 行号模式生成单独列，而不是每行前硬拼数字

### 5. 自定义 Pygments style 可能把 bash / env 行高亮搞坏；更稳的是“默认输出 + 安全 remap 颜色”

这次踩到的真实坑：
- 直接给 Pygments 定义一套模仿 GitHub/Doocs 的自定义 Style，可能会让某些 bash 行（尤其 `export VAR="***"` 这种）输出损坏的 inline HTML
- 结果不是“颜色差一点”，而是 HTML 直接坏掉

更稳的做法：
1. 先用 Pygments 默认稳定输出 inline HTML
2. 再做一层 **有限、安全的颜色 remap**
   - 例如把常见默认色映射到更接近 GitHub/Doocs 的颜色：
     - 关键字绿色 → `#22863A`
     - 变量蓝色 → `#005CC5`
     - 字符串深蓝 → `#032F62`
     - 注释灰 → `#6A737D`
3. 只做经过验证的少量替换，不要在 tokenizer 层过度“自造主题”

### 6. Mac 顶部更像 Doocs 的做法：header 与 code padding 分层

比起简单绝对定位三个圆点，更接近 Doocs 的做法是：
- 在 `pre` 里面先插一个单独的 Mac sign/header 区块
- header 负责顶部留白与圆点
- `code` 自己再负责正文 padding

实践上比“`pre` 整体大 padding + 圆点 absolute 定位”更稳，也更容易继续细调。

### 7. 长命令块：`pre` 与 `code` 的 overflow 应分层控制

为了减少公众号里底部滚动条/灰线观感：
- `pre` 外层建议 `overflow: hidden`
- `code` 内层保留 `overflow-x: auto`
- 再加：
  - `scrollbar-width: none`
  - `-ms-overflow-style: none`

这样通常比直接让 `pre` 自己滚动更干净。

## 验收清单

- [ ] `list-styles` 可返回完整样式能力
- [ ] `render-preview` 能切换 Doocs-like preset
- [ ] `publish` 与 `render-preview` 使用同一套渲染参数
- [ ] callout/HR 在 preview 与发布 HTML 中都有稳定 class
- [ ] 全量测试通过
