import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { generateGptImageSlides, selectLocalSlideImages } from '../services/gptImageSlideService.js';
import type { ImageGenerationOptions, ImageProvider } from '../providers/image/base.js';
import type { ScriptSegment } from '../types.js';

const PNG_1X1 = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
  0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
  0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
  0x08, 0x04, 0x00, 0x00, 0x00, 0xb5, 0x1c, 0x0c,
  0x02, 0x00, 0x00, 0x00, 0x0b, 0x49, 0x44, 0x41,
  0x54, 0x78, 0xda, 0x63, 0xfc, 0xff, 0x1f, 0x00,
  0x03, 0x03, 0x02, 0x00, 0xef, 0xbf, 0xa7, 0xdb,
  0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, 0x44,
  0xae, 0x42, 0x60, 0x82,
]);

class FakeImageProvider implements ImageProvider {
  prompts: string[] = [];
  options: ImageGenerationOptions[] = [];
  async generateImage(prompt: string, options: ImageGenerationOptions = {}) {
    this.prompts.push(prompt);
    this.options.push(options);
    return {
      buffer: PNG_1X1,
      usageMetadata: { model: 'fake-gpt-image-2', provider: 'fake', inputTokens: 1, outputTokens: 1, totalTokens: 2, costUSD: 0.01 },
    };
  }
}

const script: ScriptSegment[] = [
  { speaker: 'Male', text: '一枚钱币从贵霜腹地走向远方，贸易网络把城市、宗教和人的命运连起来。', visualPrompt: null, estimatedDuration: 12 },
  { speaker: 'Female', text: '一只耳环像一次谈判，审美、身份与权力在金饰上留下痕迹。', visualPrompt: null, estimatedDuration: 10 }
];

async function testGeneratorPersistsSpecsPromptsQaAndRetries() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gpt-image-slides-test-'));
  const provider = new FakeImageProvider();
  let qaCalls = 0;

  const result = await generateGptImageSlides({
    bookTitle: '十件古物中的丝路文明史',
    language: 'Chinese',
    script,
    chapters: [],
    outDir: tmp,
    imageProvider: provider,
    maxRetries: 2,
    imageDensity: 'segment',
    aspectRatio: '16:9',
    targetResolution: '1920x1080',
    postProcessFrame: async ({ rawPath, finalPath }) => fs.copyFileSync(rawPath, finalPath),
    qaFrame: async ({ spec }) => {
      qaCalls += 1;
      if (spec.segmentIndex === 0 && qaCalls === 1) {
        return { passed: false, reason: 'missing required text', retryForbiddenTexts: ['东罗马道院'] };
      }
      return { passed: true, reason: 'ok', retryForbiddenTexts: [] };
    },
  });

  assert.equal(result.frames.length, 2);
  assert.equal(provider.prompts.length, 3, 'first frame should retry once');
  assert.deepEqual(provider.options.map(options => options.aspectRatio), ['16:9', '16:9', '16:9']);
  assert.ok(provider.prompts[0].includes('1920x1080'), 'prompt should include requested target resolution');
  assert.ok(provider.prompts[1].includes('东罗马道院'), 'retry prompt should include forbidden wrong text');
  assert.ok(fs.existsSync(path.join(tmp, 'metadata', 'image_style_bible.json')));
  assert.ok(fs.existsSync(path.join(tmp, 'metadata', 'image_design_specs.json')));
  assert.ok(fs.existsSync(path.join(tmp, 'metadata', 'image_prompts.json')));
  assert.ok(fs.existsSync(path.join(tmp, 'metadata', 'image_qa.json')));
  assert.ok(fs.existsSync(path.join(tmp, 'gpt_image_raw', '000_attempt2.png')));
  assert.ok(fs.existsSync(path.join(tmp, 'gpt_image_slides', '000.png')));
  assert.equal(script[0].generatedImageUrl, path.join(tmp, 'gpt_image_slides', '000.png'));
  assert.equal(result.manifest.slidesDir, 'gpt_image_slides');
  assert.equal(result.manifest.rawDir, 'gpt_image_raw');
}

async function testSelectLocalSlideImagesPrefersGptSlidesAndFallsBack() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'slide-select-test-'));
  const smart = path.join(tmp, 'smart_slides');
  const gpt = path.join(tmp, 'gpt_image_slides');
  fs.mkdirSync(smart, { recursive: true });
  fs.mkdirSync(gpt, { recursive: true });
  fs.writeFileSync(path.join(smart, '000.png'), PNG_1X1);
  fs.writeFileSync(path.join(gpt, '000.png'), PNG_1X1);
  fs.writeFileSync(path.join(gpt, '001.png'), PNG_1X1);

  const selected = selectLocalSlideImages(tmp, 2);
  assert.deepEqual(selected.map(p => path.relative(tmp, p)), ['gpt_image_slides/000.png', 'gpt_image_slides/001.png']);

  fs.rmSync(gpt, { recursive: true, force: true });
  const fallback = selectLocalSlideImages(tmp, 1);
  assert.deepEqual(fallback.map(p => path.relative(tmp, p)), ['smart_slides/000.png']);
}

await testGeneratorPersistsSpecsPromptsQaAndRetries();
await testSelectLocalSlideImagesPrefersGptSlidesAndFallsBack();
console.log('gptImageSlideService tests passed');
