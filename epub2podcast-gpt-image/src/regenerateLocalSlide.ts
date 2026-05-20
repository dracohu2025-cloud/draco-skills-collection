import * as dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import http from 'http';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { htmlImageService } from './services/htmlImageService.js';
import { DEFAULT_PPT_MODEL } from './constants.js';

const execFileAsync = promisify(execFile);
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

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

function ensureDir(dir: string) {
  fs.mkdirSync(dir, { recursive: true });
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

async function materializeLocalCover(coverImageBase64: string | undefined, outDir: string): Promise<string | undefined> {
  if (!coverImageBase64) return undefined;
  const matches = coverImageBase64.match(/^data:([^;]+);base64,(.+)$/);
  if (!matches) return undefined;
  const mimeType = matches[1];
  const base64Data = matches[2];
  const ext = mimeType.includes('png') ? 'png' : mimeType.includes('webp') ? 'webp' : 'jpg';
  const assetsDir = path.join(outDir, 'assets');
  ensureDir(assetsDir);
  const coverFilePath = path.join(assetsDir, `cover.${ext}`);
  fs.writeFileSync(coverFilePath, Buffer.from(base64Data, 'base64'));
  return coverFilePath;
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
  if (!address || typeof address === 'string') throw new Error('Failed to start local asset server');
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise<void>((resolve, reject) => server.close(err => err ? reject(err) : resolve())),
  };
}

async function recomposeVideo(outDir: string, script: any[]) {
  const slidesDir = path.join(outDir, 'smart_slides');
  const slideFiles = fs.readdirSync(slidesDir).filter(name => name.endsWith('.png')).sort();
  if (!slideFiles.length) throw new Error('No slide PNGs found');
  const concatPath = path.join(outDir, 'slides.txt');
  const lines: string[] = [];
  for (let i = 0; i < slideFiles.length; i++) {
    const duration = Number(script[i]?.estimatedDuration || 3);
    lines.push(`file 'smart_slides/${slideFiles[i]}'`);
    lines.push(`duration ${duration.toFixed(3)}`);
  }
  lines.push(`file 'smart_slides/${slideFiles[slideFiles.length - 1]}'`);
  fs.writeFileSync(concatPath, lines.join('\n') + '\n', 'utf8');

  const ffmpeg = getFfmpegPath();
  const audioPath = path.join(outDir, 'full_podcast.mp3');
  const videoPath = path.join(outDir, 'final_podcast.mp4');
  const args = [
    '-y',
    '-f', 'concat', '-safe', '0', '-i', concatPath,
    '-i', audioPath,
    '-vf', 'scale=1440:1080:force_original_aspect_ratio=decrease,pad=1440:1080:(ow-iw)/2:(oh-ih)/2:black',
    '-r', '30',
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-shortest',
    '-movflags', '+faststart',
    videoPath,
  ];
  await execFileAsync(ffmpeg, args, { cwd: outDir, maxBuffer: 1024 * 1024 * 50 });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const outDir = String(args['delivery-dir'] || args['out-dir'] || '');
  if (!outDir) throw new Error('Usage: node dist/regenerateLocalSlide.js --delivery-dir <dir> --slide-index <n> [--recompose] [--language Chinese] [--ppt-model model] [--color-theme theme]');
  const slideIndex = Number(args['slide-index'] ?? args['index'] ?? 0);
  if (!Number.isInteger(slideIndex) || slideIndex < 0) throw new Error('slide-index must be a non-negative integer');

  const book = JSON.parse(fs.readFileSync(path.join(outDir, 'metadata', 'book.json'), 'utf8'));
  const script = JSON.parse(fs.readFileSync(path.join(outDir, 'metadata', 'script.json'), 'utf8'));
  if (!Array.isArray(script) || !script.length) throw new Error('script.json is empty');
  if (slideIndex >= script.length) throw new Error(`slide-index ${slideIndex} out of range; script has ${script.length} segments`);

  const language = String(args['language'] || 'Chinese');
  const pptModel = String(args['ppt-model'] || DEFAULT_PPT_MODEL);
  const colorTheme = String(args['color-theme'] || 'gq_fashion');
  const coverFilePath = slideIndex === 0 ? await materializeLocalCover(book.coverImageBase64, outDir) : undefined;
  const assetServer = await startLocalAssetServer(outDir);

  try {
    const coverUrl = coverFilePath ? `${assetServer.baseUrl}/${path.relative(outDir, coverFilePath).replace(/\\/g, '/')}` : undefined;
    const prompt = htmlImageService.generateSmartPptPrompt(
      script[slideIndex]?.text || '',
      book.title,
      slideIndex,
      script.length,
      slideIndex === 0,
      language,
      slideIndex === 0 ? coverUrl : undefined,
    );

    const result = await htmlImageService.generateHtmlImage(prompt, pptModel, language, colorTheme);
    const paddedIndex = String(slideIndex).padStart(3, '0');
    const htmlPath = path.join(outDir, 'smart_slides_html', `${paddedIndex}.html`);
    const imagePath = path.join(outDir, 'smart_slides', `${paddedIndex}.png`);
    const htmlContent = coverUrl && coverFilePath
      ? result.htmlContent.replaceAll(coverUrl, path.relative(path.dirname(htmlPath), coverFilePath).replace(/\\/g, '/'))
      : result.htmlContent;

    fs.writeFileSync(htmlPath, htmlContent, 'utf8');
    fs.writeFileSync(imagePath, result.buffer);

    if (args['recompose']) {
      await recomposeVideo(outDir, script);
    }

    console.log(JSON.stringify({
      outDir,
      slideIndex,
      imagePath,
      htmlPath,
      recomposed: Boolean(args['recompose']),
      coverUrl: slideIndex === 0 ? coverUrl : undefined,
      model: pptModel,
      colorTheme,
    }, null, 2));
  } finally {
    await assetServer.close();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
