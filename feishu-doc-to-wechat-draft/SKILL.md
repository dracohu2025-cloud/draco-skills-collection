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

## 真实发布

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