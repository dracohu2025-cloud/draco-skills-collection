---
name: news-aggregator-skill
description: Use when collecting public news candidates from Hacker News, GitHub Trending, Hugging Face papers, and other web sources for briefings and daily reports.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
metadata:
  hermes:
    tags: [news, briefing, hackernews, github, huggingface, ai, local-only]
---

# News Aggregator Skill

## Overview

This skill provides a local-first news collection workflow for daily briefings.

It is designed to collect candidate items from public sources, not to decide truth by itself. Treat aggregator output as leads. Important items still need official/GitHub/API/media verification before they enter a final report.

## When to Use

Use this skill when the task asks to:

- collect AI / tech / open-source news candidates
- inspect Hacker News, GitHub Trending, or Hugging Face papers
- prepare source material for a daily briefing
- run a repeatable local news collection command

## Entry Point

```bash
python3 scripts/news_aggregator_run.py <subcommand> [...args]
```

Common commands:

```bash
python3 scripts/news_aggregator_run.py sources
python3 scripts/news_aggregator_run.py fetch --source hackernews --limit 10 --save
python3 scripts/news_aggregator_run.py fetch --source github --limit 10 --save
python3 scripts/news_aggregator_run.py fetch --source huggingface --limit 10 --save
python3 scripts/news_aggregator_run.py smoke-test --quick
```

## Source Rules

- Hacker News is useful for discovery, but noisy.
- GitHub Trending is a trend signal, not proof of a release.
- Hugging Face papers are useful for research signals, not product news.
- Official changelogs, GitHub releases/PRs, docs, and APIs outrank aggregator output.

## Output

The public helper script outputs JSON to stdout and can save reports under:

```text
reports/YYYY-MM-DD/<source>.json
```

## Common Pitfalls

1. Do not treat trending as a launch.
2. Do not cite HN comments as primary evidence.
3. Keep source URLs with each item.
4. Re-verify important items before writing a report.

## Verification Checklist

- [ ] `python3 scripts/news_aggregator_run.py smoke-test --quick` passes
- [ ] At least one target source returns JSON
- [ ] Saved output contains title and URL fields
- [ ] Final briefing uses verified sources, not only aggregator output
