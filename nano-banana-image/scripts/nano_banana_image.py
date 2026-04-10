#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib import request, error

DEFAULT_MODEL = 'google/gemini-3.1-flash-image-preview'
DEFAULT_REFERER = 'https://hermes.aigc.green'
DEFAULT_TITLE = 'Hermes Nano Banana'
PRESET_ASPECTS = {'1:1', '4:3', '16:9', '9:16', '3:4', '2:3', '3:2', '4:5', '5:4', '21:9'}
TEMPLATES = {
    'generic': {
        'style': '',
        'composition': '',
        'lighting': '',
        'palette': '',
        'negative': [],
    },
    'wechat-cover': {
        'style': 'clean editorial illustration or premium cover design',
        'composition': 'strong horizontal composition, clear focal point, headline-safe negative space, optimized for article cover readability',
        'lighting': 'clean cinematic lighting with clear subject separation',
        'palette': 'high-contrast brand-friendly palette with one dominant accent color',
        'negative': ['watermark', 'messy text', 'crowded layout', 'distorted hands', 'blurry subject'],
    },
    'product-hero': {
        'style': 'premium commercial product rendering or advertising photography',
        'composition': 'centered hero subject, premium spacing, polished foreground-background separation',
        'lighting': 'studio lighting, glossy highlights, controlled reflections',
        'palette': 'minimal luxury palette',
        'negative': ['watermark', 'cheap clutter', 'cropped product', 'extra objects'],
    },
    'poster': {
        'style': 'bold visual poster design',
        'composition': 'clear hierarchy, dramatic focal point, striking silhouette',
        'lighting': 'dramatic, cinematic, poster-like contrast',
        'palette': 'bold, memorable, poster-grade contrast palette',
        'negative': ['watermark', 'muddy colors', 'flat composition'],
    },
    'landing-hero': {
        'style': 'modern SaaS hero illustration or polished marketing key visual',
        'composition': 'wide hero composition, room for overlay text, visually clean structure',
        'lighting': 'soft premium lighting with modern tech atmosphere',
        'palette': 'modern product-friendly palette, tasteful gradients',
        'negative': ['watermark', 'busy background', 'awkward cropping', 'visual noise'],
    },
}


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


def parse_image_from_message(message: dict):
    mime_type = 'image/png'
    b64 = None
    images = message.get('images')
    if isinstance(images, list) and images:
        item = images[0]
        url = ''
        if isinstance(item, str):
            url = item
        elif isinstance(item, dict):
            url = ((item.get('image_url') or {}).get('url')) or item.get('url') or ''
            b64 = item.get('b64_json')
        if not b64 and url.startswith('data:image/'):
            m = re.match(r'data:(image/[^;]+);base64,(.+)', url)
            if m:
                mime_type, b64 = m.groups()
        elif not b64 and len(url) > 1000 and re.match(r'^[A-Za-z0-9+/=]+$', url):
            b64 = url
    if not b64:
        content = message.get('content') or ''
        m = re.match(r'data:(image/[^;]+);base64,(.+)', content)
        if m:
            mime_type, b64 = m.groups()
        elif len(content) > 1000 and re.match(r'^[A-Za-z0-9+/=]+$', content):
            b64 = content
    if not b64:
        raise ValueError('No image data found in response')
    return mime_type, b64


def default_output_path(mime_type: str) -> Path:
    ext = mimetypes.guess_extension(mime_type) or '.png'
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    return Path.cwd() / f'nano-banana-{ts}{ext}'


def upload_to_feishu(path: Path):
    cmd = ['lark-cli', 'drive', '+upload', '--file', f'./{path.name}', '--name', path.name]
    res = subprocess.run(cmd, cwd=path.parent, check=True, capture_output=True, text=True)
    data = json.loads(res.stdout)
    token = data['data']['file_token']
    q = [
        'lark-cli', 'drive', 'metas', 'batch_query',
        '--data', json.dumps({'request_docs': [{'doc_token': token, 'doc_type': 'file'}], 'with_url': True}, ensure_ascii=False)
    ]
    meta = subprocess.run(q, check=True, capture_output=True, text=True)
    meta_data = json.loads(meta.stdout)
    url = meta_data['data']['metas'][0]['url']
    return token, url


def split_csv(value: str):
    if not value:
        return []
    return [x.strip() for x in value.split(',') if x.strip()]


def validate_aspect_ratio(value: str) -> str:
    value = value.strip()
    if value in PRESET_ASPECTS:
        return value
    if re.fullmatch(r'\d+(?:\.\d+)?:\d+(?:\.\d+)?', value):
        left, right = value.split(':', 1)
        if float(left) > 0 and float(right) > 0:
            return value
    fail(f'Invalid --aspect-ratio: {value}. Use presets like 16:9 / 21:9 or custom ratios like 2.35:1')


def detect_template(prompt: str, explicit: str | None) -> str:
    if explicit and explicit != 'auto':
        return explicit
    p = prompt.lower()
    if '公众号' in prompt or 'wechat' in p or 'cover' in p or '封面' in prompt:
        return 'wechat-cover'
    if 'hero' in p or 'landing' in p or '头图' in prompt or '落地页' in prompt:
        return 'landing-hero'
    if 'product' in p or '产品' in prompt:
        return 'product-hero'
    if 'poster' in p or '海报' in prompt:
        return 'poster'
    return 'generic'


def parse_prompt_heuristically(prompt: str) -> dict:
    text = prompt.strip()
    parsed = {
        'subject': '',
        'scene': text,
        'style': '',
        'composition': '',
        'lighting': '',
        'camera': '',
        'palette': '',
        'negative': [],
        'must_include': [],
        'must_avoid': [],
        'reference_notes': '',
    }
    style_hits = []
    style_keywords = ['插画', 'illustration', 'cinematic', 'editorial', 'photography', '商业摄影', '极简', 'minimalist', 'cyberpunk', '3d', '海报']
    for kw in style_keywords:
        if kw.lower() in text.lower():
            style_hits.append(kw)
    if style_hits:
        parsed['style'] = ', '.join(style_hits)
    lighting_hits = []
    lighting_keywords = ['warm', '柔和', '晨光', 'moonlight', 'cinematic lighting', 'studio lighting', 'golden hour', '霓虹', 'neon']
    for kw in lighting_keywords:
        if kw.lower() in text.lower():
            lighting_hits.append(kw)
    if lighting_hits:
        parsed['lighting'] = ', '.join(lighting_hits)
    if any(k in text.lower() for k in ['close-up', '特写']):
        parsed['composition'] = 'close-up composition'
    elif any(k in text.lower() for k in ['wide', '全景', 'hero', '头图']):
        parsed['composition'] = 'wide composition with clear focal point'
    if '不要' in text:
        parsed['must_avoid'].append('respect explicit Chinese negative instructions in source prompt')
    subject = re.split(r'[，。,.;；!！?？]', text)[0].strip()
    parsed['subject'] = subject[:120]
    return parsed


def merge_lists(*lists):
    seen = set()
    out = []
    for lst in lists:
        for item in lst:
            if item and item not in seen:
                seen.add(item)
                out.append(item)
    return out


def build_json_spec(prompt: str, args) -> dict:
    parsed = parse_prompt_heuristically(prompt)
    template_name = detect_template(prompt, args.template)
    template = TEMPLATES.get(template_name, TEMPLATES['generic'])

    subject = args.subject or parsed['subject']
    scene = args.scene or parsed['scene']
    style = args.style or parsed['style'] or template.get('style', '')
    composition = args.composition or parsed['composition'] or template.get('composition', '')
    lighting = args.lighting or parsed['lighting'] or template.get('lighting', '')
    camera = args.camera or parsed['camera']
    palette = args.palette or parsed['palette'] or template.get('palette', '')
    negative = merge_lists(template.get('negative', []), parsed['negative'], split_csv(args.negative))
    must_include = merge_lists(parsed['must_include'], split_csv(args.must_include))
    must_avoid = merge_lists(parsed['must_avoid'], split_csv(args.must_avoid))
    reference_notes = args.reference_notes or parsed['reference_notes']

    return {
        'task': 'generate_image',
        'model_intent': 'Google Nano Banana / Gemini Flash Image structured prompt',
        'template': template_name,
        'prompt_design_rules': {
            'describe_scene_not_keywords': True,
            'be_explicit_about_subject_style_composition_lighting': True,
            'prefer_semantic_negative_constraints': True,
            'preserve_visual_coherence': True,
            'single_final_image_only': True,
        },
        'parser_output': parsed,
        'image_request': {
            'source_prompt': prompt,
            'subject': subject,
            'scene': scene,
            'style': style,
            'composition': composition,
            'lighting': lighting,
            'camera_language': camera,
            'color_palette': palette,
            'text_rendering': args.text_overlay or '',
            'aspect_ratio': args.aspect_ratio,
            'quality_target': args.quality,
            'negative_constraints': negative,
            'must_include': must_include,
            'must_avoid': must_avoid,
            'reference_notes': reference_notes,
        },
        'output_contract': {
            'return': 'one finished image',
            'no_watermark': True,
            'no_unrequested_borders': True,
            'no_unrequested_extra_text': True,
        },
    }


def build_json_prompt(prompt: str, args) -> str:
    spec = build_json_spec(prompt, args)
    return (
        'Interpret the following JSON as the authoritative image specification. '
        'Generate exactly one image that follows it faithfully. '
        'If any field is empty, infer it conservatively from source_prompt.\n\n'
        + json.dumps(spec, ensure_ascii=False, indent=2)
    )


def main():
    project_root = Path(__file__).resolve().parents[1]
    load_env_file(project_root / '.env')
    if Path.cwd() != project_root:
        load_env_file(Path.cwd() / '.env')

    ap = argparse.ArgumentParser(description='Generate an image using OpenRouter + Google Nano Banana style image model.')
    ap.add_argument('--prompt')
    ap.add_argument('--input')
    ap.add_argument('--output')
    ap.add_argument('--aspect-ratio', default='1:1')
    ap.add_argument('--model')
    ap.add_argument('--provider-order', default='Vertex AI')
    ap.add_argument('--upload-feishu', action='store_true')
    ap.add_argument('--title', default=DEFAULT_TITLE)
    ap.add_argument('--referer', default=DEFAULT_REFERER)
    ap.add_argument('--raw-prompt', action='store_true', help='Disable JSON wrapping and send original prompt directly')
    ap.add_argument('--template', choices=['auto', 'generic', 'wechat-cover', 'product-hero', 'poster', 'landing-hero'], default='auto')
    ap.add_argument('--subject')
    ap.add_argument('--scene')
    ap.add_argument('--style')
    ap.add_argument('--composition')
    ap.add_argument('--lighting')
    ap.add_argument('--camera')
    ap.add_argument('--palette')
    ap.add_argument('--text-overlay')
    ap.add_argument('--negative', help='Comma-separated negative constraints')
    ap.add_argument('--must-include', help='Comma-separated required visual elements')
    ap.add_argument('--must-avoid', help='Comma-separated forbidden visual elements')
    ap.add_argument('--reference-notes')
    ap.add_argument('--quality', default='high')
    ap.add_argument('--dump-json-spec', help='Write the generated JSON spec to this path')
    args = ap.parse_args()

    args.aspect_ratio = validate_aspect_ratio(args.aspect_ratio)
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        fail('Missing OPENROUTER_API_KEY')

    prompt = load_prompt(args)
    model = args.model or os.getenv('OPENROUTER_IMAGE') or DEFAULT_MODEL
    provider_order = [x.strip() for x in args.provider_order.split(',') if x.strip()]

    json_spec = None
    if args.raw_prompt:
        user_prompt = prompt
    else:
        json_spec = build_json_spec(prompt, args)
        user_prompt = (
            'Interpret the following JSON as the authoritative image specification. '
            'Generate exactly one image that follows it faithfully. '
            'If any field is empty, infer it conservatively from source_prompt.\n\n'
            + json.dumps(json_spec, ensure_ascii=False, indent=2)
        )
        if args.dump_json_spec:
            dump_path = Path(args.dump_json_spec)
            dump_path.parent.mkdir(parents=True, exist_ok=True)
            dump_path.write_text(json.dumps(json_spec, ensure_ascii=False, indent=2), encoding='utf-8')

    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': user_prompt}],
        'max_tokens': 4096,
        'modalities': ['image', 'text'],
        'provider': {'order': provider_order},
    }

    req = request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': args.referer,
            'X-Title': args.title,
        },
        method='POST'
    )

    try:
        with request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
    except error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        fail(f'HTTPError {e.code}: {body}', 2)
    except error.URLError as e:
        fail(f'URLError: {e}', 2)

    data = json.loads(raw)
    message = data['choices'][0]['message']
    mime_type, b64 = parse_image_from_message(message)
    image_bytes = base64.b64decode(b64)

    output = Path(args.output) if args.output else default_output_path(mime_type)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_bytes)

    print(f'output={output}')
    print(f'bytes={len(image_bytes)}')
    print(f'mime_type={mime_type}')
    print(f'model={data.get("model") or model}')
    print(f'provider={data.get("provider") or "unknown"}')
    print(f'json_prompt_mode={not args.raw_prompt}')
    if json_spec:
        print(f'json_template={json_spec.get("template")}')
    print(f'aspect_ratio={args.aspect_ratio}')

    if args.upload_feishu:
        token, url = upload_to_feishu(output)
        print(f'feishu_token={token}')
        print(f'feishu_url={url}')


if __name__ == '__main__':
    main()
