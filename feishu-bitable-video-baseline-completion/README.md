# feishu-bitable-video-baseline-completion

把已经验收的 AI 视频版本，补成一条完整、可复盘的飞书多维表基线记录。

它解决的问题很具体：视频成片已经有了，但多维表这一行缺上游资产链路，比如角色参考图的工具、Prompt、图片附件，场景参考图的来源，Payload、QA、成本和输出映射。

![工作流预览](./assets/feishu-bitable-video-baseline-completion-flow.svg)

## 适合做什么

| 场景 | 动作 |
|---|---|
| 视频版本已验收，但表格行缺内容 | 回填资产链路 |
| 缺角色参考图工具 / Prompt / 图片 | 从来源资产行补齐 |
| 缺场景参考图来源 | 补工具、Prompt、附件、URL |
| 多个历史行分散 | 合并成一条 baseline 行 |
| 需要防止凭据泄漏 | 推送前做敏感信息扫描 |

## 核心流程

1. 定位目标视频行
2. 回读字段结构和已有内容
3. 定位来源资产行
4. 用 hash 校验本地文件 / 公网文件 / 来源资产一致
5. 上传缺失附件到目标行
6. 批量补写工具、Prompt、资产映射
7. 回读目标行，确认缺失数为 0

## 典型补全字段

```text
角色参考图（CRS）_角色1_工具
角色参考图（CRS）_角色1_Prompt
输入资产_角色1参考图

场景环境设定参考图（SES）_工具
场景环境设定参考图（SES）_Prompt
输入资产_场景环境设定参考图

Prompt_Output_Map
Reference_URLs
视频生成_Prompt
视频生成 Payload文件
生成视频成片
质量检查抽帧图
QA摘要
视频生成_Tokens
视频生成_估算成本CNY
```

## 关键原则

- 一条合格视频 = 一条可审计 baseline 记录
- 附件给人看，公网 URL 给 API 复现
- Prompt 和资产来源必须能追溯
- 不把 token、table id、API key、签名 URL 写进公开仓库
- 更新后必须 `record-get` 回读验证

## 最小使用方式

把 `SKILL.md` 放到支持 Agent Skills 的环境中。遇到“合格视频行缺资产链路”的任务时加载此 skill。

```text
Use when a Feishu/Lark Base row for an approved video baseline is missing upstream asset lineage, prompts, tools, URLs, or attachment fields.
```

## 常见坑

- 飞书附件上传不要传绝对路径，先 `cd` 再传相对文件名
- `record-list` 可能看不到长字段完整内容，验证用 `record-get`
- `record-batch-update` 要用 `record_id_list + patch` 结构
- 不能只凭记忆补资产，要看 payload、Reference_URLs 和 hash
- 推 Git 前先扫敏感凭据
