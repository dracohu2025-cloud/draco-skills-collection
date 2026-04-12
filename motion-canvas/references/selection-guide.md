# When to Choose Motion Canvas

## Choose Motion Canvas when
- you want code-driven animation in TypeScript
- the output is an explainer, demo, product story, or staged visualization
- you want real-time preview while authoring
- narration timing matters
- you care about scene choreography more than pure frame-by-frame page rendering

## Prefer Manim when
- the core content is math, formulas, proofs, axes, geometry, derivations
- you want a stronger object-transformation teaching language
- Python is the natural authoring language

## Prefer Remotion when
- your team already lives in React
- the real problem is template video generation
- you want a component-driven content factory
- many videos share the same UI skeleton and data-binding model

## Fast heuristic
- **Teach a concept with animated objects** → Manim
- **Ship lots of React-shaped videos** → Remotion
- **Stage a code-driven scene performance in TS** → Motion Canvas

## Smell tests
If you keep asking “what should this screen look like at frame N?” you are drifting toward Remotion.
If you keep asking “what object is changing, and how?” you are drifting toward Manim.
If you keep asking “what is this scene doing over time?” Motion Canvas is probably the right tool.