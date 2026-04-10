#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib import request, error

API_URL = 'https://ark.cn-beijing.volces.com/api/v3/images/generations'
DEFAULT_MODEL = 'doubao-seedream-5-0-260128'


def fail(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def load_env_file(path: Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k, v)


def load_prompt(args) -> str:
    if args.prompt:
        return args.prompt.strip()
    if args.input:
        return Path(args.input).read_text(encoding='utf-8').strip()
    data = sys.stdin.read().strip()
    if data:
        return data
    fail('No prompt provided. Use --prompt, --input, or stdin.')


def normalize_size(value: str) -> str:
    raw = value.strip()
    lower = raw.lower()
    if lower in {'2k', '3k'}:
        return lower
    if re.fullmatch(r'\d+x\d+', lower):
        return lower
    fail("Invalid --size. Use 2k, 3k, or WIDTHxHEIGHT like 1344x768")


def resolve_api_key() -> str:
    return (
        os.getenv('VOLCENGINE_API_KEY')
        or os.getenv('SEEDREAM_API_KEY')
        or os.getenv('JIMENG_API_KEY')
        or ''
    )


def resolve_model(args) -> str:
    return (
        args.model
        or os.getenv('JIMENG_MODEL_NAME')
        or os.getenv('JIMENG_MODEL')
        or DEFAULT_MODEL
    )


def collect_reference_images(args):
    images = []
    for value in args.image or []:
        if value.startswith('http://') or value.startswith('https://'):
            images.append(value)
            continue
        fail(f'Reference image must be http/https URL for now: {value}')
    return images


def build_payload(prompt: str, args):
    images = collect_reference_images(args)
    payload = {
        'model': resolve_model(args),
        'prompt': prompt,
        'sequential_image_generation': args.sequential,
        'response_format': args.response_format,
        'size': normalize_size(args.size),
        'stream': False,
        'watermark': args.watermark,
    }
    if images:
        payload['image'] = images[0] if len(images) == 1 else images
    if args.sequential == 'auto' and args.max_images:
        payload['sequential_image_generation_options'] = {'max_images': args.max_images}
    return payload


def fetch_json(payload, api_key: str):
    req = request.Request(
        API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST'
    )
    try:
        with request.urlopen(req, timeout=420) as resp:
            return json.loads(resp.read().decode('utf-8', errors='replace'))
    except error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        fail(f'HTTPError {e.code}: {body}', 2)
    except error.URLError as e:
        fail(f'URLError: {e}', 2)


def default_file_name(idx: int, suffix: str = '.jpg') -> str:
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    return f'jimeng-{ts}-{idx:02d}{suffix}'


def download_url(url: str) -> tuple[bytes, str]:
    with request.urlopen(url, timeout=300) as resp:
        data = resp.read()
        ctype = resp.headers.get_content_type()
    ext = mimetypes.guess_extension(ctype) or '.jpg'
    return data, ext


def decode_b64(item: dict) -> tuple[bytes, str]:
    b64 = item.get('b64_json')
    if not b64:
        fail('Missing b64_json in response item', 2)
    return base64.b64decode(b64), '.png'


def save_images(data_items, args):
    if len(data_items) == 1:
        if args.output:
            target = Path(args.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            item = data_items[0]
            if 'url' in item:
                content, ext = download_url(item['url'])
            else:
                content, ext = decode_b64(item)
            if target.suffix == '':
                target = target.with_suffix(ext)
            target.write_bytes(content)
            return [target]

    outdir = Path(args.outdir) if args.outdir else Path.cwd() / f'jimeng-output-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for idx, item in enumerate(data_items, start=1):
        if 'url' in item:
            content, ext = download_url(item['url'])
        else:
            content, ext = decode_b64(item)
        target = outdir / default_file_name(idx, ext)
        target.write_bytes(content)
        paths.append(target)
    return paths


def main():
    project_root = Path(__file__).resolve().parents[1]
    load_env_file(project_root / '.env')
    if Path.cwd() != project_root:
        load_env_file(Path.cwd() / '.env')

    ap = argparse.ArgumentParser(description='Generate images with Jimeng / Doubao Seedream via Volcengine Ark.')
    ap.add_argument('--prompt')
    ap.add_argument('--input')
    ap.add_argument('--output')
    ap.add_argument('--outdir')
    ap.add_argument('--image', action='append', help='Reference image URL. Repeat for multiple references.')
    ap.add_argument('--model')
    ap.add_argument('--size', default='2k', help='2k, 3k, or WIDTHxHEIGHT like 1344x768')
    ap.add_argument('--response-format', choices=['url', 'b64_json'], default='url')
    ap.add_argument('--sequential', choices=['disabled', 'auto'], default='disabled')
    ap.add_argument('--max-images', type=int)
    ap.add_argument('--watermark', dest='watermark', action='store_true')
    ap.add_argument('--no-watermark', dest='watermark', action='store_false')
    ap.set_defaults(watermark=True)
    args = ap.parse_args()

    if args.max_images and args.max_images < 1:
        fail('--max-images must be >= 1')
    if args.sequential == 'disabled' and args.max_images:
        fail('--max-images requires --sequential auto')

    api_key = resolve_api_key()
    if not api_key:
        fail('Missing VOLCENGINE_API_KEY / SEEDREAM_API_KEY / JIMENG_API_KEY')

    prompt = load_prompt(args)
    payload = build_payload(prompt, args)
    response = fetch_json(payload, api_key)
    items = response.get('data') or []
    if not items:
        fail(f'No image data returned: {json.dumps(response, ensure_ascii=False)}', 2)

    paths = save_images(items, args)
    usage = response.get('usage') or {}

    print(f'model={response.get("model") or payload["model"]}')
    print(f'generated_images={len(items)}')
    print(f'size={payload["size"]}')
    print(f'sequential={payload["sequential_image_generation"]}')
    if 'generated_images' in usage:
        print(f'usage_generated_images={usage.get("generated_images")}')
    if 'total_tokens' in usage:
        print(f'usage_total_tokens={usage.get("total_tokens")}')
    for idx, path in enumerate(paths, start=1):
        print(f'output_{idx}={path}')
    print('response_json_begin')
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print('response_json_end')


if __name__ == '__main__':
    main()
