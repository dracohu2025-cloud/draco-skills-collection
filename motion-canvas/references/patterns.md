# Motion Canvas Patterns

## Fade + slide in
```ts
export function* fadeSlideIn(node, duration = 0.6, dy = 80) {
  const y = node.position.y();
  node.opacity(0);
  node.position.y(y + dy);
  yield* all(
    node.opacity(1, duration),
    node.position.y(y, duration),
  );
}
```

## Pop in
```ts
export function* popIn(node, duration = 0.5) {
  node.scale(0.7);
  node.opacity(0);
  yield* all(
    node.scale(1, duration),
    node.opacity(1, duration * 0.8),
  );
}
```

## Parallel emphasis
Good for "show then highlight" beats.

```ts
yield* all(
  card().scale(1.05, 0.3),
  card().fill('#f59e0b', 0.3),
);
```

## Staggered list reveal
```ts
yield* sequence(
  0.08,
  ...items.map(item => all(item.opacity(1, 0.25), item.x(0, 0.25))),
);
```

## Counter / metric animation
```tsx
const value = createSignal(0);
view.add(<Txt text={() => `${Math.round(value())}%`} />);
yield* value(87, 1.4);
```

## Code walkthrough
```tsx
yield* code().selection(code().findFirstRange('binarySearch'), 0.4);
yield* code().code.replace(range, 'mid = left + right >> 1', 0.6);
```

## Scene decomposition rule
When a scene tries to do too much, split it like this:

1. static layout scene
2. single key change scene
3. comparison scene
4. summary scene

That rule is boring. It also works.

## Practical rhythm defaults
- micro emphasis: 0.2–0.3s
- reveal / move: 0.4–0.8s
- concept transition: 0.8–1.4s
- absorption pause: 0.3–0.8s

If everything takes 1 second, the piece feels robotic.
If everything is fast, the viewer learns nothing.