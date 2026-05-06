任务：生成“过去24小时 AI / Agent / AIGC Top News 早报”，发布到飞书原生文档，并在发布成功后自动归档到飞书多维表。完成后把结果回传到当前聊天。

必须使用 daily-ai-agent-aigc-top-news skill 执行完整流程。

固定要求：
1. 时间窗口：过去24小时，时区 Asia/Shanghai。
2. 内容范围：AI / Agent / coding agent / eval / workflow / toolchain / AIGC 生图生视频。
3. 必须单独核查 <owner>/<repo>：release、最近24小时 commits、merged PR、重要用户可感知变化。
4. 必须检查 GitHub Trending Today；只能写成“今日趋势信号”，不能冒充过去24小时正式发布。
5. 必须检查 AIGC 生图 / 生视频官方源：OpenAI、Google、Runway、Pika、Kling、字节/即梦/Seedance、Midjourney、Ideogram、Adobe Firefly、Stability。
6. 真实性优先；不要硬凑条数。
7. 输出中文。
8. 发布为飞书原生文档，标题：AI / Agent / AIGC Top News 24h｜YYYY-MM-DD 08:00。
9. 创建后必须 docs +fetch 回读验收。
10. 如启用归档，归档到飞书多维表：base_token <FEISHU_BITABLE_BASE_TOKEN>，table_id <FEISHU_BITABLE_TABLE_ID>。
11. 如启用归档，归档后必须按 record_id 回读验收。
12. 最终回复包含：文档标题、doc_url、bitable_url、record_id、3～6条摘要。
