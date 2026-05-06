# DingTalk 适配方案 — ai-news-bitable-archive-dingtalk

## 适配概览

输入为**钉钉文档**，归档目标为**钉钉多维表**。本 skill 是钉钉专用版，不涉及飞书。

## 核心命令

| 操作 | 命令 |
|---------|-------------|
| 读取钉钉文档 | `dws doc read --node "<NODE_ID>" --format json` |
| 创建多维表记录 | `dws aitable record create --base-id ... --table-id ... --records ... --format json` |
| 更新多维表记录 | `dws aitable record update --base-id ... --table-id ... --records ... --format json` |
| 查询多维表记录 | `dws aitable record query --base-id ... --table-id ... --record-ids ... --format json` |
| 获取多维表 schema | `dws aitable table get --base-id ... --table-id ... --format json` |

## 改造要点

- 解析字段逻辑完全保留（标题、日期、Top1-3、一句话结论、摘要）
- 仅替换数据读取和写入的存储层
- 钉钉版脚本 `sync_doc_to_dingtable.py` 已内置 schema 自动映射
- 查重逻辑不变：按文档Token 或日期匹配已有记录
- URL 字段直接传字符串，无需 `{link, text}` 对象

## 快速开始

```bash
python3 scripts/sync_doc_to_dingtable.py \
  --doc-url 'https://alidocs.dingtalk.com/i/nodes/<NODE_ID>' \
  --base-id '<DINGTALK_BASE_ID>' \
  --table-id '<DINGTALK_TABLE_ID>' \
  --date 'YYYY-MM-DD' \
  --status '已归档'
```
