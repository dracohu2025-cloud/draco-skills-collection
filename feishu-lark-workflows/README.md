# feishu-lark-workflows

飞书 / Lark 自动化工作流 skill。

它不是单一脚本，更像一张路线图：什么时候该创建原生文档，什么时候该查多维表字段，什么时候该走 Drive 上传，什么时候别手拼 JSON。

![工作流预览](./assets/feishu-lark-workflows-flow.svg)

## 适合做什么

| 场景 | 推荐动作 |
|---|---|
| 创建飞书文档 | `lark-cli docs +create` |
| 回读验收文档 | `lark-cli docs +fetch` |
| 写多维表 | 先查 fields，再写 records |
| 上传文件 | 走 Drive upload，再取可打开链接 |
| 排查权限 | `lark-cli auth status/scopes` |

## 快速检查

```bash
lark-cli auth status
lark-cli auth scopes
```

## 多维表字段检查

```bash
lark-cli api GET "/open-apis/bitable/v1/apps/<BASE_TOKEN>/tables/<TABLE_ID>/fields?page_size=100" --as user
```

## 常见坑

- URL 字段别写裸字符串，通常要 `{link, text}`
- Markdown 附件不是飞书原生文档
- 写记录前先查字段类型
- 文件上传和附件字段写入通常是两个动作

## 和早报 skill 的关系

`daily-ai-agent-aigc-top-news` 用它处理飞书文档发布、回读验收、多维表写入这些平台动作。
