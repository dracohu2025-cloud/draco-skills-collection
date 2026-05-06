# DingTalk 适配方案 — ai-news-bitable-archive

## 适配概览

输入从**飞书文档**改为**钉钉文档**，归档目标从**飞书多维表**改为**钉钉多维表**。

## 核心替换

| 飞书路径 | 钉钉替代路径 |
|---------|-------------|
| `lark-cli docs +fetch` | `dws doc read --node "<NODE_ID>" --format json` |
| `lark-cli base +*` | `dws aitable record create/update/query` |
| URL 字段 `{link, text}` | 钉钉多维表直接传字符串 URL |
| `sync_doc_to_bitable.py` | `sync_doc_to_dingtable.py` |

## 改造要点

- 解析字段逻辑完全保留（标题、日期、Top1-3、一句话结论、摘要）
- 仅替换数据读取和写入的存储层
- 钉钉版脚本 `sync_doc_to_dingtable.py` 已内置 schema 自动映射
- 查重逻辑不变：按文档Token 或日期匹配已有记录

## 快速开始

```bash
python3 scripts/sync_doc_to_dingtable.py \
  --doc-url 'https://alidocs.dingtalk.com/i/nodes/<NODE_ID>' \
  --base-id '<DINGTALK_BASE_ID>' \
  --table-id '<DINGTALK_TABLE_ID>' \
  --date 'YYYY-MM-DD' \
  --status '已归档'
```