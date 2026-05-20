import fs from 'fs';
import path from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

function getFfmpegPath(): string {
  const possiblePaths = ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg', '/usr/local/opt/ffmpeg/bin/ffmpeg'];
  for (const p of possiblePaths) if (fs.existsSync(p)) return p;
  return 'ffmpeg';
}

function parseResolution(resolution: string): { width: number; height: number } {
  const match = String(resolution || '').match(/^(\d+)x(\d+)$/);
  if (!match) return { width: 1440, height: 1080 };
  return { width: Number(match[1]), height: Number(match[2]) };
}

function concatFileLine(baseDir: string, filePath: string): string {
  const rel = path.relative(baseDir, filePath).replace(/\\/g, '/');
  return `file '${rel.replace(/'/g, "'\\''")}'`;
}

export async function fitImageToFrame(inputPath: string, outputPath: string, targetResolution = '1440x1080'): Promise<void> {
  const { width, height } = parseResolution(targetResolution);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const ffmpeg = getFfmpegPath();
  const filter = [
    `[0:v]scale=${width}:${height}:force_original_aspect_ratio=increase,crop=${width}:${height},gblur=sigma=24[bg]`,
    `[0:v]scale=${width}:${height}:force_original_aspect_ratio=decrease[fg]`,
    `[bg][fg]overlay=(W-w)/2:(H-h)/2`,
  ].join(';');
  const args = [
    '-y',
    '-i', inputPath,
    '-filter_complex', filter,
    '-frames:v', '1',
    outputPath,
  ];
  await execFileAsync(ffmpeg, args, { maxBuffer: 1024 * 1024 * 20 });
}

export async function renderVideoFromImages(params: {
  imageFiles: string[];
  durations: number[];
  audioFile: string;
  outputFile: string;
  targetResolution?: string;
  fps?: number;
  audioBitrate?: string;
}): Promise<void> {
  const { imageFiles, durations, audioFile, outputFile } = params;
  if (!imageFiles.length) throw new Error('No images for video rendering');
  const { width, height } = parseResolution(params.targetResolution || '1440x1080');
  const fps = params.fps || 30;
  const tempDir = path.dirname(outputFile);
  fs.mkdirSync(tempDir, { recursive: true });
  const concatFile = path.join(tempDir, 'slides.txt');
  const lines: string[] = [];
  for (let i = 0; i < imageFiles.length; i++) {
    lines.push(concatFileLine(tempDir, imageFiles[i]));
    lines.push(`duration ${(durations[i] || 3).toFixed(3)}`);
  }
  lines.push(concatFileLine(tempDir, imageFiles[imageFiles.length - 1]));
  fs.writeFileSync(concatFile, lines.join('\n') + '\n', 'utf-8');

  const ffmpeg = getFfmpegPath();
  const args = [
    '-y',
    '-f', 'concat', '-safe', '0', '-i', concatFile,
    '-i', audioFile,
    '-vf', `scale=${width}:${height}:force_original_aspect_ratio=decrease,pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2:black`,
    '-r', String(fps),
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', params.audioBitrate || '192k',
    '-shortest',
    '-movflags', '+faststart',
    outputFile,
  ];
  await execFileAsync(ffmpeg, args, { cwd: tempDir, maxBuffer: 1024 * 1024 * 50 });
}
