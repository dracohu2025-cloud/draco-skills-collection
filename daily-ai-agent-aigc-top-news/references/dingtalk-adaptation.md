# DingTalk 适配方案 — daily-ai-agent-aigc-top-news

## 适配概览

发布目标从**飞书原生文档**改为**钉钉文档**，归档目标从**飞书多维表**改为**钉钉多维表**。

## 核心替换

| 飞书路径 | 钉钉替代路径 |
|---------|-------------|
| `lark-cli docs +create` | `dws doc create --name "..." --markdown "..." --format json` |
| `lark-cli docs +fetch` | `dws doc read --node "<NODE_ID>" --format json` |
| `lark-cli base +*` | `dws aitable record create/update/query` |
| 飞书 doc_url | `https://alidocs.dingtalk.com/i/nodes/{nodeId}` |
| 飞书 bitable_url | `https://alidocs.dingtalk.com/i/nodes/{baseId}` |

## 改造要点

1. **早报发布**：`dws doc create` 创建钉钉文档，提取 `nodeId`
2. **回读验收**：`dws doc read --node <NODE_ID>` 读取内容做校验
3. **归档**：`python3 scripts/sync_doc_to_dingtable.py`（ai-news-bitable-archive skill 提供）
4. **报告链接**：所有飞书链接替换为钉钉链接

## 注意事项

- 报告内容（AI/Agent/AIGC 新闻筛选逻辑）完全不变
- 仅替换发布和归档的存储层
- dws 技能支持创建/读取钉钉文档和多维表
- 钉钉多维表 URL 格式：`https://alidocs.dingtalk.com/i/nodes/{baseId}`
- 归档脚本自动处理字段名→fieldId 映射，无需手动查 schema