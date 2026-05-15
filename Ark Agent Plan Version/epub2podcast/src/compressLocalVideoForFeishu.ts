import fs from 'fs';
import path from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

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

function getFfmpegPath(): string {
  const possiblePaths = ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg', '/usr/local/opt/ffmpeg/bin/ffmpeg'];
  for (const p of possiblePaths) if (fs.existsSync(p)) return p;
  return 'ffmpeg';
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const input = String(args['input'] || '');
  if (!input) throw new Error('Usage: node dist/compressLocalVideoForFeishu.js --input /path/to/final_podcast.mp4 [--output /path/to/final_podcast_feishu.mp4]');

  const inputPath = path.resolve(input);
  if (!fs.existsSync(inputPath)) throw new Error(`Input not found: ${inputPath}`);

  const outputPath = path.resolve(String(args['output'] || path.join(path.dirname(inputPath), `${path.parse(inputPath).name}_feishu${path.extname(inputPath) || '.mp4'}`)));
  const ffmpeg = getFfmpegPath();
  const ffmpegArgs = [
    '-y',
    '-i', inputPath,
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '27',
    '-maxrate', '2200k',
    '-bufsize', '4400k',
    '-c:a', 'aac',
    '-b:a', '96k',
    '-movflags', '+faststart',
    outputPath,
  ];

  await execFileAsync(ffmpeg, ffmpegArgs, { maxBuffer: 1024 * 1024 * 50 });

  const sizeBytes = fs.statSync(outputPath).size;
  console.log(JSON.stringify({
    inputPath,
    outputPath,
    sizeBytes,
    sizeMB: Number((sizeBytes / 1024 / 1024).toFixed(2)),
    target: 'Feishu drive +upload <= 20MB'
  }, null, 2));
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
