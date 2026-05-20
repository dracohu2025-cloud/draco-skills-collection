import assert from 'node:assert/strict';
import { normalizeOpenRouterScriptResponse, validateGeneratedScript } from '../services/scriptService.js';
import type { ScriptSegment } from '../types.js';

function makeSegment(index: number): ScriptSegment {
  return {
    speaker: index % 2 === 0 ? 'Male' : 'Female',
    text: `测试段落 ${index}`,
    visualPrompt: `视觉提示 ${index}`,
  };
}

const sampleScript = Array.from({ length: 12 }, (_, index) => makeSegment(index));

assert.equal(
  normalizeOpenRouterScriptResponse(sampleScript),
  sampleScript,
  'top-level JSON array should be accepted unchanged',
);

assert.equal(
  normalizeOpenRouterScriptResponse({ script: sampleScript }),
  sampleScript,
  'object wrapper with script array should be unwrapped',
);

assert.equal(
  normalizeOpenRouterScriptResponse({ segments: sampleScript }),
  sampleScript,
  'object wrapper with segments array should be unwrapped',
);

assert.equal(
  normalizeOpenRouterScriptResponse({ podcastScript: sampleScript }),
  sampleScript,
  'object wrapper with podcastScript array should be unwrapped',
);

assert.throws(
  () => normalizeOpenRouterScriptResponse({ script: { nested: true } }),
  /expected array/i,
  'non-array wrappers should still fail loudly',
);

const healthyLongChineseText = '这是一个足够长的中文段落，用来模拟真实脚本质量门禁。它覆盖草原帝国的历史脉络、政治结构、军事动员和文化交换，确保每段都有足够信息密度。它还继续讨论阿提拉、成吉思汗与帖木儿之间的历史差异，避免把复杂材料切成空洞短句。并且补充游牧政权、绿洲贸易、宗教传播、军事组织和欧亚大陆秩序的互动关系。';
const eighteenSegmentScript = Array.from({ length: 18 }, (_, index) => ({
  ...makeSegment(index),
  text: `${healthyLongChineseText}${healthyLongChineseText}第 ${index} 段继续展开不同主题，避免过短。`,
}));
const validation = validateGeneratedScript(eighteenSegmentScript, 'Chinese', { preset: 'smart_ppt' });
assert.equal(
  validation.ok,
  true,
  `18-segment strict Chinese podcast script should pass when dialogue density is healthy: ${validation.reasons.join('; ')}`,
);

const nineteenSegmentScript = Array.from({ length: 19 }, (_, index) => ({
  ...makeSegment(index),
  text: `${healthyLongChineseText}${healthyLongChineseText}第 ${index} 段继续展开不同主题，保证总信息量。`,
}));
const overLimitValidation = validateGeneratedScript(nineteenSegmentScript, 'Chinese', { preset: 'smart_ppt' });
assert.equal(
  overLimitValidation.ok,
  false,
  'strict Chinese podcast script should reject more than 18 segments so GPT image count stays bounded',
);
assert.match(
  overLimitValidation.reasons.join('; '),
  /segment count 19 > maximum 18/,
);

console.log('scriptServiceResponseNormalization tests passed');
