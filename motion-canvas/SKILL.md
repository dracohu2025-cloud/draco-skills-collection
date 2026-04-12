---
name: motion-canvas
description: "Production pipeline for Motion Canvas — TypeScript-based programmatic vector animation with real-time preview. Use when users want explainer videos, technical demos, timeline-based motion graphics, code animations, animated UI mockups, or synchronized voice-over scenes built with Motion Canvas."
version: 1.0.0
metadata:
  hermes:
    tags: [motion-canvas, animation, typescript, motion-graphics, explainer-video, data-visualization]
    related_skills: [manim-video, p5js, excalidraw]
---

# Motion Canvas Production Pipeline

Motion Canvas sits between Manim and Remotion.

- **Manim** thinks in objects + transforms
- **Remotion** thinks in React components per frame
- **Motion Canvas** thinks in **scenes + timeline + reactive properties**

Use this skill when the user wants code-driven animation but prefers TypeScript, real-time preview, scene choreography, vector motion graphics, or synced narration.

## Best fit

Choose Motion Canvas when the task looks like one of these:

- animated explainers
- technical demos and mechanism walkthroughs
- data visualization with staged reveals
- animated UI / product mockups
- code walkthroughs with highlighted ranges
- timeline-synced narration

Avoid it when the real need is:

- pure math / formula-heavy proof animation → prefer `manim-video`
- bulk React template videos / content factory → prefer Remotion-style workflow
- browser-interactive art toy / open-ended generative sketch → prefer `p5js`

## Core mental model

A Motion Canvas project is:

1. **project.ts** — declares scenes, fps, size, optional audio
2. **scene generator** — `function* (view) { ... }`
3. **nodes** — `Rect`, `Circle`, `Txt`, `Line`, `Code`, `Img`, layouts
4. **refs** — access nodes later with `createRef()` / `createRefArray()`
5. **signals** — reactive values you can read, set, and animate
6. **timeline flow** — `yield*`, `all()`, `sequence()`, `waitFor()`, `waitUntil()`

The key move is simple:

> Set up scene state, then drive properties over time with `yield*`.

## Bootstrap

Current scaffold route validated here:

```bash
npx @motion-canvas/create@latest
cd <project>
npm install
npm start
```

The create package currently exists as `@motion-canvas/create`; `npm view` on this machine reports it as “Quickly scaffold Motion Canvas projects”.

### CLI gotcha validated here

- `npx create-motion-canvas@latest` failed against the current npm mirror because that package name does not exist there.
- `npx @motion-canvas/create@latest` is the working package route.
- Calling `npx @motion-canvas/create@latest --help` on this machine still dropped into an interactive `Project name` prompt instead of printing normal help.

So for automation, do not assume a harmless `--help` or non-interactive probe. Treat the scaffold command as interactive unless you have re-verified the exact flags in a PTY.

Typical structure:

```text
project/
├── src/
│   ├── project.ts
│   └── scenes/
│       └── intro.tsx
├── package.json
└── vite.config.ts
```

## Authoring rules

### 1. One scene, one idea
If you are explaining a mechanism, do not jam five concepts into one scene. Motion Canvas is strong at staged reveals. Use that.

### 2. Start from the final visual story
Before coding, state:
- what appears first
- what changes next
- what the viewer should understand by the end of the scene

### 3. Prefer refs + named helpers over anonymous chaos
If a node will move later, give it a ref.
If an animation pattern repeats, wrap it in a generator helper.

### 4. Animate meaningfully
Do not animate everything just because you can. Use motion to direct attention.

### 5. Keep scenes composable
Short scenes with clean entrances/exits beat one giant timeline blob.

## Workflow

1. **Plan** — scene list, key beats, narration markers, visual hierarchy
2. **Scaffold** — create project, wire `project.ts`, create scene files
3. **Block** — place the main nodes with static layout first
4. **Animate** — add `yield*` timing, then parallel/stagger effects
5. **Sync** — use `waitUntil()` / duration markers if narration matters
6. **Preview** — iterate in the editor before worrying about final render
7. **Render** — export once timing and layout are stable

## Minimum working example

```tsx
import {makeScene2D, Circle} from '@motion-canvas/2d';
import {all, createRef} from '@motion-canvas/core';

export default makeScene2D(function* (view) {
  const circle = createRef<Circle>();

  view.add(
    <Circle
      ref={circle}
      size={180}
      fill={'#3b82f6'}
      opacity={0}
      scale={0.6}
    />,
  );

  yield* all(
    circle().opacity(1, 0.6),
    circle().scale(1, 0.6),
    circle().position.x(240, 1.2),
  );
});
```

This already shows the whole model:
- add a node to `view`
- store a ref
- animate properties over time with `yield*`

## High-value patterns

- **Sequential:** `yield* a(); yield* b();`
- **Parallel:** `yield* all(a(), b(), c())`
- **Staggered:** `yield* sequence(0.1, ...anims)`
- **Pause:** `yield* waitFor(0.5)`
- **Narration marker:** `yield* waitUntil('beat-name')`
- **Reactive value:** `const x = createSignal(0)` then `yield* x(100, 1)`
- **Code walkthrough:** use `Code` node and animate `selection()` / `code.replace()`

## Critical pitfalls

- `scene` imports need the `?scene` suffix in `project.ts`
- refs are functions: use `circle()` rather than `circle`
- node properties are signals; many can be read, set, or animated the same way
- if layout is still moving, do not polish easing yet
- if a scene feels muddy, split it rather than stacking more effects

## Deliverables

For real work, default to producing:
- project source
- at least one clean scene per concept
- a short README or notes with run/render commands
- exported preview or final render if requested

## References

Load these on demand:
- `references/core-concepts.md`
- `references/patterns.md`
- `references/selection-guide.md`
- `templates/scene-starter.tsx`
- `templates/project-starter.ts`
