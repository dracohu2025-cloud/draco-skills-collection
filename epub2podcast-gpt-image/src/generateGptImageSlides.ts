import * as dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { GptImageProvider } from './providers/image/gptImage.js';
import { generateGptImageSlides } from './services/gptImageSlideService.js';
import { renderVideoFromImages } from './services/localVideoRenderService.js';
import { ScriptSegment, SourceChapter } from './types.js';

dotenv.config({ path: path.resolve(process.cwd(), '.env') });

function parseArgs(argv: string[]): Record<string, string | boolean> {
  const args: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (!key.startsWith('--')) continue;
    const next = argv[i + 1];
    args[key.slice(2)] = !next || next.startsWith('--') ? true : next;
    if (next && !next.startsWith('--')) i++;
  }
  return args;
}

function fail(message: string): never {
  throw new Error(message);
}

function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8')) as T;
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const deliveryDir = path.resolve(String(args['delivery-dir'] || args['out-dir'] || ''));
  if (!deliveryDir || deliveryDir === process.cwd()) fail('Usage: node dist/generateGptImageSlides.js --delivery-dir /path/to/delivery [--recompose]');
  const metadataDir = path.join(deliveryDir, 'metadata');
  const scriptPath = path.join(metadataDir, 'script.json');
  const bookPath = path.join(metadataDir, 'book.json');
  if (!fs.existsSync(scriptPath)) fail(`script.json not found: ${scriptPath}`);
  if (!fs.existsSync(bookPath)) fail(`book.json not found: ${bookPath}`);

  const script = readJson<ScriptSegment[]>(scriptPath);
  const book = readJson<{ title?: string; chapters?: SourceChapter[] }>(bookPath);
  const bookTitle = String(args['book-title'] || book.title || 'Untitled Book');
  const language = String(args['language'] || 'Chinese');
  const imageDensity = String(args['image-density'] || 'segment') as 'segment' | 'chapter';
  const aspectRatio = String(args['aspect-ratio'] || '4:3');
  const targetResolution = String(args['resolution'] || '1440x1080');
  const maxRetries = Number(args['max-retries'] || 2);

  const result = await generateGptImageSlides({
    bookTitle,
    language,
    script,
    chapters: book.chapters || [],
    outDir: deliveryDir,
    imageProvider: new GptImageProvider(),
    imageDensity,
    aspectRatio,
    targetResolution,
    maxRetries,
  });

  fs.writeFileSync(scriptPath, JSON.stringify(script, null, 2), 'utf-8');

  const manifestPath = path.join(deliveryDir, 'manifest.json');
  const existingManifest = fs.existsSync(manifestPath) ? readJson<Record<string, unknown>>(manifestPath) : {};
  fs.writeFileSync(manifestPath, JSON.stringify({
    ...existingManifest,
    visualMode: 'gpt-image-slide',
    imageDensity,
    aspectRatio,
    resolution: targetResolution,
    visualOutput: result.manifest,
  }, null, 2), 'utf-8');

  let finalVideoPath: string | undefined;
  if (args['recompose'] === true) {
    const audioFile = path.join(deliveryDir, 'full_podcast.mp3');
    if (!fs.existsSync(audioFile)) fail(`full_podcast.mp3 not found: ${audioFile}`);
    const imageFiles = result.frames.map(frame => frame.imagePath);
    const durations = result.frames.map(frame => frame.segmentIndexes.reduce((sum, idx) => sum + (script[idx].estimatedDuration || 3), 0));
    finalVideoPath = path.join(deliveryDir, 'final_podcast.mp4');
    await renderVideoFromImages({ imageFiles, durations, audioFile, outputFile: finalVideoPath, targetResolution });
  }

  console.log(JSON.stringify({
    deliveryDir,
    frames: result.frames.length,
    slidesDir: path.join(deliveryDir, result.manifest.slidesDir),
    finalVideoPath,
  }, null, 2));
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
