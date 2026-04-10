#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SINGLE = SCRIPT_DIR / 'jimeng_image.py'


def fail(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def load_prompts(args):
    prompts = []
    if args.prompt:
        prompts.append(args.prompt.strip())
    if args.input:
        text = Path(args.input).read_text(encoding='utf-8')
        prompts.extend([x.strip() for x in text.split('\n\n') if x.strip()])
    stdin = sys.stdin.read().strip()
    if stdin:
        prompts.extend([x.strip() for x in stdin.split('\n\n') if x.strip()])
    prompts = [p for p in prompts if p]
    if not prompts:
        fail('No prompts provided. Use --prompt, --input, or stdin.')
    return prompts


def make_zip(target_dir: Path):
    archive_base = target_dir.parent / target_dir.name
    return Path(shutil.make_archive(str(archive_base), 'zip', root_dir=target_dir.parent, base_dir=target_dir.name))


def main():
    ap = argparse.ArgumentParser(description='Batch generate images with Jimeng / Seedream.')
    ap.add_argument('--prompt')
    ap.add_argument('--input')
    ap.add_argument('--outdir')
    ap.add_argument('--image', action='append', help='Reference image URL. Repeat for multiple references.')
    ap.add_argument('--model')
    ap.add_argument('--size', default='2k')
    ap.add_argument('--response-format', choices=['url', 'b64_json'], default='url')
    ap.add_argument('--sequential', choices=['disabled', 'auto'], default='disabled')
    ap.add_argument('--max-images', type=int)
    ap.add_argument('--watermark', dest='watermark', action='store_true')
    ap.add_argument('--no-watermark', dest='watermark', action='store_false')
    ap.add_argument('--zip', action='store_true')
    ap.set_defaults(watermark=True)
    args = ap.parse_args()

    prompts = load_prompts(args)
    outdir = Path(args.outdir) if args.outdir else Path.cwd() / f'jimeng-batch-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    outdir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for i, prompt in enumerate(prompts, start=1):
        item_dir = outdir / f'{i:03d}'
        item_dir.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(SINGLE), '--prompt', prompt, '--outdir', str(item_dir), '--size', args.size, '--response-format', args.response_format, '--sequential', args.sequential]
        if args.model:
            cmd += ['--model', args.model]
        if args.max_images:
            cmd += ['--max-images', str(args.max_images)]
        if not args.watermark:
            cmd.append('--no-watermark')
        for img in args.image or []:
            cmd += ['--image', img]
        subprocess.run(cmd, check=True)
        manifest.append({'index': i, 'dir': item_dir.name, 'prompt': prompt})

    manifest_obj = {
        'count': len(manifest),
        'size': args.size,
        'sequential': args.sequential,
        'max_images': args.max_images,
        'items': manifest,
    }
    zip_path = None
    if args.zip:
        zip_path = make_zip(outdir)
        manifest_obj['zip_file'] = zip_path.name
        print(f'zip={zip_path}')
    manifest_path = outdir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest_obj, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'outdir={outdir}')
    print(f'count={len(manifest)}')
    print(f'manifest={manifest_path}')


if __name__ == '__main__':
    main()
