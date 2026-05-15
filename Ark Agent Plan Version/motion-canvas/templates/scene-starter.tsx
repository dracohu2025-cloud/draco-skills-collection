import {Circle, Layout, Txt, makeScene2D} from '@motion-canvas/2d';
import {all, createRef, waitFor} from '@motion-canvas/core';

export default makeScene2D(function* (view) {
  const title = createRef<Txt>();
  const circle = createRef<Circle>();

  view.add(
    <Layout layout direction={'column'} gap={48} alignItems={'center'}>
      <Txt ref={title} text={'Scene Title'} fontSize={72} fill={'#f8fafc'} opacity={0} />
      <Circle ref={circle} size={180} fill={'#3b82f6'} opacity={0} scale={0.7} />
    </Layout>,
  );

  yield* all(
    title().opacity(1, 0.5),
    circle().opacity(1, 0.5),
    circle().scale(1, 0.5),
  );

  yield* waitFor(0.4);
  yield* circle().position.x(260, 1);
  yield* waitFor(0.3);
});
