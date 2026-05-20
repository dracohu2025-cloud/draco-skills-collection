import * as dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';
import os from 'os';
import http from 'http';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { epubService } from './services/epubService.js';
import { scriptService } from './services/scriptService.js';
import { ttsService } from './services/ttsService.js';
import { audioService } from './services/audioService.js';
import { htmlImageService } from './services/htmlImageService.js';
import { ImageStyleConfig, ScriptSegment } from './types.js';
import { DEFAULT_PPT_MODEL, TTSProviderType } from './constants.js';
import { GptImageProvider } from './providers/image/gptImage.js';
import { generateGptImageSlides } from './services/gptImageSlideService.js';
import { renderVideoFromImages } from './services/localVideoRenderService.js';

const execFileAsync = promisify(execFile);
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

function fail(msg: string): never {
  throw new Error(msg);
}

function parseArgs(argv: string[]) {
  const args: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith('--')) {
      args[key] = true;
    } else {
      args[key] = next;
      i++;
    }
  }
  return args;
}

function ensureDir(p: string) {
  fs.mkdirSync(p, { recursive: true });
}

function chooseTtsProvider(language: string, override?: string): TTSProviderType {
  if (override) return override as TTSProviderType;
  return language === 'Chinese' ? 'volcengine' : 'minimax';
}

function normalizeSpeaker(raw: string): 'Male' | 'Female' {
  const s = String(raw || '').trim();
  if (s === 'Male' || s.includes('Male') || s === '阿哲' || s === 'Alex' || s.includes('哲')) return 'Male';
  return 'Female';
}

function resolveOpenRouterTextModel(textModel: string): string {
  if (textModel === 'gemini-3-flash') return 'deepseek/deepseek-v4-flash'; // legacy alias
  if (textModel === 'deepseek-v4-flash') return 'deepseek/deepseek-v4-flash';
  if (textModel.startsWith('gemini-')) return 'deepseek/deepseek-v4-flash';
  return textModel.includes('/') ? textModel : 'deepseek/deepseek-v4-flash';
}

function getFfmpegPath(): string {
  const possiblePaths = ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg', '/usr/local/opt/ffmpeg/bin/ffmpeg'];
  for (const p of possiblePaths) if (fs.existsSync(p)) return p;
  return 'ffmpeg';
}

function getMimeType(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case '.png': return 'image/png';
    case '.webp': return 'image/webp';
    case '.gif': return 'image/gif';
    case '.svg': return 'image/svg+xml';
    default: return 'image/jpeg';
  }
}

async function materializeLocalCover(
  coverImageBase64: string | undefined,
  outDir: string
): Promise<{ coverFilePath?: string; cleanup: () => Promise<void> }> {
  if (!coverImageBase64) {
    return { cleanup: async () => {} };
  }

  const matches = coverImageBase64.match(/^data:([^;]+);base64,(.+)$/);
  if (!matches) {
    console.warn('[LocalPipeline] Cover image data URL is invalid; skipping local cover materialization.');
    return { cleanup: async () => {} };
  }

  const mimeType = matches[1];
  const base64Data = matches[2];
  const extension = mimeType.includes('png') ? 'png' : mimeType.includes('webp') ? 'webp' : 'jpg';
  const assetsDir = path.join(outDir, 'assets');
  ensureDir(assetsDir);

  const coverFilePath = path.join(assetsDir, `cover.${extension}`);
  fs.writeFileSync(coverFilePath, Buffer.from(base64Data, 'base64'));
  console.log(`[LocalPipeline] Cover materialized locally: ${coverFilePath}`);

  return {
    coverFilePath,
    cleanup: async () => {}
  };
}

async function startLocalAssetServer(rootDir: string): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  const server = http.createServer((req, res) => {
    const reqUrl = req.url || '/';
    const pathname = decodeURIComponent(reqUrl.split('?')[0]);
    const normalized = path.posix.normalize(pathname).replace(/^\/+/g, '');
    const filePath = path.join(rootDir, normalized);

    const relative = path.relative(rootDir, filePath);
    if (relative.startsWith('..') || path.isAbsolute(relative) || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
      res.statusCode = 404;
      res.end('Not found');
      return;
    }

    res.statusCode = 200;
    res.setHeader('Content-Type', getMimeType(filePath));
    res.end(fs.readFileSync(filePath));
  });

  await new Promise<void>((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      server.off('error', reject);
      resolve();
    });
  });

  const address = server.address();
  if (!address || typeof address === 'string') {
    throw new Error('Failed to start local asset server');
  }

  const baseUrl = `http://127.0.0.1:${address.port}`;
  console.log(`[LocalPipeline] Local asset server started: ${baseUrl}`);

  return {
    baseUrl,
    close: () => new Promise<void>((resolve, reject) => {
      server.close(err => err ? reject(err) : resolve());
    })
  };
}

async function renderVideo(imageFiles: string[], durations: number[], audioFile: string, outputFile: string) {
  if (!imageFiles.length) fail('No images for video rendering');
  const tempDir = path.dirname(outputFile);
  const concatFile = path.join(tempDir, 'slides.txt');
  const rel = (p: string) => path.relative(tempDir, p).replace(/\\/g, '/');
  const lines: string[] = [];
  for (let i = 0; i < imageFiles.length; i++) {
    lines.push(`file '${rel(imageFiles[i])}'`);
    lines.push(`duration ${(durations[i] || 3).toFixed(3)}`);
  }
  lines.push(`file '${rel(imageFiles[imageFiles.length - 1])}'`);
  fs.writeFileSync(concatFile, lines.join('\n') + '\n', 'utf-8');

  const ffmpeg = getFfmpegPath();
  const args = [
    '-y',
    '-f', 'concat', '-safe', '0', '-i', concatFile,
    '-i', audioFile,
    '-vf', 'scale=1440:1080:force_original_aspect_ratio=decrease,pad=1440:1080:(ow-iw)/2:(oh-ih)/2:black',
    '-r', '30',
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-shortest',
    '-movflags', '+faststart',
    outputFile,
  ];
  await execFileAsync(ffmpeg, args, { cwd: tempDir, maxBuffer: 1024 * 1024 * 50 });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const input = String(args['epub'] || args['input'] || '');
  if (!input) fail('Usage: node dist/localPipeline.js --epub /path/to/book.epub [--output-dir dir]');
  const inputPath = path.resolve(input);
  if (!fs.existsSync(inputPath)) fail(`Input not found: ${inputPath}`);

  const outputRoot = path.resolve(String(args['output-dir'] || './local-deliveries'));
  const baseName = path.basename(inputPath).replace(/\.(epub|pdf|mobi|azw3)$/i, '').slice(0, 60);
  const jobId = `${Date.now()}`;
  const outDir = path.join(outputRoot, `${baseName}-${jobId}`);
  const sourceDir = path.join(outDir, 'source');
  const audioDir = path.join(outDir, 'audio_segments');
  const slidesDir = path.join(outDir, 'smart_slides');
  const htmlDir = path.join(outDir, 'smart_slides_html');
  const metadataDir = path.join(outDir, 'metadata');
  ensureDir(sourceDir); ensureDir(audioDir); ensureDir(slidesDir); ensureDir(htmlDir); ensureDir(metadataDir);
  fs.copyFileSync(inputPath, path.join(sourceDir, path.basename(inputPath)));

  const buffer = fs.readFileSync(inputPath);
  const parsed = await epubService.parseEpubStructured(buffer);
  const bookTitle = parsed.title || baseName;
  const language = String(args['language'] || 'Chinese');
  const imageStyle: ImageStyleConfig = {
    preset: 'smart_ppt',
    colorTheme: String(args['color-theme'] || 'gq_fashion'),
    pptModel: String(args['ppt-model'] || DEFAULT_PPT_MODEL),
  };
  const apiProvider = 'openrouter' as const;
  const ttsProvider = chooseTtsProvider(language, args['tts-provider'] as string | undefined);
  const textModel = String(args['text-model'] || 'deepseek-v4-flash');
  const visualMode = String(args['visual-mode'] || 'html-slide');
  const imageDensity = String(args['image-density'] || 'segment') as 'segment' | 'chapter';
  const aspectRatio = String(args['aspect-ratio'] || '4:3');
  const resolution = String(args['resolution'] || '1440x1080');
  const allowHtmlFallback = args['no-html-fallback'] !== true;
  process.env.OPENROUTER_TEXT = resolveOpenRouterTextModel(textModel);

  const localCover = await materializeLocalCover(parsed.coverImageBase64, outDir);
  const assetServer = await startLocalAssetServer(outDir);

  try {
    const coverImageUrl = localCover.coverFilePath
      ? `${assetServer.baseUrl}/${path.relative(outDir, localCover.coverFilePath).replace(/\\/g, '/')}`
      : undefined;

    const text = parsed.fullText;
    const scriptResult = await scriptService.generateScript(text, language, bookTitle, imageStyle, apiProvider, {
      chapters: parsed.chapters,
      totalWordCount: parsed.totalWordCount,
    });
    const script: ScriptSegment[] = scriptResult.script;

    const audioBuffers: Buffer[] = [];
    let cumulativeTime = 0;
    for (let i = 0; i < script.length; i++) {
      const seg = script[i];
      const speaker = normalizeSpeaker(seg.speaker);
      const { buffer: segAudio } = await ttsService.synthesizeSegment(seg.text, speaker, ttsProvider);
      const segPath = path.join(audioDir, `${String(i).padStart(3, '0')}.mp3`);
      fs.writeFileSync(segPath, segAudio);
      audioBuffers.push(segAudio);
      const dur = await audioService.getAudioDuration(segAudio);
      seg.startTime = cumulativeTime;
      seg.estimatedDuration = dur;
      seg.speaker = speaker;
      cumulativeTime += dur;
    }

    const finalAudioBuffer = await audioService.mergeAudio(audioBuffers);
    const finalAudioPath = path.join(outDir, 'full_podcast.mp3');
    fs.writeFileSync(finalAudioPath, finalAudioBuffer);
    const totalDuration = await audioService.getAudioDuration(finalAudioBuffer);

    const imageFiles: string[] = [];
    const durations: number[] = [];
    let visualOutputManifest: object | undefined;
    let effectiveVisualMode = visualMode;

    const renderHtmlSlides = async () => {
      effectiveVisualMode = 'html-slide';
      for (let i = 0; i < script.length; i++) {
        const seg = script[i];
        const prompt = htmlImageService.generateSmartPptPrompt(
          seg.text || '',
          bookTitle,
          i,
          script.length,
          i === 0,
          language,
          i === 0 ? coverImageUrl : undefined,
        );
        const result = await htmlImageService.generateHtmlImage(
          prompt,
          imageStyle.pptModel || DEFAULT_PPT_MODEL,
          language,
          imageStyle.colorTheme || 'gq_fashion',
        );
        const imgPath = path.join(slidesDir, `${String(i).padStart(3, '0')}.png`);
        const htmlPath = path.join(htmlDir, `${String(i).padStart(3, '0')}.html`);
        fs.writeFileSync(imgPath, result.buffer);
        fs.writeFileSync(htmlPath, result.htmlContent, 'utf-8');
        seg.generatedImageUrl = imgPath;
        (seg as any).htmlUrl = htmlPath;
        imageFiles.push(imgPath);
        durations.push(seg.estimatedDuration || 3);
      }
      visualOutputManifest = { visualMode: 'html-slide', slidesDir: 'smart_slides', htmlDir: 'smart_slides_html' };
    };

    if (visualMode === 'gpt-image-slide') {
      try {
        const gptResult = await generateGptImageSlides({
          bookTitle,
          language,
          script,
          chapters: parsed.chapters,
          outDir,
          imageProvider: new GptImageProvider(),
          imageDensity,
          aspectRatio,
          targetResolution: resolution,
        });
        for (const frame of gptResult.frames) {
          imageFiles.push(frame.imagePath);
          durations.push(frame.segmentIndexes.reduce((sum, idx) => sum + (script[idx].estimatedDuration || 3), 0));
        }
        visualOutputManifest = gptResult.manifest;
        effectiveVisualMode = 'gpt-image-slide';
      } catch (err) {
        if (!allowHtmlFallback) throw err;
        console.warn('[LocalPipeline] GPT image slide mode failed; falling back to html-slide:', err);
        await renderHtmlSlides();
      }
    } else {
      await renderHtmlSlides();
    }

    const finalVideoPath = path.join(outDir, 'final_podcast.mp4');
    await renderVideoFromImages({ imageFiles, durations, audioFile: finalAudioPath, outputFile: finalVideoPath, targetResolution: resolution });

    const marketing = await scriptService.generateMarketingContent(bookTitle, script, language, imageStyle, apiProvider);

    const manifest = {
      title: bookTitle,
      language,
      imageStyle,
      apiProvider,
      textModel,
      ttsProvider,
      totalDuration,
      scriptSegments: script.length,
      visualMode: effectiveVisualMode,
      imageDensity,
      aspectRatio,
      resolution,
      visualOutput: visualOutputManifest,
      output: {
        source: path.relative(outDir, path.join(sourceDir, path.basename(inputPath))),
        audio: 'full_podcast.mp3',
        video: 'final_podcast.mp4',
        slidesDir: effectiveVisualMode === 'gpt-image-slide' && (visualOutputManifest as any)?.slidesDir === 'gpt_image_slides' ? 'gpt_image_slides' : 'smart_slides',
        rawSlidesDir: (visualOutputManifest as any)?.rawDir,
        htmlDir: 'smart_slides_html',
        metadataDir: 'metadata',
        cover: localCover.coverFilePath ? path.relative(outDir, localCover.coverFilePath) : undefined,
      }
    };

    fs.writeFileSync(path.join(metadataDir, 'book.json'), JSON.stringify(parsed, null, 2), 'utf-8');
    fs.writeFileSync(path.join(metadataDir, 'script.json'), JSON.stringify(script, null, 2), 'utf-8');
    fs.writeFileSync(path.join(metadataDir, 'marketing.json'), JSON.stringify(marketing, null, 2), 'utf-8');
    fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf-8');

    console.log(JSON.stringify({ outDir, finalAudioPath, finalVideoPath, scriptSegments: script.length, totalDuration, coverImageUrl }, null, 2));
  } finally {
    await assetServer.close();
    await localCover.cleanup();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
