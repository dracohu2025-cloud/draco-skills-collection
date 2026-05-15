# news-aggregator-skill

一个本地新闻候选抓取 skill。适合给日报、早报、选题池提供第一批线索。

它不是“真相机器”。它负责把候选捞上来，最终是否写进报告，还要看官方发布、GitHub release/PR、API 文档或权威媒体。

![工作流预览](./assets/news-aggregator-flow.svg)

## 适合做什么

| 场景 | 输出 |
|---|---|
| 看 Hacker News 热点 | JSON 候选列表 |
| 看 GitHub Trending | 今日趋势信号 |
| 看 Hugging Face Papers | 研究候选 |
| 给 AI 早报供料 | 可核验的候选池 |

## 快速开始

```bash
cd news-aggregator-skill
python3 scripts/news_aggregator_run.py smoke-test --quick
python3 scripts/news_aggregator_run.py fetch --source hackernews --limit 10 --save
python3 scripts/news_aggregator_run.py fetch --source github --limit 10 --save
python3 scripts/news_aggregator_run.py fetch --source huggingface --limit 10 --save
```

## 支持的 source

```text
hackernews
github
huggingface
```

这版公开仓库里的脚本走标准库实现，尽量少依赖，方便搬到新机器。

## 和 daily-ai-agent-aigc-top-news 的关系

`daily-ai-agent-aigc-top-news` 用它做第一轮候选抓取。后续还必须做来源核验。

## 注意

- GitHub Trending 只能写成“趋势信号”
- HN 只做发现，不做最终证据
- 重要新闻要回到官方源 / GitHub release / API 文档核验
