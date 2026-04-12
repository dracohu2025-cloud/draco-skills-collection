# Motion Canvas Core Concepts

## 1. `makeProject`
The project file wires scenes, fps, dimensions, and optional audio.

```ts
import {makeProject} from '@motion-canvas/core';
import intro from './scenes/intro?scene';

export default makeProject({
  scenes: [intro],
  fps: 30,
  width: 1920,
  height: 1080,
});
```

### Important
- Scene imports need `?scene`
- This is where scene order lives
- Audio can be attached here for timeline sync

## 2. `makeScene2D`
A scene is a generator function.

```tsx
import {makeScene2D, Txt} from '@motion-canvas/2d';
import {waitFor} from '@motion-canvas/core';

export default makeScene2D(function* (view) {
  view.add(<Txt text={'Hello'} />);
  yield* waitFor(1);
});
```

Think of `yield*` as: advance the timeline while animating.

## 3. Refs
Use refs for nodes you need to animate later.

```tsx
const title = createRef<Txt>();
view.add(<Txt ref={title} text={'Hello'} />);
yield* title().opacity(1, 0.4);
```

Refs are called like functions: `title()`.

## 4. Signals
Signals are reactive values.

```ts
const count = createSignal(0);
yield* count(100, 1.2);
```

They can drive node props:

```tsx
const size = createSignal(80);
view.add(<Circle size={() => size()} />);
yield* size(180, 1);
```

## 5. Flow control
### Sequential
```ts
yield* first();
yield* second();
```

### Parallel
```ts
yield* all(node().x(200, 1), node().opacity(1, 1));
```

### Staggered
```ts
yield* sequence(0.1, ...items.map(item => item.opacity(1, 0.3)));
```

### Pause
```ts
yield* waitFor(0.5);
```

### Marker sync
```ts
yield* waitUntil('intro-finished');
```

## 6. Layout mindset
Motion Canvas is strong when you:
- block the scene first
- animate only the meaningful parts
- separate scenes by concept
- keep text readable and hierarchy obvious

If the viewer cannot tell what changed, the scene is badly staged.