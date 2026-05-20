import assert from 'node:assert/strict';
import { imageDesignerService } from '../services/imageDesignerService.js';
import type { ScriptSegment, SourceChapter } from '../types.js';

const script: ScriptSegment[] = [
  { speaker: 'Male', text: '今天我们从一枚钱币讲起，它从贵霜腹地流动到东非修道院，背后是贸易、宗教和人的迁徙。', visualPrompt: null, estimatedDuration: 42 },
  { speaker: 'Female', text: '这只耳环更像一次谈判：审美、身份和权力在小小的金饰上互相拉扯。', visualPrompt: null, estimatedDuration: 38 },
  { speaker: 'Male', text: '最后回到全书，古物不是静止的证据，而是文明互相改写的现场。', visualPrompt: null, estimatedDuration: 35 }
];

const chapters: SourceChapter[] = [
  { title: '钱币与远行', content: '贵霜 钱币 东非 修道院 贸易 网络', order: 1 },
  { title: '耳环与谈判', content: '耳环 金饰 审美 身份 权力', order: 2 }
];

async function testBuildsGroundedSegmentSpecs() {
  const bible = imageDesignerService.createEpisodeStyleBible({
    bookTitle: '十件古物中的丝路文明史',
    language: 'Chinese',
    chapters,
  });
  assert.equal(bible.episodeTitle, '十件古物中的丝路文明史');
  assert.ok(bible.compositionRules.some(rule => rule.includes('4:3')));
  assert.ok(bible.avoid.includes('random English text'));

  const specs = imageDesignerService.designFrames({
    bookTitle: '十件古物中的丝路文明史',
    language: 'Chinese',
    script,
    chapters,
    imageDensity: 'segment',
    aspectRatio: '4:3',
    targetResolution: '1440x1080',
  });

  assert.equal(specs.length, script.length);
  assert.deepEqual(specs.map(s => s.segmentIndex), [0, 1, 2]);
  assert.equal(specs[0].strategy, 'map-timeline');
  assert.equal(specs[1].strategy, 'knowledge-comic');
  assert.equal(specs[2].strategy, 'closing-key-visual');
  for (const spec of specs) {
    assert.ok(spec.requiredText.length >= 2 && spec.requiredText.length <= 4);
    assert.ok(spec.sourceTextExcerpt.length > 20);
    assert.equal(spec.ratio, '4:3');
    assert.equal(spec.targetResolution, '1440x1080');
  }
}

async function testPromptForcesExactChineseTextAndBansPpt() {
  const bible = imageDesignerService.createEpisodeStyleBible({ bookTitle: '十件古物中的丝路文明史', language: 'Chinese', chapters });
  const [spec] = imageDesignerService.designFrames({
    bookTitle: '十件古物中的丝路文明史',
    language: 'Chinese',
    script,
    chapters,
    imageDensity: 'segment',
    aspectRatio: '4:3',
    targetResolution: '1440x1080',
  });

  const prompt = imageDesignerService.buildPrompt(spec, bible, {
    attempt: 2,
    forbiddenWrongTexts: ['东罗马道院'],
    previousFailureReason: 'subtitle text was misspelled',
  });

  assert.match(prompt, /Include ONLY these exact Simplified Chinese texts/);
  for (const text of spec.requiredText) assert.ok(prompt.includes(`「${text}」`));
  assert.ok(prompt.includes('东罗马道院'));
  assert.match(prompt, /NOT a PowerPoint slide/);
  assert.match(prompt, /no random English/i);
  assert.match(prompt, /1440x1080/);
}

async function testQaRejectsMissingRequiredTextAndExtraEnglish() {
  const spec = imageDesignerService.designFrames({
    bookTitle: '十件古物中的丝路文明史',
    language: 'Chinese',
    script: [script[0]],
    chapters,
    imageDensity: 'segment',
    aspectRatio: '4:3',
    targetResolution: '1440x1080',
  })[0];

  const failed = imageDesignerService.evaluateTextQa(spec, {
    requiredTextPresent: [spec.requiredText[0]],
    extraText: ['SILK ROAD'],
    observedWrongTexts: ['东罗马道院'],
    isPptLike: false,
    isVisuallyStriking: true,
    isGrounded: true,
    isLegible: true,
  });
  assert.equal(failed.passed, false);
  assert.ok(failed.retryForbiddenTexts.includes('东罗马道院'));
  assert.match(failed.reason, /missing/i);

  const passed = imageDesignerService.evaluateTextQa(spec, {
    requiredTextPresent: spec.requiredText,
    extraText: [],
    observedWrongTexts: [],
    isPptLike: false,
    isVisuallyStriking: true,
    isGrounded: true,
    isLegible: true,
  });
  assert.equal(passed.passed, true);
}

await testBuildsGroundedSegmentSpecs();
await testPromptForcesExactChineseTextAndBansPpt();
await testQaRejectsMissingRequiredTextAndExtraEnglish();
console.log('imageDesigner tests passed');
