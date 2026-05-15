import {makeProject} from '@motion-canvas/core';
import intro from './scenes/intro?scene';

export default makeProject({
  scenes: [intro],
  fps: 30,
  width: 1920,
  height: 1080,
});
