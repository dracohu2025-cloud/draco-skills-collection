#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BATCH = SCRIPT_DIR / 'jimeng_batch.py'


def fail(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def sanitize(name: str) -> str:
    name = re.sub(r'\s+', '-', name.strip())
    name = re.sub(r'[^\w\-\u4e00-\u9fff]+', '-', name)
    name = re.sub(r'-{2,}', '-', name).strip('-')
    return name or 'jimeng-job'


def load_body(args):
    if args.body:
        return args.body.strip()
    if args.input:
        return Path(args.input).read_text(encoding='utf-8').strip()
    data = sys.stdin.read().strip()
    if data:
        return data
    fail('No body provided. Use --body, --input, or stdin.')


def main():
    ap = argparse.ArgumentParser(description='Structured Jimeng workflow: title + prompt body + output dir.')
    ap.add_argument('--title', required=True)
    ap.add_argument('--body')
    ap.add_argument('--input')
    ap.add_argument('--output-dir', required=True)
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

    body = load_body(args)
    job_dir = Path(args.output_dir) / sanitize(args.title)
    job_dir.mkdir(parents=True, exist_ok=True)
    source = job_dir / 'prompts.txt'
    source.write_text(body, encoding='utf-8')

    cmd = [sys.executable, str(BATCH), '--input', str(source), '--outdir', str(job_dir / 'images'), '--size', args.size, '--response-format', args.response_format, '--sequential', args.sequential]
    if args.model:
        cmd += ['--model', args.model]
    if args.max_images:
        cmd += ['--max-images', str(args.max_images)]
    if args.zip:
        cmd.append('--zip')
    if not args.watermark:
        cmd.append('--no-watermark')
    for img in args.image or []:
        cmd += ['--image', img]
    subprocess.run(cmd, check=True)

    job = {
        'title': args.title,
        'size': args.size,
        'sequential': args.sequential,
        'max_images': args.max_images,
        'source_file': source.name,
        'images_dir': 'images',
        'manifest': 'images/manifest.json',
        'zip': args.zip,
        'watermark': args.watermark,
    }
    (job_dir / 'job.json').write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
    (job_dir / 'README.md').write_text(
        f'# {args.title}\n\n- size: {args.size}\n- sequential: {args.sequential}\n- max_images: {args.max_images}\n- source: {source.name}\n- images_dir: images/\n- manifest: images/manifest.json\n- zip: {args.zip}\n- watermark: {args.watermark}\n',
        encoding='utf-8'
    )
    print(f'job_dir={job_dir}')
    print(f'images_dir={job_dir / "images"}')
    print(f'job_json={job_dir / "job.json"}')


if __name__ == '__main__':
    main()
