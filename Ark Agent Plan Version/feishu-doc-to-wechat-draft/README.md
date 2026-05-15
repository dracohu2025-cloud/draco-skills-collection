# 飞书文档 → 微信公众号草稿箱

将飞书（Feishu/Lark）文档一键转换为微信公众号草稿，支持图片自动上传、样式渲染和预览功能。

## ✨ 功能亮点

- **🚀 一键发布**: 从飞书文档 URL 直接生成微信公众号草稿
- **🎨 精美排版**: 支持 Doocs 风格渲染（优雅/活力橘主题），与 md-editor 编辑器预览效果一致
- **📸 图片自动处理**: 自动下载飞书文档中的图片并上传至微信素材库
- **👁️ 本地预览**: 发布前可生成 HTML 预览文件，确认效果后再发布
- **🔒 安全 dry-run**: 支持仅生成 payload 不实际发布，方便调试

## 📸 效果预览

使用本工具渲染的公众号文章效果：

- 标题样式：圆角标签式 H2，带阴影效果
- 正文排版：14px 字体，1.75 倍行距，0.1em 字间距
- 引用块：左侧彩色边框，圆角背景
- 表格：圆角表头，柔和阴影
- 代码块：Mac 风格窗口装饰

## 🎯 适用场景

- 在飞书中协作编辑内容，完成后一键发布到公众号
- 保持飞书文档的图片、表格、格式完整迁移到微信
- 需要与 Doocs 编辑器一致的排版风格

## 📋 前置要求

### 1. 环境依赖

- Python 3.8+
- pip

### 2. 飞书访问权限

需要配置 `lark-cli` 并能访问目标飞书文档：

```bash
# 安装 lark-cli
npm install -g @larksuiteoapi/lark-cli

# 登录飞书账号
lark-cli login
```

### 3. 微信公众号配置

需要拥有微信公众号的 AppID 和 AppSecret：

1. 登录[微信公众平台](https://mp.weixin.qq.com/)
2. 进入「开发」→「基本配置」获取 AppID 和 AppSecret
3. 在「IP 白名单」中添加你的服务器 IP

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/dracohu2025-cloud/draco-skills-collection.git
cd draco-skills-collection/feishu-doc-to-wechat-draft

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的微信配置
```

`.env` 内容示例：

```bash
WECHAT_APP_ID=your_wechat_app_id_here
WECHAT_APP_SECRET=your_wechat_app_secret_here
```

### 3. 生成预览（可选）

在正式发布前，先生成 HTML 预览确认效果：

```bash
python3 scripts/run.py render-preview-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --output /tmp/preview.html
```

在浏览器中打开 `/tmp/preview.html` 查看效果。

### 4. 发布到微信草稿箱

```bash
# 使用默认样式发布
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --thumb-media-id "your_cover_image_media_id"
```

成功后会返回 `draft_media_id`，可在微信公众号后台的「草稿箱」中查看。

## 📝 使用说明

### 命令列表

| 命令 | 用途 |
|------|------|
| `publish-feishu-doc-default` | 发布飞书文档到微信草稿箱（使用默认样式） |
| `render-preview-feishu-doc-default` | 生成本地 HTML 预览文件 |
| `list-styles` | 列出所有可用的样式配置选项 |

### 命令参数详解

#### `publish-feishu-doc-default` - 发布到草稿箱

**基础参数：**

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--doc` | ✅ | - | 飞书文档 URL，例如 `https://your-domain.feishu.cn/docx/DocID` |
| `--thumb-media-id` | ✅ | - | 封面图片的微信 media_id（需提前上传获取） |
| `--author` | ❌ | `Author` | 文章作者名（显示在公众号文章底部） |
| `--digest` | ❌ | - | 文章摘要（默认自动提取正文前120字） |
| `--cover-image` | ❌ | - | 封面图片本地路径（自动上传并设置为封面） |
| `--source-url` | ❌ | - | 原文链接（显示在文章底部「阅读原文」） |
| `--identity` | ❌ | `user` | 飞书身份类型：`user` 或 `bot` |
| `--assets-dir` | ❌ | `.` | 临时资源下载目录 |
| `--dry-run` | ❌ | - | 仅生成 payload，不实际发布（用于调试） |

**微信认证参数（如不设置则从环境变量读取）：**

| 参数 | 说明 |
|------|------|
| `--appid` | 微信公众号 AppID |
| `--appsecret` | 微信公众号 AppSecret |

#### `render-preview-feishu-doc-default` - 生成本地预览

| 参数 | 必填 | 说明 |
|------|------|------|
| `--doc` | ✅ | 飞书文档 URL |
| `--output` | ✅ | 输出 HTML 文件路径，例如 `/tmp/preview.html` |
| `--author` | ❌ | 作者名 |
| `--digest` | ❌ | 文章摘要 |

### 关于 Doocs 样式

本工具的排版样式参考了 [Doocs/md](https://github.com/doocs/md) 项目，一款开源的微信 Markdown 编辑器。

- **项目地址**：https://github.com/doocs/md
- **开源协议**：WTFPL (Do What The Fuck You Want To Public License) —— 你可以随意使用，建议保留版权声明

Doocs/md 是一款高度简洁的微信 Markdown 编辑器，支持 Markdown 语法、自定义主题样式、内容管理等特性。本工具提取并实现了其 CSS 渲染逻辑，确保在命令行环境下也能获得一致的排版效果。

### 样式配置参数（Doocs 风格）

所有发布和预览命令都支持以下样式参数，用于精细控制排版效果：

#### 1. 基础样式

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `--profile` | `default`, `doocs`, `classic`, `minimal` | 整体渲染配置方案 |
| `--theme` | `default`, `grace` (优雅), `simple` (简单) | 主题风格 |
| `--primary-color` | 任意 HEX 色值 | 主题主色（如标题、强调色） |
| `--font-family` | 字体名称 | 正文字体 |
| `--font-size` | 整数 | 正文字号（px） |
| `--line-height` | 浮点数 | 行高倍数（如 1.75） |

#### 2. 排版控制

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `--justify` | 布尔值 | 段落两端对齐（默认关闭，建议左对齐） |
| `--indent-first-line` | 布尔值 | 段落首行缩进 2 字符（默认关闭） |

#### 3. 标题样式

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `--heading-style` | `solid`, `left-bar`, `underline`, `minimal` | 标题整体风格 |
| `--h1-style` | `default`, `color-only`, `border-bottom`, `border-left`, `custom` | H1 样式 |
| `--h2-style` | 同上 | H2 样式 |
| `--h3-style` | 同上 | H3 样式 |
| `--h4-style` | 同上 | H4 样式 |
| `--h5-style` | 同上 | H5 样式 |
| `--h6-style` | 同上 | H6 样式 |

**标题风格说明：**
- `solid`: 实心背景块（grace 主题默认，圆角带阴影）
- `left-bar`: 左侧彩色边框
- `underline`: 底部下划线
- `minimal`: 极简样式

#### 4. 代码块样式

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `--code-theme` | `dark`, `light`, `github`, `github-dark`, `github-dark-dimmed`, `github-light`, `one-dark`, `vitesse-light`, `vitesse-dark` | 代码高亮主题 |
| `--mac-code-block` | 布尔值 | Mac 风格代码块（显示红黄绿三个圆点） |
| `--code-line-numbers` | 布尔值 | 显示代码行号 |

#### 5. 其他元素

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `--hr-style` | `dash` (虚线), `star` (星号), `underscore` (下划线) | 分隔线样式 |
| `--caption-mode` | `title-first`, `alt-first`, `title-only`, `alt-only`, `hidden` | 图片题注显示方式 |
| `--footnote-links` | 布尔值 | 将文中外链转为底部脚注形式 |

#### 6. 配置文件方式

对于复杂的样式组合，建议使用配置文件：

| 参数 | 说明 |
|------|------|
| `--style-config` | YAML/JSON 样式配置文件路径 |
| `--style-json` | 内联 JSON 样式配置 |

### 样式配置示例

#### 方式一：命令行参数

```bash
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --thumb-media-id "your_media_id" \
  --author "YourName" \
  --profile doocs \
  --theme grace \
  --primary-color "#FA5151" \
  --font-size 14 \
  --line-height 1.75 \
  --mac-code-block \
  --no-justify
```

#### 方式二：配置文件（推荐）

创建 `my-style.yaml`：

```yaml
style:
  profile: doocs
  theme: grace
  primary_color: "#FA5151"
  font_family: "-apple-system, BlinkMacSystemFont, Helvetica Neue, PingFang SC, Microsoft YaHei"
  font_size: 14
  line_height: 1.75
  justify: false
  indent_first_line: false
  code_theme: github
  mac_code_block: true
  code_line_numbers: false
  hr_style: dash
  heading_style: solid
  heading_styles:
    h1: default
    h2: default
    h3: default
  caption_mode: hidden
  footnote_links: false
```

使用配置：

```bash
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --thumb-media-id "your_media_id" \
  --style-config my-style.yaml
```

### 查看所有可用选项

```bash
python3 scripts/run.py list-styles
```

输出包含所有可用的颜色预设、主题、代码高亮方案等选项。

## 📁 项目结构

```
feishu-doc-to-wechat-draft/
├── scripts/
│   ├── run.py                      # CLI 入口
│   └── wechat_draft_publisher/     # 核心逻辑
│       ├── cli.py                  # 命令行接口
│       ├── lark_docs.py            # 飞书文档获取
│       ├── renderer.py             # HTML 渲染（Doocs 风格）
│       ├── wechat_api.py           # 微信 API 封装
│       └── ...
├── examples/
│   └── default-publish-style.yaml  # 默认样式配置
├── requirements.txt                # Python 依赖
└── README.md                       # 本文件
```

## 🔧 工作原理

1. **获取文档**: 使用 `lark-cli` 下载飞书文档内容（包括图片）
2. **Markdown 转换**: 将飞书文档内容标准化为 Markdown
3. **HTML 渲染**: 使用 Doocs 风格渲染为微信公众号兼容的 HTML
4. **图片上传**: 自动上传文档中的图片到微信素材库，替换为微信 CDN 链接
5. **草稿发布**: 调用微信公众号 API 创建草稿

## ⚠️ 注意事项

1. **图片大小**: 微信要求图片不超过 10MB，过大的图片会自动压缩
2. **封面图**: 必须先上传封面图到微信素材库，获取 `thumb_media_id`
3. **权限**: 确保飞书账号有权限访问目标文档
4. **IP 白名单**: 发布前确保服务器 IP 已添加到微信公众号的 IP 白名单

## 🐛 常见问题

### Q: 如何获取微信公众号的 AppID 和 AppSecret？

A:
1. 登录[微信公众平台](https://mp.weixin.qq.com/)（需使用公众号管理员账号）
2. 左侧菜单 → 「开发」→「基本配置」
3. 在页面中找到：
   - **AppID(应用ID)**: 公开标识，直接复制
   - **AppSecret(应用密钥)**: 点击「重置」或「查看」，需管理员扫码验证后显示
4. **重要**: AppSecret 只显示一次，请立即保存到安全位置
5. 同页面下方「IP白名单」，点击「查看」添加你的服务器公网 IP（否则调用 API 会报错）

### Q: 如何获取封面图的 `thumb_media_id`？

A: 需要先调用微信的素材上传接口，或使用微信官方提供的测试工具上传封面图获取 media_id。

简易方法：使用微信提供的[在线调试工具](https://mp.weixin.qq.com/debug/)，选择「新增永久素材」接口上传封面图。

### Q: 发布时报 "IP 不在白名单" 错误？

A: 登录微信公众平台 → 开发 → 基本配置 → IP 白名单，添加你的服务器公网 IP。

获取服务器 IP 的方法：
```bash
curl ifconfig.me
```

### Q: 图片显示不出来？

A: 确保：
1. 图片能正常从飞书下载
2. 图片格式被微信支持（jpg/png/gif）
3. 图片大小不超过 10MB

## 🙏 致谢

- [Doocs/md](https://github.com/doocs/md) - 样式渲染参考了该项目的 CSS 设计，一款优秀的开源微信 Markdown 编辑器

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 PR！

---

Made with ❤️ by [DracoVibeCoding](https://github.com/dracohu2025-cloud)
