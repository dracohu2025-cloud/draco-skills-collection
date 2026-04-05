---
name: feishu-doc-to-wechat-draft
names:
  - feishu-doc-to-wechat-draft
aliases:
  - 飞书文档到微信草稿箱
  - 飞书文档微信草稿箱
  - lark-wechat-draft
description: 从飞书/Feishu 文档直接生成微信公众号草稿内容，支持 Doocs 风格渲染、图片自动上传和本地预览。
version: 1.0.0
author: DracoVibeCoding
license: MIT
metadata:
  hermes:
    tags: [feishu, lark, wechat, draft, markdown, publisher, preview, doocs]
---

# 飞书文档 → 微信草稿箱

将飞书（Feishu/Lark）文档一键转换为微信公众号草稿，完整支持图片上传、样式渲染和本地预览。

## 核心能力

- **飞书文档获取**: 通过 `lark-cli` 自动下载文档内容和图片
- **Doocs 风格渲染**: 与 md-editor 编辑器一致的优雅排版
- **图片自动处理**: 自动上传图片至微信素材库，替换 CDN 链接
- **安全发布**: 支持 dry-run 模式，预览确认后再发布

## 依赖要求

### 系统依赖
- Python 3.8+
- Node.js (用于 `lark-cli`)

### 工具依赖
```bash
npm install -g @larksuiteoapi/lark-cli
```

### Python 依赖
```bash
pip install PyYAML>=6.0 markdown-it-py>=4.0.0
```

### 凭证配置
环境变量：
```bash
export WECHAT_APP_ID="your_app_id"
export WECHAT_APP_SECRET="your_app_secret"
```

## 使用方式

### 1. 生成本地预览

```bash
python3 scripts/run.py render-preview-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --output /tmp/preview.html
```

### 2. 发布到微信草稿箱

```bash
# 基础用法
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --thumb-media-id "your_media_id"

# 指定作者
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --thumb-media-id "your_media_id" \
  --author "YourName"

# Dry-run 模式（仅生成 payload，不发布）
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --thumb-media-id "DRY_RUN" \
  --dry-run
```

## 样式配置

默认使用 Doocs 风格的「优雅」主题，通过 `examples/default-publish-style.yaml` 配置：

```yaml
style:
  profile: doocs
  theme: 优雅
  font: 无衬线
  theme_colors: 活力橘
  font_size: 更小      # 14px
  mac_code_block: 开启
  justify: 关闭        # 左对齐
```

## 工作流程

```
飞书文档 URL
    ↓
lark-cli 下载文档和图片
    ↓
Markdown 标准化处理
    ↓
Doocs 风格 HTML 渲染
    ↓
图片上传至微信素材库
    ↓
创建微信公众号草稿
    ↓
返回 draft_media_id
```

## 实现细节

### 文档获取 (`lark_docs.py`)
- 使用 `lark-cli docs +download` 下载 docx
- 使用 `lark-cli docs +media-download` 提取内嵌图片
- 处理飞书特有的表格、引用块等元素

### HTML 渲染 (`renderer.py`, `rendering.py`)
- 基于 Doocs/md 项目源码提取的 CSS 参数
- 支持 grace/simple/default 三种主题
- 14px/15px/16px 三档字号
- 左对齐/两端对齐可选

### 微信 API (`wechat_api.py`)
- Access Token 缓存管理
- 图片素材上传
- 草稿创建接口

## 文件结构

```
scripts/
├── run.py                      # CLI 入口
└── wechat_draft_publisher/
    ├── cli.py                  # 命令解析
    ├── lark_docs.py            # 飞书文档处理
    ├── renderer.py             # HTML 渲染引擎
    ├── rendering.py            # 样式配置
    ├── wechat_api.py           # 微信 API 封装
    ├── pipeline.py             # 发布流程
    ├── preview.py              # 预览生成
    └── validation.py           # 参数校验
```

## 限制与注意事项

1. **图片大小**: 微信限制 10MB，超大图片会自动压缩
2. **封面图**: 需先上传获取 `thumb_media_id`
3. **IP 白名单**: 发布服务器 IP 需在微信公众号后台配置
4. **权限**: 飞书账号需有文档访问权限

## 相关项目

- [doocs/md](https://github.com/doocs/md) - 本项目样式对齐的 Markdown 编辑器

## License

MIT
