#!/usr/bin/env python3
import argparse
import subprocess
import sys

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SINGLE = SCRIPT_DIR / 'nano_banana_image.py'
BATCH = SCRIPT_DIR / 'nano_banana_batch.py'
WORKFLOW = SCRIPT_DIR / 'nano_banana_workflow.py'


def run(cmd):
    subprocess.run(cmd, check=True)


def add_shared_args(cmd, args):
    if args.model:
        cmd += ['--model', args.model]
    if getattr(args, 'template', None):
        cmd += ['--template', args.template]
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
        ('--quality', args.quality),
    ]:
        if value:
            cmd += [flag, value]
    return cmd


def main():
    ap = argparse.ArgumentParser(description='Unified Nano Banana image entrypoint: single, batch, workflow.')
    ap.add_argument('--mode', choices=['single', 'batch', 'workflow'], default='single')
    ap.add_argument('--prompt')
    ap.add_argument('--input')
    ap.add_argument('--body')
    ap.add_argument('--title')
    ap.add_argument('--output')
    ap.add_argument('--outdir')
    ap.add_argument('--output-dir')
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

    if args.mode == 'single':
        cmd = [sys.executable, str(SINGLE), '--aspect-ratio', args.aspect_ratio, '--provider-order', args.provider_order]
        if args.prompt:
            cmd += ['--prompt', args.prompt]
        elif args.input:
            cmd += ['--input', args.input]
        if args.output:
            cmd += ['--output', args.output]
        cmd = add_shared_args(cmd, args)
        run(cmd)
        return

    if args.mode == 'batch':
        cmd = [sys.executable, str(BATCH), '--aspect-ratio', args.aspect_ratio, '--provider-order', args.provider_order]
        if args.prompt:
            cmd += ['--prompt', args.prompt]
        elif args.input:
            cmd += ['--input', args.input]
        if args.outdir:
            cmd += ['--outdir', args.outdir]
        cmd = add_shared_args(cmd, args)
        run(cmd)
        return

    if args.mode == 'workflow':
        if not args.title:
            raise SystemExit('--mode workflow requires --title')
        outdir = args.output_dir or args.outdir
        if not outdir:
            raise SystemExit('--mode workflow requires --output-dir or --outdir')
        cmd = [sys.executable, str(WORKFLOW), '--title', args.title, '--output-dir', outdir, '--aspect-ratio', args.aspect_ratio, '--provider-order', args.provider_order]
        if args.body:
            cmd += ['--body', args.body]
        elif args.input:
            cmd += ['--input', args.input]
        cmd = add_shared_args(cmd, args)
        run(cmd)
        return


if __name__ == '__main__':
    main()
