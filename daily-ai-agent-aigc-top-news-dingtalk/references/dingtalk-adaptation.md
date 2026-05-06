# DingTalk 适配方案 — daily-ai-agent-aigc-top-news-dingtalk

## 适配概览

发布目标为**钉钉文档**，归档目标为**钉钉多维表**。本 skill 是钉钉专用版，不涉及飞书。

## 核心命令

| 操作 | 命令 |
|---------|-------------|
| 创建钉钉文档 | `dws doc create --name "..." --markdown "..." --format json` |
| 读取钉钉文档 | `dws doc read --node "<NODE_ID>" --format json` |
| 创建多维表记录 | `dws aitable record create --base-id ... --table-id ... --records ... --format json` |
| 查询多维表记录 | `dws aitable record query --base-id ... --table-id ... --record-ids ... --format json` |
| 获取多维表 schema | `dws aitable table get --base-id ... --table-id ... --format json` |
| 钉钉文档 URL | `https://alidocs.dingtalk.com/i/nodes/{nodeId}` |
| 钉钉多维表 URL | `https://alidocs.dingtalk.com/i/nodes/{baseId}` |

## 改造要点

1. **早报发布**：`dws doc create` 创建钉钉文档，提取 `nodeId`
2. **回读验收**：`dws doc read --node <NODE_ID>` 读取内容做校验
3. **归档**：`python3 scripts/sync_doc_to_dingtable.py`（ai-news-bitable-archive-dingtalk skill 提供）
4. **报告链接**：使用 alidocs.dingtalk.com 域名

## 注意事项

- 报告内容（AI/Agent/AIGC 新闻筛选逻辑）与飞书版完全一致
- 仅发布和归档的存储层不同
- dws CLI 自动处理钉钉认证
- 钉钉多维表 URL 格式：`https://alidocs.dingtalk.com/i/nodes/{baseId}`
- 归档脚本自动处理字段名→fieldId 映射，无需手动查 schema
