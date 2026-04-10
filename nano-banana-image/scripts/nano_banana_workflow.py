#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
import re

SCRIPT_DIR = Path(__file__).resolve().parent
BATCH = SCRIPT_DIR / 'nano_banana_batch.py'


def fail(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def sanitize(name: str) -> str:
    name = re.sub(r'\s+', '-', name.strip())
    name = re.sub(r'[^\w\-\u4e00-\u9fff]+', '-', name)
    name = re.sub(r'-{2,}', '-', name).strip('-')
    return name or 'nano-banana-job'


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
    ap = argparse.ArgumentParser(description='Structured Nano Banana workflow: title + prompt body + aspect ratio + output dir.')
    ap.add_argument('--title', required=True)
    ap.add_argument('--body')
    ap.add_argument('--input')
    ap.add_argument('--aspect-ratio', default='1:1')
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--model')
    ap.add_argument('--template', choices=['auto', 'generic', 'wechat-cover', 'product-hero', 'poster', 'landing-hero'], default='auto')
    ap.add_argument('--provider-order', default='Vertex AI')
    ap.add_argument('--zip', action='store_true')
    ap.add_argument('--upload-feishu', action='store_true')
    ap.add_argument('--raw-prompt', action='store_true')
    ap.add_argument('--subject')
    ap.add_argument('--scene')
    ap.add_argument('--style')
    ap.add_argument('--composition')
    ap.add_argument('--lighting')
    ap.add_argument('--camera')
    ap.add_argument('--palette')
    ap.add_argument('--text-overlay')
    ap.add_argument('--negative')
    ap.add_argument('--must-include')
    ap.add_argument('--must-avoid')
    ap.add_argument('--reference-notes')
    ap.add_argument('--quality', default='high')
    args = ap.parse_args()

    body = load_body(args)
    job_dir = Path(args.output_dir) / sanitize(args.title)
    job_dir.mkdir(parents=True, exist_ok=True)
    source = job_dir / 'prompts.txt'
    source.write_text(body, encoding='utf-8')

    cmd = [sys.executable, str(BATCH), '--input', str(source), '--outdir', str(job_dir / 'images'), '--aspect-ratio', args.aspect_ratio, '--provider-order', args.provider_order, '--quality', args.quality, '--template', args.template]
    if args.model:
        cmd += ['--model', args.model]
    if args.zip:
        cmd.append('--zip')
    if args.upload_feishu:
        cmd.append('--upload-feishu')
    if args.raw_prompt:
        cmd.append('--raw-prompt')
    for flag, value in [
        ('--subject', args.subject),
        ('--scene', args.scene),
        ('--style', args.style),
        ('--composition', args.composition),
        ('--lighting', args.lighting),
        ('--camera', args.camera),
        ('--palette', args.palette),
        ('--text-overlay', args.text_overlay),
        ('--negative', args.negative),
        ('--must-include', args.must_include),
        ('--must-avoid', args.must_avoid),
        ('--reference-notes', args.reference_notes),
    ]:
        if value:
            cmd += [flag, value]
    subprocess.run(cmd, check=True)

    job = {
        'title': args.title,
        'aspect_ratio': args.aspect_ratio,
        'source_file': source.name,
        'images_dir': 'images',
        'manifest': 'images/manifest.json',
        'zip': args.zip,
        'upload_feishu': args.upload_feishu,
        'json_prompt_mode': not args.raw_prompt,
        'template': args.template,
    }
    (job_dir / 'job.json').write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
    (job_dir / 'README.md').write_text(
        f'# {args.title}\n\n- aspect_ratio: {args.aspect_ratio}\n- source: {source.name}\n- images_dir: images/\n- manifest: images/manifest.json\n- zip: {args.zip}\n- upload_feishu: {args.upload_feishu}\n- json_prompt_mode: {not args.raw_prompt}\n- template: {args.template}\n',
        encoding='utf-8'
    )
    print(f'job_dir={job_dir}')
    print(f'images_dir={job_dir / "images"}')
    print(f'job_json={job_dir / "job.json"}')


if __name__ == '__main__':
    main()
