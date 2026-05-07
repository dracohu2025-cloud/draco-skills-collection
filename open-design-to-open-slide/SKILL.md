---
name: open-design-to-open-slide
description: Use when mining Open Design visual systems and converting them into Open Slide React template kits or standalone 20-page template albums, with build, deployment, screenshot QA, and provenance rules.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [open-design, open-slide, templates, react-slides, visual-qa]
    related_skills: [open-slide, presentation-visual-review, repo-credential-audit]
---

# Open Design → Open Slide Template Production

## Overview

This skill captures a practical workflow: use **Open Design** as a visual template corpus, then rebuild the result as **Open Slide** React slides.

Core rule: **Open Design is a source of design language, not a runtime dependency.** Mine its palettes, typography, page recipes, examples, and component rhythm; implement the output as Open Slide `Page[]` with React primitives.

## When to Use

Use this skill when you need to:

- Convert Open Design examples or design systems into Open Slide decks.
- Create an OD-derived template kit, suite, album, or gallery.
- Expand a small template suite into a reusable 20-page presentation pack.
- Build public-facing React slide templates with screenshot QA.
- Preserve design provenance while avoiding runtime coupling.

Do not use it for:

- Importing Open Design daemon, web app, agent adapter, or navigation runtime.
- Copying raw single-file HTML decks directly into Open Slide.
- Producing `.pptx` files.
- Shipping public repos without credential and path audits.

## Architecture Decision

| Layer | Source | Keep | Reject |
|---|---|---|---|
| Visual language | Open Design | color, typography, spacing, cards, diagrams, density | logos, brand lockups, vendor identity |
| Page recipes | Open Design examples | cover, agenda, metrics, diagram, timeline, quote, matrix | raw HTML navigation scripts |
| Runtime | Open Slide | React `Page[]`, TSX primitives, static build | Open Design daemon/runtime |
| QA | Headless browser | screenshots, hash checks, contact sheets | trusting build success only |

## Standard 20-Page Suite Structure

For OD-derived template suites, use this stable 20-page shape:

1. Cover
2. Agenda
3. Problem / Context
4. Framework
5. Content
6. Metrics / Data
7. Timeline / Roadmap
8. Diagram / Architecture
9. Closing / CTA
10. Section Divider
11. Quote / Key Insight
12. Comparison
13. Process / Workflow
14. Matrix / 2×2
15. Table / Spec
16. Case Study
17. Checklist
18. Risks / Tradeoffs
19. FAQ / Appendix
20. Thank You / Contact

Important learned preference:

- Keep the first 9 pages visually stable.
- Add coverage by appending pages 10–20.
- Do not mass-rewrite many suites into heavily scene-specific layouts unless screenshots prove the result is better.

## Workflow: Create a New OD-Derived Suite

1. Pick a slug:

```bash
mkdir -p slides/od-<name>-suite
```

2. Inspect Open Design source candidates:

```bash
# examples only; adapt paths to your local Open Design clone
ls skills/
ls templates/
ls design-systems/
```

3. Extract only:

- palette
- typography
- component shape
- visual rhythm
- page archetypes
- provenance path

4. Implement in Open Slide TSX:

```tsx
import type { CSSProperties, ReactNode } from 'react';
import type { DesignSystem, Page, SlideMeta } from '@open-slide/core';

export const design: DesignSystem = { /* tokens */ };
export const meta: SlideMeta = {
  title: 'OD <Name> Suite',
  description: '<Name> OD-derived 20-page Open Slide template suite.'
};
export const notes = [
  'Source: Open Design ...',
  'Runtime: Open Slide only'
];

const Cover: Page = () => /* ... */;
// ... 20 pages total
export default [
  Cover, Agenda, Problem, Framework, Content,
  Metrics, Timeline, Diagram, Closing,
  SectionDivider, QuoteInsight, Comparison, ProcessWorkflow,
  Matrix2x2, TableSpec, CaseStudy, ChecklistPage,
  RisksTradeoffs, FAQAppendix, ThankYou
];
```

5. Keep design helpers local and simple:

```tsx
const rgba = (h: string, a: number) => {
  const x = h.replace('#', '');
  const n = parseInt(x.length === 3 ? x.split('').map(c => c + c).join('') : x, 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
};

const isDarkBg = (h: string) => {
  const x = h.replace('#', '');
  const n = parseInt(x.length === 3 ? x.split('').map(c => c + c).join('') : x, 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 96;
};

const dark = isDarkBg(t.bg);
```

`dark` must be global if appended pages use it. Missing global `dark` can build successfully but render blank at runtime. Nasty little trap.

## Workflow: Expand a 9-Page Suite to 20 Pages

1. Count pages:

```bash
python3 - <<'PY'
from pathlib import Path
base = Path('slides')
for p in sorted(base.glob('od-*-suite/index.tsx')):
    s = p.read_text()
    pages = s.split('export default [')[-1].split(']')[0].count(',') + 1
    print(p.parent.name, pages)
PY
```

2. Append pages 10–20 from the standard recipe list.
3. Update copy such as `9 slides` → `20 pages`.
4. Update metrics such as `9` → `20` and `slides` → `pages`.
5. Ensure appended pages only reference globally available helpers.
6. Run build and screenshot QA.

## Build and Deploy

Typical Open Slide build:

```bash
pnpm install
pnpm build
```

For a static deployment, copy the build output to your web root. The exact path depends on your server.

## Screenshot QA

For important work, screenshot every page and build contact sheets.

Minimum QA checks:

- all expected screenshots exist
- public route or local preview loads
- DOM is not empty
- no near-blank pages
- screenshot hashes are unique unless duplication is intentional
- cover sheet and full contact sheet are generated

Representative command pattern:

```bash
CHROME=${CHROME:-chromium}
OUT=/tmp/od-suite-shots
mkdir -p "$OUT"
for slug in $(find slides -maxdepth 2 -path 'slides/od-*-suite/index.tsx' -printf '%h\n' | xargs -n1 basename | sort); do
  mkdir -p "$OUT/$slug"
  for p in $(seq 1 20); do
    "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
      --virtual-time-budget=6500 --window-size=1920,1080 \
      --screenshot="$OUT/$slug/p${p}.png" \
      "http://127.0.0.1:5173/s/$slug?p=$p"
  done
  echo "captured $slug"
done
```

Use Python/Pillow to compute hashes, detect near-blank images via image variance, and generate contact sheets.

## Visual Rules

1. Design for 16:9 fixed canvas.
2. One idea per page.
3. Use strong hierarchy and cards; avoid bullet dumps.
4. Use Open Design for rhythm, not runtime.
5. Keep provenance in `notes` or comments.
6. Strip obvious third-party logos and brand marks.
7. Avoid remote assets unless there is a strong reason.
8. Generate screenshots and contact sheets before declaring success.

## Common Pitfalls

1. **Copying Open Design HTML directly.** This creates a hidden second runtime. Port the design into React primitives instead.

2. **Missing global variables in appended pages.** Pages 10–20 often reference `dark`, `rgba`, `font`, `t`, `Card`, `Shell`, `Tag`, `H`, and `P`. If any are scoped inside old functions, the deck may build but render blank.

3. **Trusting route 200.** SPA route 200 only proves `index.html` was served. Use browser DOM/screenshot checks to catch white screens.

4. **Over-fitting each suite into scene-specific structure.** Preserve visual coherence first. Expand coverage by appending reusable pages.

5. **Huge screenshot jobs with no progress.** Use background execution and print progress per suite.

6. **Dismissing duplicate hashes.** Duplicate hashes may mean actual white screens. Check variance and DOM.

7. **Leaking local paths or internal URLs in public docs.** Public skills should use placeholders and environment variables.

## Verification Checklist

- [ ] Every suite exports the intended number of pages.
- [ ] `pnpm build` passes.
- [ ] Preview route opens in a browser.
- [ ] Screenshots cover every suite/page.
- [ ] Screenshot hash count equals screenshot count unless duplication is intentional.
- [ ] No near-blank pages by variance check.
- [ ] Contact sheet generated.
- [ ] Public version contains no secrets, private IDs, or machine-specific absolute paths.
