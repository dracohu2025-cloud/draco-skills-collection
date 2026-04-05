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
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_secret_here
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

### 命令参数

#### `publish-feishu-doc-default` - 发布到草稿箱

| 参数 | 必填 | 说明 |
|------|------|------|
| `--doc` | ✅ | 飞书文档 URL |
| `--thumb-media-id` | ✅ | 封面图片的微信 media_id |
| `--author` | ❌ | 作者名（默认：DracoVibeCoding）|
| `--dry-run` | ❌ | 仅生成 payload，不实际发布 |

#### `render-preview-feishu-doc-default` - 生成本地预览

| 参数 | 必填 | 说明 |
|------|------|------|
| `--doc` | ✅ | 飞书文档 URL |
| `--output` | ✅ | 输出 HTML 文件路径 |

### 样式配置

默认使用 Doocs 风格的「优雅」主题（活力橘色），可通过修改 `examples/default-publish-style.yaml` 自定义：

```yaml
style:
  profile: doocs        # 渲染配置: doocs
  theme: 优雅            # 主题: 优雅/简单
  font: 无衬线           # 字体
  theme_colors: 活力橘    # 主题色
  font_size: 更小        # 字号: 更小(14px)/稍小(15px)/推荐(16px)
  code_theme: github     # 代码高亮主题
  mac_code_block: 开启    # Mac 风格代码块
  justify: 关闭          # 两端对齐
```

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

### Q: 如何获取封面图的 `thumb_media_id`？

A: 需要先调用微信的素材上传接口，或使用微信官方提供的测试工具上传封面图获取 media_id。

### Q: 发布时报 "IP 不在白名单" 错误？

A: 登录微信公众平台 → 开发 → 基本配置 → IP 白名单，添加你的服务器公网 IP。

### Q: 图片显示不出来？

A: 确保：
1. 图片能正常从飞书下载
2. 图片格式被微信支持（jpg/png/gif）
3. 图片大小不超过 10MB

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 PR！

---

Made with ❤️ by [DracoVibeCoding](https://github.com/dracohu2025-cloud)
