#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request

import yaml

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEFAULT_TEXT_MODEL = 'google/gemini-3.1-flash-lite-preview'
DEFAULT_IMAGE_MODEL = 'google/gemini-3.1-flash-image-preview'
DEFAULT_REFERER = 'https://hermes.aigc.green'
DEFAULT_TITLE = 'Hermes Article To WeChat Cover'
DEFAULT_PROVIDER_ORDER = ['Vertex AI']
DEFAULT_ASPECT_RATIO = '2.35:1'

FRONTMATTER_DELIMITER = '---'
DOC_TOKEN_RE = re.compile(r'/docx?/([A-Za-z0-9]+)')
TEXT_TAG_RE = re.compile(r'<text\b[^>]*>(.*?)</text>', re.S)
LARK_TABLE_RE = re.compile(r'<lark-table\b.*?</lark-table>', re.S)
IMAGE_RE = re.compile(r'<image\b[^>]*token="([^"]+)"[^>]*>')
QUOTE_RE = re.compile(r'<quote-container>(.*?)</quote-container>', re.S)
WS_RE = re.compile(r'\s+')
HR_RE = re.compile(r'(^|\n)(-{3,}|\*{3,}|_{3,})(\s*\n|$)', re.M)
H1_RE = re.compile(r'^#\s+(.+?)\s*$', re.M)
HEADING_RE = re.compile(r'^#{1,6}\s+(.+?)\s*$', re.M)
BULLET_RE = re.compile(r'^\s*[-*+]\s+', re.M)
ORDERED_RE = re.compile(r'^\s*\d+\.\s+', re.M)


@dataclass(slots=True)
class ArticleSource:
    title: str
    markdown: str
    source_url: str | None = None
    source_type: str = 'markdown'


def fail(message: str, code: int = 1) -> int:
    print(message, file=sys.stderr)
    return code


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip())


def extract_lark_doc_token(doc: str) -> str:
    text = doc.strip()
    if text.startswith(('http://', 'https://')):
        match = DOC_TOKEN_RE.search(text)
        if not match:
            raise ValueError(f'unsupported Lark doc URL: {doc}')
        return match.group(1)
    return text


def fetch_lark_doc(doc: str, *, identity: str = 'user') -> dict[str, Any]:
    completed = subprocess.run(
        ['lark-cli', 'docs', '+fetch', '--as', identity, '--doc', doc, '--format', 'json'],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or 'failed to fetch Lark doc')
    payload = json.loads(completed.stdout)
    data = payload.get('data') or {}
    return {
        'doc_id': data.get('doc_id') or extract_lark_doc_token(doc),
        'title': data.get('title', ''),
        'markdown': data.get('markdown', ''),
        'source_url': doc if doc.startswith(('http://', 'https://')) else None,
        'raw': payload,
    }


def _collapse_ws(text: str) -> str:
    return WS_RE.sub(' ', text).strip()


def _convert_text_tags(markdown: str) -> str:
    return TEXT_TAG_RE.sub(lambda m: _collapse_ws(m.group(1)), markdown)


def _convert_image_tags(markdown: str) -> str:
    return IMAGE_RE.sub(lambda m: f'![image](lark-image://{m.group(1)})', markdown)


def _convert_quote_containers(markdown: str) -> str:
    def replace_quote(match: re.Match[str]) -> str:
        content = match.group(1).strip()
        lines = content.split('\n')
        return '\n'.join(f'> {line}' if line.strip() else '>' for line in lines)
    return QUOTE_RE.sub(replace_quote, markdown)


def _convert_lark_table(table_markup: str) -> str:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(f'<root>{table_markup}</root>')
    table = root.find('lark-table')
    if table is None:
        return table_markup
    rows: list[list[str]] = []
    for tr in table.findall('lark-tr'):
        cells = []
        for td in tr.findall('lark-td'):
            cells.append(_collapse_ws(''.join(td.itertext())))
        if cells:
            rows.append(cells)
    if not rows:
        return ''
    width = max(len(row) for row in rows)
    normalized_rows = [row + [''] * (width - len(row)) for row in rows]
    def escape_cell(text: str) -> str:
        return text.replace('|', '\\|')
    lines = ['| ' + ' | '.join(escape_cell(cell) for cell in normalized_rows[0]) + ' |']
    lines.append('| ' + ' | '.join(['---'] * width) + ' |')
    for row in normalized_rows[1:]:
        lines.append('| ' + ' | '.join(escape_cell(cell) for cell in row) + ' |')
    return '\n'.join(lines)


def _convert_horizontal_rules(markdown: str) -> str:
    return HR_RE.sub('\n\n<hr />\n\n', markdown)


def normalize_lark_markdown(markdown: str) -> str:
    normalized = _convert_text_tags(markdown)
    normalized = _convert_quote_containers(normalized)
    normalized = _convert_image_tags(normalized)
    normalized = LARK_TABLE_RE.sub(lambda m: _convert_lark_table(m.group(0)), normalized)
    normalized = _convert_horizontal_rules(normalized)
    normalized = normalized.replace('\r\n', '\n')
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)
    return normalized.strip() + '\n'


def load_markdown_article(path: str) -> ArticleSource:
    raw = Path(path).read_text(encoding='utf-8')
    metadata: dict[str, Any] = {}
    body = raw
    if raw.startswith(f'{FRONTMATTER_DELIMITER}\n'):
        try:
            _, frontmatter, body = raw.split(FRONTMATTER_DELIMITER, 2)
            metadata = yaml.safe_load(frontmatter) or {}
            body = body.lstrip('\n')
        except ValueError:
            body = raw
    title = (metadata.get('title') or '').strip()
    if not title:
        match = H1_RE.search(body)
        if match:
            title = match.group(1).strip()
    if not title:
        title = Path(path).stem.replace('-', ' ').replace('_', ' ').strip() or 'Untitled Article'
    return ArticleSource(title=title, markdown=body.strip() + '\n', source_url=None, source_type='markdown')


def load_lark_doc_article(doc: str, *, identity: str = 'user') -> tuple[ArticleSource, dict[str, Any]]:
    doc_data = fetch_lark_doc(doc, identity=identity)
    markdown = normalize_lark_markdown(doc_data['markdown'])
    source = ArticleSource(
        title=(doc_data.get('title') or '').strip() or 'Untitled Feishu Doc',
        markdown=markdown,
        source_url=doc_data.get('source_url'),
        source_type='feishu-doc',
    )
    return source, doc_data


def markdown_to_plain_text(markdown: str) -> str:
    text = markdown
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'!\[[^\]]*\]\(([^)]+)\)', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)
    text = re.sub(r'^>+\s*', '', text, flags=re.M)
    text = BULLET_RE.sub('', text)
    text = ORDERED_RE.sub('', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'#{1,6}\s+', '', text)
    return _collapse_ws(text)


def extract_sections(markdown: str, limit: int = 8) -> list[str]:
    sections = []
    for match in HEADING_RE.finditer(markdown):
        heading = _collapse_ws(match.group(1))
        if heading:
            sections.append(heading)
        if len(sections) >= limit:
            break
    return sections


def clip_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + '…'


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def call_openrouter(*, api_key: str, payload: dict[str, Any], referer: str, title: str) -> dict[str, Any]:
    req = request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': referer,
            'X-Title': title,
        },
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode('utf-8', errors='replace'))
    except error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'OpenRouter HTTPError {e.code}: {body}') from e
    except error.URLError as e:
        raise RuntimeError(f'OpenRouter URLError: {e}') from e


def analyze_article_theme(
    *,
    article: ArticleSource,
    api_key: str,
    model: str,
    provider_order: list[str],
    referer: str,
    title: str,
    visual_style_hint: str | None,
    must_include: list[str],
    must_avoid: list[str],
    allow_text_overlay: bool,
) -> dict[str, Any]:
    plain_text = markdown_to_plain_text(article.markdown)
    sections = extract_sections(article.markdown)
    prompt = {
        'task': 'extract_wechat_cover_brief',
        'output_language': 'zh-CN',
        'rules': {
            'cover_aspect_ratio': DEFAULT_ASPECT_RATIO,
            'cover_should_reflect_article_core_theme': True,
            'cover_style_should_be_inferred_from_article_content_and_tone': True,
            'default_no_text_overlay': not allow_text_overlay,
            'avoid_literal_ui_screenshots': True,
            'avoid_generic_stock_image_feel': True,
        },
        'user_overrides': {
            'visual_style_hint': visual_style_hint or '',
            'must_include': must_include,
            'must_avoid': must_avoid,
        },
        'article': {
            'source_type': article.source_type,
            'title': article.title,
            'source_url': article.source_url or '',
            'sections': sections,
            'excerpt': clip_text(plain_text, 6000),
        },
        'response_json_schema': {
            'headline': '文章标题的简短重述',
            'core_theme': '文章核心主题',
            'reader_takeaway': '读者最强获得感',
            'tone': '如冷静、犀利、未来感、温暖、理性、硬核',
            'visual_direction': '一句话视觉方向',
            'subject': '主视觉主体',
            'scene': '具体场景描述',
            'composition': '适合2.35:1横幅的构图',
            'lighting': '光线建议',
            'palette': '配色建议',
            'style_keywords': ['最多6个风格关键词'],
            'must_include': ['必须出现的元素'],
            'must_avoid': ['必须避免的元素'],
            'text_overlay': '若默认不建议加字则返回空字符串',
        },
    }
    payload = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': (
                    '请根据下面 JSON 中的文章信息，提炼一个适合微信公众号封面图的视觉 brief。'
                    '必须输出合法 JSON，且严格遵守 response_json_schema 的字段。\n\n'
                    + json.dumps(prompt, ensure_ascii=False, indent=2)
                ),
            }
        ],
        'max_tokens': 2000,
        'provider': {'order': provider_order},
        'response_format': {'type': 'json_object'},
    }
    data = call_openrouter(api_key=api_key, payload=payload, referer=referer, title=title)
    content = data['choices'][0]['message']['content']
    try:
        brief = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f'Failed to parse theme analysis JSON: {content}') from e
    brief['_meta'] = {
        'model': data.get('model') or model,
        'provider': data.get('provider') or 'unknown',
        'usage': data.get('usage') or {},
    }
    return brief


def merge_unique(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for item in group:
            cleaned = item.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                merged.append(cleaned)
    return merged


def build_image_spec(
    *,
    article: ArticleSource,
    brief: dict[str, Any],
    allow_text_overlay: bool,
    must_include: list[str],
    must_avoid: list[str],
) -> dict[str, Any]:
    negative = merge_unique(
        ['watermark', 'logo', '二维码', 'UI screenshot', 'busy collage', 'tiny unreadable text', 'poster-like clutter'],
        brief.get('must_avoid') or [],
        must_avoid,
    )
    include = merge_unique(brief.get('must_include') or [], must_include)
    text_overlay = ''
    if allow_text_overlay:
        text_overlay = (brief.get('text_overlay') or '').strip()
    return {
        'task': 'generate_image',
        'model_intent': 'WeChat official account cover generated from article theme using Nano Banana structured prompt',
        'template': 'wechat-cover',
        'prompt_design_rules': {
            'describe_scene_not_keywords': True,
            'be_explicit_about_subject_style_composition_lighting': True,
            'prefer_semantic_negative_constraints': True,
            'preserve_visual_coherence': True,
            'single_final_image_only': True,
        },
        'article_context': {
            'title': article.title,
            'source_type': article.source_type,
            'source_url': article.source_url or '',
            'core_theme': brief.get('core_theme', ''),
            'tone': brief.get('tone', ''),
            'reader_takeaway': brief.get('reader_takeaway', ''),
        },
        'image_request': {
            'source_prompt': f'为微信公众号文章《{article.title}》生成封面图，主题为：{brief.get("core_theme", "")}',
            'subject': brief.get('subject', '') or article.title,
            'scene': brief.get('scene', '') or brief.get('visual_direction', ''),
            'style': ', '.join(brief.get('style_keywords') or []),
            'composition': brief.get('composition', '') or 'strong panoramic editorial composition with clear focal point and safe negative space',
            'lighting': brief.get('lighting', '') or 'clean cinematic lighting',
            'camera_language': 'wide panoramic banner framing suitable for WeChat article cover',
            'color_palette': brief.get('palette', ''),
            'text_rendering': text_overlay,
            'aspect_ratio': DEFAULT_ASPECT_RATIO,
            'quality_target': 'high',
            'negative_constraints': negative,
            'must_include': include,
            'must_avoid': negative,
            'reference_notes': (
                'The image must instantly communicate the article\'s core theme. '
                'It should look like a premium editorial WeChat cover, not a PowerPoint screenshot or generic stock banner. '
                'Leave tasteful breathing room for the WeChat cover layout.'
            ),
        },
        'output_contract': {
            'return': 'one finished image',
            'no_watermark': True,
            'no_unrequested_borders': True,
            'no_unrequested_extra_text': True,
        },
    }


def parse_image_from_message(message: dict[str, Any]) -> tuple[str, str]:
    mime_type = 'image/png'
    b64: str | None = None
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
            match = re.match(r'data:(image/[^;]+);base64,(.+)', url)
            if match:
                mime_type, b64 = match.groups()
        elif not b64 and len(url) > 1000 and re.match(r'^[A-Za-z0-9+/=]+$', url):
            b64 = url
    if not b64:
        content = message.get('content') or ''
        match = re.match(r'data:(image/[^;]+);base64,(.+)', content)
        if match:
            mime_type, b64 = match.groups()
        elif len(content) > 1000 and re.match(r'^[A-Za-z0-9+/=]+$', content):
            b64 = content
    if not b64:
        raise RuntimeError('No image data found in OpenRouter response')
    return mime_type, b64


def normalized_extension_for_mime(mime_type: str) -> str:
    return mimetypes.guess_extension(mime_type) or '.png'


def default_output_path(mime_type: str) -> Path:
    ext = normalized_extension_for_mime(mime_type)
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    return Path.cwd() / f'wechat-cover-{ts}{ext}'


def resolve_output_path(output: str | None, mime_type: str) -> Path:
    if not output:
        return default_output_path(mime_type)
    path = Path(output)
    correct_ext = normalized_extension_for_mime(mime_type)
    if not path.suffix:
        return path.with_suffix(correct_ext)
    if path.suffix.lower() != correct_ext.lower():
        return path.with_suffix(correct_ext)
    return path


def build_final_image_prompt(image_spec: dict[str, Any]) -> str:
    return (
        'Interpret the following JSON as the authoritative image specification. '
        'Generate exactly one image that follows it faithfully. '
        'If any field is empty, infer it conservatively from source_prompt.\n\n'
        + json.dumps(image_spec, ensure_ascii=False, indent=2)
    )


def generate_image(
    *,
    api_key: str,
    image_model: str,
    provider_order: list[str],
    referer: str,
    title: str,
    image_spec: dict[str, Any],
) -> tuple[dict[str, Any], bytes, str]:
    user_prompt = build_final_image_prompt(image_spec)
    payload = {
        'model': image_model,
        'messages': [{'role': 'user', 'content': user_prompt}],
        'max_tokens': 4096,
        'modalities': ['image', 'text'],
        'provider': {'order': provider_order},
    }
    data = call_openrouter(api_key=api_key, payload=payload, referer=referer, title=title)
    message = data['choices'][0]['message']
    mime_type, b64 = parse_image_from_message(message)
    return data, base64.b64decode(b64), mime_type


def upload_to_feishu(path: Path) -> tuple[str, str]:
    upload = subprocess.run(
        ['lark-cli', 'drive', '+upload', '--file', f'./{path.name}', '--name', path.name],
        cwd=path.parent,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(upload.stdout)
    token = payload['data']['file_token']
    query = subprocess.run(
        [
            'lark-cli', 'drive', 'metas', 'batch_query',
            '--data', json.dumps({'request_docs': [{'doc_token': token, 'doc_type': 'file'}], 'with_url': True}, ensure_ascii=False),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    meta_data = json.loads(query.stdout)
    url = meta_data['data']['metas'][0]['url']
    return token, url


def upload_cover_to_wechat(path: Path, *, appid: str, appsecret: str) -> str:
    sys.path.insert(0, str(Path.home() / '.hermes/skills/productivity/feishu-doc-to-wechat-draft/scripts'))
    from wechat_draft_publisher.wechat_api import WechatClient  # type: ignore

    client = WechatClient(appid=appid, appsecret=appsecret)
    access_token = client.get_access_token()
    return client.upload_cover_image(str(path), access_token)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Generate a 2.35:1 WeChat article cover from Feishu doc or Markdown using OpenRouter Nano Banana.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    def add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument('--output')
        sub.add_argument('--analysis-json')
        sub.add_argument('--dump-json-spec')
        sub.add_argument('--final-prompt-output')
        sub.add_argument('--confirm-generate', action='store_true', help='Confirm that the final prompt/spec has been reviewed and approved; without this flag the command stops before image generation')
        sub.add_argument('--text-model', default=os.getenv('OPENROUTER_TEXT') or DEFAULT_TEXT_MODEL)
        sub.add_argument('--image-model', default=os.getenv('OPENROUTER_IMAGE') or DEFAULT_IMAGE_MODEL)
        sub.add_argument('--provider-order', default=','.join(DEFAULT_PROVIDER_ORDER))
        sub.add_argument('--visual-style-hint')
        sub.add_argument('--must-include')
        sub.add_argument('--must-avoid')
        sub.add_argument('--allow-text-overlay', action='store_true')
        sub.add_argument('--referer', default=DEFAULT_REFERER)
        sub.add_argument('--title', default=DEFAULT_TITLE)
        sub.add_argument('--upload-feishu', action='store_true')
        sub.add_argument('--upload-wechat-cover', action='store_true')
        sub.add_argument('--appid', default=os.getenv('WECHAT_APP_ID'))
        sub.add_argument('--appsecret', default=os.getenv('WECHAT_APP_SECRET'))

    sub_doc = subparsers.add_parser('from-feishu-doc', help='Generate cover from Feishu/Lark doc URL or token')
    sub_doc.add_argument('--doc', required=True)
    sub_doc.add_argument('--identity', default='user', choices=['user', 'bot'])
    add_common(sub_doc)

    sub_md = subparsers.add_parser('from-markdown', help='Generate cover from local Markdown file')
    sub_md.add_argument('--input', required=True)
    add_common(sub_md)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_env_file(Path.home() / '.hermes/.env')
    parser = build_parser()
    args = parser.parse_args(argv)

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return fail('Missing OPENROUTER_API_KEY')

    provider_order = [item.strip() for item in args.provider_order.split(',') if item.strip()]
    must_include = split_csv(args.must_include)
    must_avoid = split_csv(args.must_avoid)

    try:
        if args.command == 'from-feishu-doc':
            article, _doc_meta = load_lark_doc_article(args.doc, identity=args.identity)
        else:
            article = load_markdown_article(args.input)

        brief = analyze_article_theme(
            article=article,
            api_key=api_key,
            model=args.text_model,
            provider_order=provider_order,
            referer=args.referer,
            title=args.title,
            visual_style_hint=args.visual_style_hint,
            must_include=must_include,
            must_avoid=must_avoid,
            allow_text_overlay=args.allow_text_overlay,
        )
        image_spec = build_image_spec(
            article=article,
            brief=brief,
            allow_text_overlay=args.allow_text_overlay,
            must_include=must_include,
            must_avoid=must_avoid,
        )

        final_prompt = build_final_image_prompt(image_spec)

        if args.analysis_json:
            path = Path(args.analysis_json)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding='utf-8')
        if args.dump_json_spec:
            path = Path(args.dump_json_spec)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(image_spec, ensure_ascii=False, indent=2), encoding='utf-8')
        if args.final_prompt_output:
            path = Path(args.final_prompt_output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(final_prompt, encoding='utf-8')

        print(f'article_title={article.title}')
        print(f'core_theme={brief.get("core_theme", "")}')
        print(f'visual_direction={brief.get("visual_direction", "")}')
        print(f'text_model={brief.get("_meta", {}).get("model", args.text_model)}')
        print(f'image_model={args.image_model}')
        print(f'aspect_ratio={DEFAULT_ASPECT_RATIO}')
        print('final_prompt_review_required=true')
        print('final_prompt_preview_begin')
        print(final_prompt)
        print('final_prompt_preview_end')
        if not args.confirm_generate:
            print('generation_skipped=pending_user_confirmation')
            if args.final_prompt_output:
                print(f'final_prompt_output={args.final_prompt_output}')
            else:
                print('hint=Use --final-prompt-output /tmp/final-prompt.txt to save the prompt, review it with the user, then rerun with --confirm-generate')
            return 0

        data, image_bytes, mime_type = generate_image(
            api_key=api_key,
            image_model=args.image_model,
            provider_order=provider_order,
            referer=args.referer,
            title=args.title,
            image_spec=image_spec,
        )

        requested_output = args.output
        output = resolve_output_path(requested_output, mime_type)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(image_bytes)

        print(f'output={output}')
        if requested_output and str(output) != requested_output:
            print(f'output_adjusted_from={requested_output}')
        print(f'bytes={len(image_bytes)}')
        print(f'mime_type={mime_type}')
        print(f'aspect_ratio={DEFAULT_ASPECT_RATIO}')
        print(f'article_title={article.title}')
        print(f'core_theme={brief.get("core_theme", "")}')
        print(f'visual_direction={brief.get("visual_direction", "")}')
        print(f'text_model={brief.get("_meta", {}).get("model", args.text_model)}')
        print(f'image_model={data.get("model") or args.image_model}')

        if args.upload_feishu:
            token, url = upload_to_feishu(output)
            print(f'feishu_token={token}')
            print(f'feishu_url={url}')

        if args.upload_wechat_cover:
            if not args.appid or not args.appsecret:
                return fail('WECHAT_APP_ID and WECHAT_APP_SECRET are required for --upload-wechat-cover', 2)
            media_id = upload_cover_to_wechat(output, appid=args.appid, appsecret=args.appsecret)
            print(f'thumb_media_id={media_id}')

        return 0
    except Exception as exc:
        return fail(str(exc), 2)


if __name__ == '__main__':
    raise SystemExit(main())
