import fs from 'fs';
import path from 'path';
import { jsonrepair } from 'jsonrepair';
import { ImageProvider, ImageUsageMetadata, AspectRatio } from '../providers/image/base.js';
import { ScriptSegment, SourceChapter } from '../types.js';
import { fitImageToFrame } from './localVideoRenderService.js';
import {
  EpisodeStyleBible,
  ImageDensity,
  ImageDesignSpec,
  ImageQaDecision,
  imageDesignerService,
  VisionQaObservation,
} from './imageDesignerService.js';

export interface GptImageSlideFrame {
  segmentIndex: number;
  segmentIndexes: number[];
  imagePath: string;
  rawPath: string;
  prompt: string;
  qa: ImageQaDecision;
  attempts: number;
  usageMetadata?: ImageUsageMetadata;
}

export interface GptImageSlideManifest {
  visualMode: 'gpt-image-slide';
  imageDensity: ImageDensity;
  slidesDir: string;
  rawDir: string;
  promptsFile: string;
  specsFile: string;
  qaFile: string;
  styleBibleFile: string;
  frames: Array<{
    segmentIndex: number;
    segmentIndexes: number[];
    image: string;
    raw: string;
    attempts: number;
    strategy: string;
    passedQa: boolean;
  }>;
}

export interface GptImageSlideResult {
  bible: EpisodeStyleBible;
  specs: ImageDesignSpec[];
  frames: GptImageSlideFrame[];
  manifest: GptImageSlideManifest;
}

export interface GenerateGptImageSlidesParams {
  bookTitle: string;
  language: string;
  script: ScriptSegment[];
  chapters?: SourceChapter[];
  outDir: string;
  imageProvider: ImageProvider;
  maxRetries?: number;
  imageDensity?: ImageDensity;
  aspectRatio?: string;
  targetResolution?: string;
  qaFrame?: (params: { imagePath: string; rawPath: string; spec: ImageDesignSpec; prompt: string; attempt: number }) => Promise<ImageQaDecision>;
  postProcessFrame?: (params: { rawPath: string; finalPath: string; spec: ImageDesignSpec }) => Promise<void>;
}

interface PromptRecord {
  segmentIndex: number;
  attempt: number;
  prompt: string;
}

interface QaRecord {
  segmentIndex: number;
  attempt: number;
  imagePath: string;
  passed: boolean;
  reason: string;
  retryForbiddenTexts: string[];
}

function ensureDir(dir: string): void {
  fs.mkdirSync(dir, { recursive: true });
}

function indexName(index: number): string {
  return String(index).padStart(3, '0');
}

function rel(base: string, filePath: string): string {
  return path.relative(base, filePath).replace(/\\/g, '/');
}

function listPngs(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(name => /^\d{3}\.png$/.test(name))
    .sort()
    .map(name => path.join(dir, name));
}

function normalizeAspectRatio(value: string): AspectRatio {
  const allowed: AspectRatio[] = ['1:1', '4:3', '16:9', '9:16', '3:4'];
  return allowed.includes(value as AspectRatio) ? value as AspectRatio : '4:3';
}

function extractJsonObject(text: string): string {
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end < start) throw new Error(`Vision QA did not return JSON: ${text.slice(0, 500)}`);
  return text.slice(start, end + 1);
}

function normalizeChatContent(content: unknown): string {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content.map(part => {
      if (typeof part === 'string') return part;
      if (part && typeof part === 'object' && 'text' in part) return String((part as { text: unknown }).text || '');
      return '';
    }).join('\n');
  }
  return String(content || '');
}

async function qaFrameWithOpenRouter(params: { imagePath: string; spec: ImageDesignSpec; prompt: string }): Promise<ImageQaDecision> {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) throw new Error('OPENROUTER_API_KEY is required for image QA in gpt-image-slide mode');

  const imageBase64 = fs.readFileSync(params.imagePath).toString('base64');
  const model = process.env.OPENROUTER_VISION || 'google/gemini-3-pro-preview';
  const qaPrompt = `You are a strict visual QA judge for a Chinese podcast image frame.
Return ONLY JSON matching this schema:
{
  "requiredTextPresent": ["exact required Chinese strings that are visible and correctly written"],
  "extraText": ["any extra visible words not allowed, including English"],
  "observedWrongTexts": ["misspelled or semantically substituted Chinese strings"],
  "isPptLike": false,
  "isVisuallyStriking": true,
  "isGrounded": true,
  "isLegible": true,
  "notes": "short note"
}

Required exact Chinese texts:
${params.spec.requiredText.map(text => `- ${text}`).join('\n')}

Segment excerpt:
${params.spec.sourceTextExcerpt}

Reject if any required text is missing/misspelled, if random English/logo/watermark appears, if it looks like a stiff PowerPoint slide, or if it is not grounded in the segment.`;

  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model,
      messages: [{
        role: 'user',
        content: [
          { type: 'text', text: qaPrompt },
          { type: 'image_url', image_url: { url: `data:image/png;base64,${imageBase64}` } },
        ],
      }],
      temperature: 0,
    }),
  });

  const responseText = await res.text();
  if (!res.ok) throw new Error(`OpenRouter vision QA failed: ${res.status} ${res.statusText} ${responseText.slice(0, 500)}`);
  const json = JSON.parse(responseText) as { choices?: Array<{ message?: { content?: unknown } }> };
  const content = normalizeChatContent(json.choices?.[0]?.message?.content);
  const repaired = jsonrepair(extractJsonObject(content));
  const observation = JSON.parse(repaired) as VisionQaObservation;
  return imageDesignerService.evaluateTextQa(params.spec, observation);
}

export function selectLocalSlideImages(outDir: string, expectedCount?: number): string[] {
  const gptImages = listPngs(path.join(outDir, 'gpt_image_slides'));
  if (gptImages.length && (!expectedCount || gptImages.length >= expectedCount)) return gptImages;
  const smartImages = listPngs(path.join(outDir, 'smart_slides'));
  if (smartImages.length && (!expectedCount || smartImages.length >= expectedCount)) return smartImages;
  return gptImages.length ? gptImages : smartImages;
}

export async function generateGptImageSlides(params: GenerateGptImageSlidesParams): Promise<GptImageSlideResult> {
  const imageDensity = params.imageDensity || 'segment';
  const targetResolution = params.targetResolution || '1440x1080';
  const aspectRatio = params.aspectRatio || '4:3';
  const providerAspectRatio = normalizeAspectRatio(aspectRatio);
  const maxRetries = params.maxRetries ?? 2;
  const metadataDir = path.join(params.outDir, 'metadata');
  const rawDir = path.join(params.outDir, 'gpt_image_raw');
  const slidesDir = path.join(params.outDir, 'gpt_image_slides');
  ensureDir(metadataDir);
  ensureDir(rawDir);
  ensureDir(slidesDir);

  const bible = imageDesignerService.createEpisodeStyleBible({
    bookTitle: params.bookTitle,
    language: params.language,
    chapters: params.chapters,
    aspectRatio,
    targetResolution,
  });
  const specs = imageDesignerService.designFrames({
    bookTitle: params.bookTitle,
    language: params.language,
    script: params.script,
    chapters: params.chapters,
    imageDensity,
    aspectRatio,
    targetResolution,
  });

  const promptRecords: PromptRecord[] = [];
  const qaRecords: QaRecord[] = [];
  const frames: GptImageSlideFrame[] = [];

  fs.writeFileSync(path.join(metadataDir, 'image_style_bible.json'), JSON.stringify(bible, null, 2), 'utf-8');
  fs.writeFileSync(path.join(metadataDir, 'image_design_specs.json'), JSON.stringify(specs, null, 2), 'utf-8');

  for (const spec of specs) {
    const finalPath = path.join(slidesDir, `${indexName(spec.segmentIndex)}.png`);
    let retryForbiddenTexts: string[] = [];
    let previousFailureReason = '';
    let accepted: GptImageSlideFrame | undefined;

    for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
      const prompt = imageDesignerService.buildPrompt(spec, bible, {
        attempt,
        forbiddenWrongTexts: retryForbiddenTexts,
        previousFailureReason,
      });
      promptRecords.push({ segmentIndex: spec.segmentIndex, attempt, prompt });

      const generated = await params.imageProvider.generateImage(prompt, { aspectRatio: providerAspectRatio });
      const rawPath = path.join(rawDir, `${indexName(spec.segmentIndex)}_attempt${attempt}.png`);
      fs.writeFileSync(rawPath, generated.buffer);

      const postProcess = params.postProcessFrame || (async ({ rawPath: input, finalPath: output }) => fitImageToFrame(input, output, targetResolution));
      await postProcess({ rawPath, finalPath, spec });

      const qa = params.qaFrame
        ? await params.qaFrame({ imagePath: finalPath, rawPath, spec, prompt, attempt })
        : await qaFrameWithOpenRouter({ imagePath: finalPath, spec, prompt });

      qaRecords.push({
        segmentIndex: spec.segmentIndex,
        attempt,
        imagePath: rel(params.outDir, finalPath),
        passed: qa.passed,
        reason: qa.reason,
        retryForbiddenTexts: qa.retryForbiddenTexts,
      });

      if (qa.passed) {
        for (const idx of spec.segmentIndexes) params.script[idx].generatedImageUrl = finalPath;
        accepted = {
          segmentIndex: spec.segmentIndex,
          segmentIndexes: spec.segmentIndexes,
          imagePath: finalPath,
          rawPath,
          prompt,
          qa,
          attempts: attempt,
          usageMetadata: generated.usageMetadata,
        };
        break;
      }

      retryForbiddenTexts = Array.from(new Set([...retryForbiddenTexts, ...qa.retryForbiddenTexts]));
      previousFailureReason = qa.reason;
    }

    if (!accepted) {
      throw new Error(`GPT image slide QA failed after ${maxRetries + 1} attempts for segment ${spec.segmentIndex}: ${previousFailureReason}`);
    }
    frames.push(accepted);
  }

  fs.writeFileSync(path.join(metadataDir, 'image_prompts.json'), JSON.stringify(promptRecords, null, 2), 'utf-8');
  fs.writeFileSync(path.join(metadataDir, 'image_qa.json'), JSON.stringify(qaRecords, null, 2), 'utf-8');

  const manifest: GptImageSlideManifest = {
    visualMode: 'gpt-image-slide',
    imageDensity,
    slidesDir: 'gpt_image_slides',
    rawDir: 'gpt_image_raw',
    promptsFile: 'metadata/image_prompts.json',
    specsFile: 'metadata/image_design_specs.json',
    qaFile: 'metadata/image_qa.json',
    styleBibleFile: 'metadata/image_style_bible.json',
    frames: frames.map(frame => {
      const spec = specs.find(item => item.segmentIndex === frame.segmentIndex);
      return {
        segmentIndex: frame.segmentIndex,
        segmentIndexes: frame.segmentIndexes,
        image: rel(params.outDir, frame.imagePath),
        raw: rel(params.outDir, frame.rawPath),
        attempts: frame.attempts,
        strategy: spec?.strategy || 'unknown',
        passedQa: frame.qa.passed,
      };
    }),
  };

  return { bible, specs, frames, manifest };
}
