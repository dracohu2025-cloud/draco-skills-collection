---
name: daily-ai-agent-aigc-top-news-dingtalk
description: Use when generating a daily 24h AI / Agent / AIGC top-news briefing, publishing it as a DingTalk document, validating it, and optionally archiving it to a DingTalk multidimensional table. 钉钉专用版。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - news
    - ai
    - agent
    - aigc
    - briefing
    - cron
    - dingtalk
    - dws
    - aitable
    related_skills:
    - news-aggregator-skill
    - ai-news-bitable-archive-dingtalk
---
# Daily AI / Agent / AIGC Top News Briefing (DingTalk Edition)

## Overview

This skill runs a daily AI / Agent / AIGC morning briefing workflow.

It collects candidates from news aggregators and source-of-truth pages, filters for high-signal items, writes a Chinese 24h report, publishes it as a DingTalk document, fetches it back for validation, and optionally archives the result to a DingTalk multidimensional table.

Core rule: **truth first, no quota-filling**. If there are only a few important items, keep the report short.

## When to Use

Use this skill when the task asks for any of these:

- daily AI / Agent / AIGC top news
- 过去24小时 AI / Agent / AIGC 早报
- cron-generated AI morning briefing
- DingTalk document delivery
- AI news archive into DingTalk multidimensional table
- recurring report that must include Agent, AIGC image/video, GitHub Trending, and a mandatory project check

Do not use this for:

- broad weekly reports with a different time window
- pure finance/news briefings unrelated to AI / Agent / AIGC
- one-off research notes that do not need DingTalk publishing or multidimensional table archival

## Required Inputs

A cron prompt should be self-contained and include:

```text
Task: Generate the past-24h AI / Agent / AIGC Top News briefing.
Timezone: Asia/Shanghai.
Delivery: create DingTalk doc, fetch-back validate, optionally archive to DingTalk multidimensional table, send result to origin chat.
Archive base_id: <DINGTALK_BASE_ID>
Archive table_id: <DINGTALK_TABLE_ID>
Aitable URL: https://alidocs.dingtalk.com/i/nodes/<DINGTALK_BASE_ID>
Required project check: <owner>/<repo>
```

If no DingTalk folder ID is supplied, create the document in the default DingTalk location. Do not block.

## Output Contract

Final answer must include:

```md
已完成。

- 文档标题：...
- doc_url：...
- aitable_url：...  # if archival is enabled
- record_id：...    # if archival is enabled
- 摘要：
  - ...
  - ...
  - ...
```

If archival fails but doc publishing succeeds, say so explicitly and include the doc URL plus a short error summary.

## Phase 1 — Preflight

Always check live time. Do not infer time mentally.

```bash
date -u '+UTC=%Y-%m-%d %H:%M:%S' && TZ='Asia/Shanghai' date '+CST=%Y-%m-%d %H:%M:%S %Z'
```

No Feishu auth check needed. DingTalk document and multidimensional table operations go through `dws` CLI which handles auth automatically.

## Phase 2 — Source Collection

Prefer a local news aggregator as the first pass. It gives candidates, not final truth.

Example commands, adapt paths to your local setup:

```bash
python3 path/to/news_aggregator_run.py smoke-test --quick
python3 path/to/news_aggregator_run.py fetch --source hackernews --limit 30 --deep --save --outdir /tmp/<run>/hn
python3 path/to/news_aggregator_run.py fetch --source github --limit 30 --deep --save --outdir /tmp/<run>/github
python3 path/to/news_aggregator_run.py fetch --source huggingface --limit 30 --deep --save --outdir /tmp/<run>/hf
```

Also perform targeted checks against official/source-of-truth pages. At minimum check:

- OpenAI models / image / video updates
- Google Gemini / Imagen / Veo updates
- Anthropic / Claude / coding-agent updates
- Runway
- Pika
- Kling / 可灵
- ByteDance / 即梦 / Seedance
- Midjourney
- Ideogram
- Adobe Firefly
- Stability AI
- GitHub Trending Today for AI / Agent / AIGC / developer-tool / infra projects

Use web search/extract for current facts. If a page blocks extraction, combine search-result snippets, official docs/API pages, and one reputable secondary source.

## Phase 3 — Mandatory Project Check

Always check the configured project separately. External popularity does not decide whether it appears.

Default recommended project for this workflow:

```text
NousResearch/hermes-agent
```

### A. Local clone, if available

```bash
REPO_DIR="/path/to/local/repo"
if git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$REPO_DIR" fetch origin --prune
  git -C "$REPO_DIR" log origin/main --since='24 hours ago' --pretty=format:'%h | %ad | %s' --date=iso
fi
```

### B. Latest release

```bash
python3 - <<'PY'
import json, urllib.request
owner_repo = 'NousResearch/hermes-agent'
req = urllib.request.Request(
    f'https://api.github.com/repos/{owner_repo}/releases/latest',
    headers={'User-Agent':'Daily-AI-Agent-Briefing'}
)
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.load(r)
print(json.dumps({k:data.get(k) for k in ['tag_name','name','published_at','html_url']}, ensure_ascii=False, indent=2))
PY
```

### C. Recent merged PRs

```bash
python3 - <<'PY'
import json, urllib.parse, urllib.request, datetime
owner_repo = 'NousResearch/hermes-agent'
start = (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=24)).date().isoformat()
q = f'repo:{owner_repo} is:pr merged:>={start} sort:updated-desc'
url = 'https://api.github.com/search/issues?' + urllib.parse.urlencode({'q':q,'per_page':10})
req = urllib.request.Request(url, headers={'User-Agent':'Daily-AI-Agent-Briefing'})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.load(r)
for item in data.get('items',[])[:10]:
    print(json.dumps({'number':item['number'],'title':item['title'],'html_url':item['html_url']}, ensure_ascii=False))
PY
```

Include the checked project if any of these occurred in the window:

- release
- dashboard / admin / gateway changes
- platform adapter or messaging fixes
- provider/model routing changes
- memory / facts / skills / cron / backup / debug workflow changes
- onboarding/auth/config stability improvements

If there is no material update, still mention that the check was performed in source notes or omit the section only if truly empty. Never skip the check.

## Phase 4 — Selection Rules

Use this priority order:

1. official release / changelog / docs / API evidence
2. GitHub release / merged PR / commit evidence
3. reputable media report
4. HN / social discussion as secondary signal
5. GitHub Trending as trend signal only

Hard rules:

- Do not write rumors as releases.
- Do not convert GitHub Trending Today into "past 24h launched". Say "今日趋势信号".
- HN Algolia is noisy. Treat it as discovery, not proof.
- Verify important HN links using original `objectID` / `hn_url`; do not guess item IDs.
- If official naming differs from media naming, state the official name clearly.
- AIGC image/video must be checked daily, even if no item survives final selection.
- Prefer fewer strong items over many weak items.

## Phase 5 — Report Structure

Title format:

```text
AI / Agent / AIGC Top News 24h｜YYYY-MM-DD 08:00
```

Markdown body template:

```md
更新于：YYYY-MM-DD 08:00 CST

统计窗口：过去24小时

筛选口径：官方发布 / GitHub release 或 PR / 权威媒体 / 开源趋势信号。Trending 只作为趋势，不等同于正式发布。

最终保留：N 条。没硬凑。

## 最值得注意的 3 条

### 1. 标题
发生了什么：...
为什么重要：...
对工作流影响：...
来源：...

### 2. 标题
...

### 3. 标题
...

## 模型 / Agent 产品

## AIGC 生图 / 生视频

## 评测 / 基准 / 研究

## GitHub Trending / 开源趋势信号

## 开源项目 / Toolchain 信号

## 指定项目过去24小时更新

## 产业动态

## 一句话结论
...
```

Formatting rules:

- Chinese only, unless product/repo/model names need English.
- Every `##` heading must have a blank line before it.
- Every retained news item should explain: what happened / why it matters / practical workflow impact.
- Avoid hype words and generic filler.
- Links must point to the actual source when possible.

## Phase 6 — Publish DingTalk Doc

Write the report to a local temporary Markdown file, then create the DingTalk doc:

```bash
dws doc create \
  --name 'AI / Agent / AIGC Top News 24h｜YYYY-MM-DD 08:00' \
  --markdown "$(cat /tmp/daily_report.md)" \
  --format json
```

If a folder is specified:

```bash
dws doc create \
  --name 'AI / Agent / AIGC Top News 24h｜YYYY-MM-DD 08:00' \
  --markdown "$(cat /tmp/daily_report.md)" \
  --folder '<DINGTALK_FOLDER_ID>' \
  --format json
```

Extract `nodeId` from the response. The doc URL is:

```text
https://alidocs.dingtalk.com/i/nodes/{nodeId}
```

## Phase 7 — Fetch-Back Validation (DingTalk)

```bash
dws doc read --node '<NODE_ID>' --format json
```

Validate from the returned `content`:
- title is correct
- opening metadata contains 更新时间 / 统计窗口 / 筛选口径
- `## 最值得注意的 3 条` exists
- `## AIGC 生图 / 生视频` exists
- `## GitHub Trending / 开源趋势信号` exists
- `## 一句话结论` exists
- mandatory project check was performed and is represented if material
- paragraphs are not glued together

## Phase 8 — Optional Archive to DingTalk Multidimensional Table

Use the dedicated DingTalk archive script from the `ai-news-bitable-archive-dingtalk` skill:

```bash
python3 scripts/sync_doc_to_dingtable.py \
  --doc-url 'https://alidocs.dingtalk.com/i/nodes/<NODE_ID>' \
  --base-id '<DINGTALK_BASE_ID>' \
  --table-id '<DINGTALK_TABLE_ID>' \
  --date 'YYYY-MM-DD' \
  --status '已归档'
```

The script returns `record_id`. Validate:

```bash
dws aitable record query \
  --base-id '<DINGTALK_BASE_ID>' \
  --table-id '<DINGTALK_TABLE_ID>' \
  --record-ids '<RECORD_ID>' \
  --format json
```

Verify fields: 标题, 文档链接, 文档Token, 统计窗口, Top1-3, 一句话结论, 摘要, 状态.

## Cron Prompt Template

```text
任务：生成"过去24小时 AI / Agent / AIGC Top News 早报"，发布到钉钉文档，并在发布成功后自动归档到钉钉多维表。完成后把结果回传到当前聊天。

必须使用已加载的 daily-ai-agent-aigc-top-news-dingtalk skill 执行完整流程。

固定要求：
1. 时间窗口：过去24小时，时区 Asia/Shanghai。
2. 内容范围：AI / Agent / coding agent / eval / workflow / toolchain / AIGC 生图生视频。
3. 必须单独核查 <owner>/<repo>：release、最近24小时 commits、merged PR、重要用户可感知变化。
4. 必须检查 GitHub Trending Today；只能写成"今日趋势信号"，不能冒充过去24小时正式发布。
5. 必须检查 AIGC 生图 / 生视频官方源：OpenAI、Google、Runway、Pika、Kling、字节/即梦/Seedance、Midjourney、Ideogram、Adobe Firefly、Stability。
6. 真实性优先；不要硬凑条数。
7. 输出中文。
8. 发布为钉钉文档，标题：AI / Agent / AIGC Top News 24h｜YYYY-MM-DD 08:00。
9. 创建后必须 dws doc read 回读验收。
10. 如启用归档，归档到钉钉多维表：base_id <DINGTALK_BASE_ID>，table_id <DINGTALK_TABLE_ID>。
11. 如启用归档，归档后必须按 record_id 回读验收。
12. 最终回复包含：文档标题、doc_url（alidocs.dingtalk.com）、aitable_url、record_id、3～6条摘要。
```

Attach these skills to the cron job if available:

```text
daily-ai-agent-aigc-top-news-dingtalk
news-aggregator-skill
ai-news-bitable-archive-dingtalk
```

## Common Pitfalls

1. **Only using the aggregator.** Aggregator gives candidates; official/GitHub/API evidence decides inclusion.

2. **Skipping AIGC media checks.** Daily report must cover image/video model and product updates, even when the final answer says no material update.

3. **Treating Trending as release news.** GitHub Trending is a trend signal only.

4. **Guessing HN item IDs.** Always use `objectID` / `hn_url` from source data.

5. **Forgetting the mandatory project check.** It is a separate check, not just another candidate.

6. **Shell JSON pain.** For DingTalk multidimensional table, prefer Python subprocess with argv and JSON serialization.

7. **Reporting before validation.** Doc creation alone is not enough. Fetch back the doc and the multidimensional table record.

8. **Writing glued Markdown.** Keep blank lines between intro paragraphs and before every `##` heading.

## Verification Checklist

- [ ] Live CST time checked
- [ ] DingTalk auth handled by dws CLI
- [ ] Aggregator ran or fallback search was used
- [ ] Official/source checks performed
- [ ] GitHub Trending Today checked and labeled as trend
- [ ] AIGC image/video official sources checked
- [ ] Mandatory project checked separately
- [ ] Report written in Chinese with required sections
- [ ] DingTalk doc created via `dws doc create`
- [ ] `dws doc read` validation passed
- [ ] DingTalk multidimensional table archive script ran, if archival is enabled
- [ ] Archived record fetched by `record_id`, if archival is enabled
- [ ] Final reply includes title, doc_url (alidocs.dingtalk.com), archive info when enabled, and summaries
