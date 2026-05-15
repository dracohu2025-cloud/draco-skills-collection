# ai-news-bitable-archive

把飞书原生日报文档解析后，写入飞书多维表。

它适合接在 `daily-ai-agent-aigc-top-news` 后面：日报先发成飞书文档，然后把标题、Top3、摘要、文档链接等字段同步到多维表。

![工作流预览](./assets/ai-news-bitable-archive-flow.svg)

## 快速开始

```bash
cd ai-news-bitable-archive
python3 scripts/sync_doc_to_bitable.py   --doc-url 'https://www.feishu.cn/docx/xxxx'   --base-token '<FEISHU_BITABLE_BASE_TOKEN>'   --table-id '<FEISHU_BITABLE_TABLE_ID>'   --date 'YYYY-MM-DD'   --status '已归档'
```

## 需要什么

- `python3`
- `lark-cli`
- 已登录飞书/Lark
- 多维表 `base_token`
- 多维表 `table_id`

## 会写哪些字段

| 字段 | 来源 |
|---|---|
| 标题 | 文档标题 |
| 日期 | 参数或标题日期 |
| 文档链接 | `doc_url` |
| 文档Token | docx token |
| 统计窗口 | 文档正文 |
| Top1/Top2/Top3 | `## 最值得注意的 3 条` |
| 一句话结论 | `## 一句话结论` |
| 摘要 | Top3 拼接 |
| 状态 | 参数 |

## 注意

飞书多维表的 URL 字段通常要写成对象：

```json
{"link":"https://...", "text":"https://..."}
```

脚本已经处理了这个坑。
