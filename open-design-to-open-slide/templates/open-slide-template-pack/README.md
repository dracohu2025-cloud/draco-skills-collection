# Open Slide 49-Deck Template Pack

这是真正随 skill 分发的模板资产包：**49 套 Open Slide React decks**。

| 分类 | 数量 | 页数 |
|---|---:|---:|
| Open-Slide 官方 / starter | 11 | 107 |
| Open-Design 移植 suite | 38 | 760 |
| 合计 | 49 | 867 |

## 怎么安装到你的 Open Slide 项目

在仓库根目录执行：

```bash
bash open-design-to-open-slide/scripts/install-template-pack.sh /path/to/your/open-slide-project
```

只装 OD 移植套件：

```bash
bash open-design-to-open-slide/scripts/install-template-pack.sh /path/to/your/open-slide-project --od
```

覆盖同名 deck：

```bash
bash open-design-to-open-slide/scripts/install-template-pack.sh /path/to/your/open-slide-project --overwrite
```

安装后在目标 Open Slide 项目里：

```bash
pnpm install
pnpm build
pnpm dev
```

## 目录结构

```text
open-design-to-open-slide/
  templates/open-slide-template-pack/
    manifest.json
    slides/
      <slug>/index.tsx
      <slug>/assets/...
  scripts/install-template-pack.sh
  scripts/list-template-pack.py
```

## Open-Slide 官方 / starter

| Slug | 页数 | 路径 |
|---|---:|---|
| `getting-started` | 13 | `slides/getting-started` |
| `open-slide-launch` | 7 | `slides/open-slide-launch` |
| `open-slide-anatomy` | 16 | `slides/open-slide-anatomy` |
| `vercel-ai-sdk` | 8 | `slides/vercel-ai-sdk` |
| `ssh-explained` | 10 | `slides/ssh-explained` |
| `material-design-2014` | 7 | `slides/material-design-2014` |
| `claude-code-intro` | 9 | `slides/claude-code-intro` |
| `harness-engineering` | 8 | `slides/harness-engineering` |
| `llm-fundamentals` | 12 | `slides/llm-fundamentals` |
| `nextjs-ppr-cache` | 8 | `slides/nextjs-ppr-cache` |
| `raycast-api` | 9 | `slides/raycast-api` |

## Open-Design 移植 suite

| Slug | 页数 | 路径 |
|---|---:|---|
| `od-brutalist-deck-suite` | 20 | `slides/od-brutalist-deck-suite` |
| `od-course-module-suite` | 20 | `slides/od-course-module-suite` |
| `od-cyber-terminal-suite` | 20 | `slides/od-cyber-terminal-suite` |
| `od-dashboard-brief-suite` | 20 | `slides/od-dashboard-brief-suite` |
| `od-docs-page-suite` | 20 | `slides/od-docs-page-suite` |
| `od-editorial-taste-suite` | 20 | `slides/od-editorial-taste-suite` |
| `od-email-marketing-suite` | 20 | `slides/od-email-marketing-suite` |
| `od-eng-runbook-suite` | 20 | `slides/od-eng-runbook-suite` |
| `od-finance-report-suite` | 20 | `slides/od-finance-report-suite` |
| `od-graphify-dark-suite` | 20 | `slides/od-graphify-dark-suite` |
| `od-hr-onboarding-suite` | 20 | `slides/od-hr-onboarding-suite` |
| `od-kami-paper-suite` | 20 | `slides/od-kami-paper-suite` |
| `od-kanban-board-suite` | 20 | `slides/od-kanban-board-suite` |
| `od-knowledge-blueprint-suite` | 20 | `slides/od-knowledge-blueprint-suite` |
| `od-magazine-poster-suite` | 20 | `slides/od-magazine-poster-suite` |
| `od-mobile-onboarding-suite` | 20 | `slides/od-mobile-onboarding-suite` |
| `od-motion-frames-suite` | 20 | `slides/od-motion-frames-suite` |
| `od-pitch-deck-suite` | 20 | `slides/od-pitch-deck-suite` |
| `od-pm-spec-suite` | 20 | `slides/od-pm-spec-suite` |
| `od-pricing-page-suite` | 20 | `slides/od-pricing-page-suite` |
| `od-product-launch-suite` | 20 | `slides/od-product-launch-suite` |
| `od-replit-atlas-suite` | 20 | `slides/od-replit-atlas-suite` |
| `od-replit-bevel-suite` | 20 | `slides/od-replit-bevel-suite` |
| `od-replit-bluehouse-suite` | 20 | `slides/od-replit-bluehouse-suite` |
| `od-replit-helix-suite` | 20 | `slides/od-replit-helix-suite` |
| `od-replit-holm-suite` | 20 | `slides/od-replit-holm-suite` |
| `od-replit-vance-suite` | 20 | `slides/od-replit-vance-suite` |
| `od-replit-world-dark-suite` | 20 | `slides/od-replit-world-dark-suite` |
| `od-replit-world-mint-suite` | 20 | `slides/od-replit-world-mint-suite` |
| `od-saas-landing-suite` | 20 | `slides/od-saas-landing-suite` |
| `od-social-carousel-suite` | 20 | `slides/od-social-carousel-suite` |
| `od-team-okrs-suite` | 20 | `slides/od-team-okrs-suite` |
| `od-tech-sharing-suite` | 20 | `slides/od-tech-sharing-suite` |
| `od-testing-safety-alert-suite` | 20 | `slides/od-testing-safety-alert-suite` |
| `od-weekly-update-suite` | 20 | `slides/od-weekly-update-suite` |
| `od-xhs-editorial-suite` | 20 | `slides/od-xhs-editorial-suite` |
| `od-xhs-pastel-suite` | 20 | `slides/od-xhs-pastel-suite` |
| `od-xhs-post-suite` | 20 | `slides/od-xhs-post-suite` |

## 注意

- 这些模板是 Open Slide React `Page[]`，不是 Open Design runtime。
- OD suite 是视觉语言移植；不捆绑 Open Design daemon、web app、agent adapter。
- 安装脚本默认不覆盖目标项目已有同名 deck；需要覆盖时显式传 `--overwrite`。
