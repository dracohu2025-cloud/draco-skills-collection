#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SINGLE = SCRIPT_DIR / 'jimeng_image.py'
BATCH = SCRIPT_DIR / 'jimeng_batch.py'
WORKFLOW = SCRIPT_DIR / 'jimeng_workflow.py'


def run(cmd):
    subprocess.run(cmd, check=True)


def add_shared_args(cmd, args):
    if args.model:
        cmd += ['--model', args.model]
    if getattr(args, 'size', None):
        cmd += ['--size', args.size]
    if getattr(args, 'response_format', None):
        cmd += ['--response-format', args.response_format]
    if getattr(args, 'sequential', None):
        cmd += ['--sequential', args.sequential]
    if getattr(args, 'max_images', None):
        cmd += ['--max-images', str(args.max_images)]
    if not args.watermark:
        cmd.append('--no-watermark')
    for img in getattr(args, 'image', []) or []:
        cmd += ['--image', img]
    return cmd


def main():
    ap = argparse.ArgumentParser(description='Unified Jimeng / Seedream image entrypoint: single, batch, workflow.')
    ap.add_argument('--mode', choices=['single', 'batch', 'workflow'], default='single')
    ap.add_argument('--prompt')
    ap.add_argument('--input')
    ap.add_argument('--body')
    ap.add_argument('--title')
    ap.add_argument('--output')
    ap.add_argument('--outdir')
    ap.add_argument('--output-dir')
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

    if args.mode == 'single':
        cmd = [sys.executable, str(SINGLE)]
        if args.prompt:
            cmd += ['--prompt', args.prompt]
        elif args.input:
            cmd += ['--input', args.input]
        if args.output:
            cmd += ['--output', args.output]
        if args.outdir:
            cmd += ['--outdir', args.outdir]
        cmd = add_shared_args(cmd, args)
        run(cmd)
        return

    if args.mode == 'batch':
        cmd = [sys.executable, str(BATCH)]
        if args.prompt:
            cmd += ['--prompt', args.prompt]
        elif args.input:
            cmd += ['--input', args.input]
        if args.outdir:
            cmd += ['--outdir', args.outdir]
        if args.zip:
            cmd.append('--zip')
        cmd = add_shared_args(cmd, args)
        run(cmd)
        return

    if args.mode == 'workflow':
        if not args.title:
            raise SystemExit('--mode workflow requires --title')
        outdir = args.output_dir or args.outdir
        if not outdir:
            raise SystemExit('--mode workflow requires --output-dir or --outdir')
        cmd = [sys.executable, str(WORKFLOW), '--title', args.title, '--output-dir', outdir]
        if args.body:
            cmd += ['--body', args.body]
        elif args.input:
            cmd += ['--input', args.input]
        if args.zip:
            cmd.append('--zip')
        cmd = add_shared_args(cmd, args)
        run(cmd)
        return


if __name__ == '__main__':
    main()
