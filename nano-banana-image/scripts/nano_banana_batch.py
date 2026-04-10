#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SINGLE = SCRIPT_DIR / 'nano_banana_image.py'


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


def upload_to_feishu(path: Path):
    cmd = ['lark-cli', 'drive', '+upload', '--file', f'./{path.name}', '--name', path.name]
    res = subprocess.run(cmd, cwd=path.parent, check=True, capture_output=True, text=True)
    data = json.loads(res.stdout)
    token = data['data']['file_token']
    q = ['lark-cli', 'drive', 'metas', 'batch_query', '--data', json.dumps({'request_docs': [{'doc_token': token, 'doc_type': 'file'}], 'with_url': True}, ensure_ascii=False)]
    meta = subprocess.run(q, check=True, capture_output=True, text=True)
    meta_data = json.loads(meta.stdout)
    return token, meta_data['data']['metas'][0]['url']


def append_shared_args(cmd, args):
    if args.model:
        cmd += ['--model', args.model]
    if getattr(args, 'template', None):
        cmd += ['--template', args.template]
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
        ('--quality', args.quality),
    ]:
        if value:
            cmd += [flag, value]
    return cmd


def main():
    ap = argparse.ArgumentParser(description='Batch generate images with Nano Banana style provider.')
    ap.add_argument('--prompt')
    ap.add_argument('--input')
    ap.add_argument('--outdir')
    ap.add_argument('--aspect-ratio', default='1:1')
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

    prompts = load_prompts(args)
    outdir = Path(args.outdir) if args.outdir else Path.cwd() / f'nano-banana-batch-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    outdir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for i, prompt in enumerate(prompts, start=1):
        outfile = outdir / f'{i:03d}.png'
        cmd = [sys.executable, str(SINGLE), '--prompt', prompt, '--output', str(outfile), '--aspect-ratio', args.aspect_ratio, '--provider-order', args.provider_order]
        cmd = append_shared_args(cmd, args)
        subprocess.run(cmd, check=True)
        manifest.append({'index': i, 'file': outfile.name, 'prompt': prompt})

    manifest_obj = {'count': len(manifest), 'aspect_ratio': args.aspect_ratio, 'json_prompt_mode': not args.raw_prompt, 'items': manifest}
    zip_path = None
    if args.zip:
        zip_path = make_zip(outdir)
        manifest_obj['zip_file'] = zip_path.name
        print(f'zip={zip_path}')

    manifest_path = outdir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest_obj, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.upload_feishu:
        target = zip_path or manifest_path
        token, url = upload_to_feishu(target)
        manifest_obj['feishu_file_token'] = token
        manifest_obj['feishu_url'] = url
        manifest_path.write_text(json.dumps(manifest_obj, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'feishu_token={token}')
        print(f'feishu_url={url}')

    print(f'outdir={outdir}')
    print(f'count={len(manifest)}')
    print(f'manifest={manifest_path}')


if __name__ == '__main__':
    main()
