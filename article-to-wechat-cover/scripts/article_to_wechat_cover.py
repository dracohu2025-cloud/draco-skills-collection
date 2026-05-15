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
import tempfile
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
DEFAULT_COVER_BROTH = (
    '先理解推荐对象为什么值得被看见，再把复杂信息收束为一个清晰、有力、耐看的封面理由；'
    '手机端 3 秒可读，信息少而准，主视觉来自对象本身的气质，保持高级、可信、克制。'
)

COVER_SEASONING_RECIPES: dict[str, dict[str, str]] = {
    'architectural-blueprint': {
        'name': '建筑图纸美学',
        'seasoning': '空间秩序、中轴网格、细密注释、冷静极简、工程感字体、结构化插画、石墨灰强调色',
    },
    'tech-morandi': {
        'name': '科技莫兰迪',
        'seasoning': '科技美学、居中排版、小字点缀、极简黑体、柔和渐变、莫兰迪配色、韩系几何背景',
    },
    'power-editorial': {
        'name': '力量编辑感',
        'seasoning': '力量美学、强情绪、居中标题、多层小字、暗色渐变、艺术化字体、象征插画',
    },
    'oriental-literati': {
        'name': '东方文人',
        'seasoning': '留白意境、居中章法、印章式点缀、书卷感、水墨抽象、朱砂红强调、题跋式克制',
    },
    'cinematic-title': {
        'name': '电影片头',
        'seasoning': '电影片头美学、叙事情绪、宽银幕、若隐若现的小字线索、克制神秘、暗金强调色',
    },
    'garden-journal': {
        'name': '园艺手账',
        'seasoning': '松弛生活感、中心标题、日期天气标注、手写感、温柔极简、鼠尾草绿、安静日记感',
    },
    'healing-line-art': {
        'name': '治愈线条',
        'seasoning': '线条艺术、圆体、治愈系配色、柔和渐变、干净留白、轻盈插画',
    },
    'product-manual': {
        'name': '产品手册',
        'seasoning': '产品手册美学、清晰结构、中心排版、多层注释、蓝色强调、理性插画、可解释感',
    },
    'art-exhibition': {
        'name': '艺术展览',
        'seasoning': '诗性留白、展墙说明、碎片化小字、克制高级、抽象插画、慢镜头氛围、雾紫强调色',
    },
    'variety-trailer': {
        'name': '综艺预告',
        'seasoning': '轻松好笑、爆梗排版、贴纸小字、明亮极简、圆润字体、夸张表情、柠檬黄强调色',
    },
}

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
IMAGE_TAG_RE = re.compile(r'<image\b[^>]*?/?>')
LEADING_IMAGE_TAG_RE = re.compile(r'^(?:\s*<image\b[^>]*?/?>\s*\n*)+', re.S)


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


def seasoning_library_for_prompt() -> list[dict[str, str]]:
    return [
        {'id': recipe_id, 'name': recipe['name'], 'seasoning': recipe['seasoning']}
        for recipe_id, recipe in COVER_SEASONING_RECIPES.items()
    ]


def resolve_seasoning_recipe(brief: dict[str, Any]) -> tuple[str, dict[str, str]]:
    raw = str(brief.get('selected_recipe_id') or brief.get('selected_seasoning_id') or brief.get('selected_recipe') or '').strip()
    normalized = raw.lower().replace('_', '-').replace(' ', '-')
    if normalized in COVER_SEASONING_RECIPES:
        return normalized, COVER_SEASONING_RECIPES[normalized]

    for recipe_id, recipe in COVER_SEASONING_RECIPES.items():
        if raw and raw in {recipe['name'], recipe_id}:
            return recipe_id, recipe

    haystack = ' '.join(
        str(brief.get(key, ''))
        for key in ('tone', 'visual_direction', 'subject', 'scene', 'composition', 'palette')
    )
    keyword_map = [
        ('product-manual', ('产品', '手册', '说明', '工具', '方法', '蓝色')),
        ('architectural-blueprint', ('建筑', '图纸', '工程', '网格', '空间秩序')),
        ('oriental-literati', ('东方', '文人', '水墨', '书卷', '留白', '古籍')),
        ('cinematic-title', ('电影', '片头', '叙事', '宽银幕', '暗金')),
        ('garden-journal', ('手账', '日记', '温柔', '生活', '松弛', '绿色')),
        ('variety-trailer', ('综艺', '搞笑', '爆梗', '轻松', '明亮')),
        ('art-exhibition', ('展览', '艺术', '诗性', '展墙', '抽象')),
        ('power-editorial', ('力量', '强情绪', '暗色', '冲击')),
        ('healing-line-art', ('治愈', '线条', '柔和', '圆体')),
        ('tech-morandi', ('科技', 'AI', 'Agent', '极简', '莫兰迪', '渐变')),
    ]
    for recipe_id, keywords in keyword_map:
        if any(keyword in haystack for keyword in keywords):
            return recipe_id, COVER_SEASONING_RECIPES[recipe_id]
    return 'tech-morandi', COVER_SEASONING_RECIPES['tech-morandi']


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
            'method': '固定汤底 + 风格佐料 + 针对标题更改一两个关键元素',
            'cover_should_reflect_article_core_theme': True,
            'cover_style_should_be_inferred_from_article_content_and_tone': True,
            'default_no_text_overlay': not allow_text_overlay,
            'avoid_literal_ui_screenshots': True,
            'avoid_generic_stock_image_feel': True,
            'choose_exactly_one_seasoning_recipe': True,
        },
        'cover_broth': DEFAULT_COVER_BROTH,
        'seasoning_library': seasoning_library_for_prompt(),
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
            'selected_recipe_id': '从 seasoning_library 中选择一个 id',
            'selected_recipe_reason': '为什么这个佐料适合本文',
            'recipe_adaptations': ['只写1到3个基于文章标题/主题的小改动，不要重写整套风格'],
            'cover_message': '封面3秒内要传达的一句话推荐理由',
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
    recipe_id, recipe = resolve_seasoning_recipe(brief)
    raw_adaptations = brief.get('recipe_adaptations') or []
    if isinstance(raw_adaptations, str):
        adaptations = [raw_adaptations.strip()] if raw_adaptations.strip() else []
    else:
        adaptations = [str(item).strip() for item in raw_adaptations if str(item).strip()]
    adaptations = adaptations[:3]

    text_overlay = ''
    if allow_text_overlay:
        text_overlay = (brief.get('text_overlay') or '').strip()
    style_keywords = ', '.join(brief.get('style_keywords') or [])
    style = '; '.join(
        item for item in [
            f"{recipe['name']}：{recipe['seasoning']}",
            style_keywords,
            '文章专属巧思：' + '；'.join(adaptations) if adaptations else '',
        ] if item
    )
    cover_message = (brief.get('cover_message') or brief.get('reader_takeaway') or brief.get('core_theme') or '').strip()

    execution_spec = {
        'source_prompt': f'为微信公众号文章《{article.title}》生成封面图，主题为：{brief.get("core_theme", "")}',
        'broth': DEFAULT_COVER_BROTH,
        'selected_seasoning': {
            'id': recipe_id,
            'name': recipe['name'],
            'seasoning': recipe['seasoning'],
        },
        'article_adaptations': adaptations,
        'cover_message': cover_message,
        'subject': brief.get('subject', '') or article.title,
        'scene': brief.get('scene', '') or brief.get('visual_direction', ''),
        'style': style,
        'composition': brief.get('composition', '') or 'strong panoramic editorial composition with clear focal point and safe negative space',
        'lighting': brief.get('lighting', '') or 'clean cinematic lighting',
        'camera_language': 'wide panoramic banner framing suitable for WeChat article cover',
        'color_palette': brief.get('palette', ''),
        'text_rendering': text_overlay,
        'aspect_ratio': DEFAULT_ASPECT_RATIO,
        'quality_target': 'high',
        'must_include': include,
        'must_avoid': negative,
    }
    review_spec = {
        'title': article.title,
        'core_theme': brief.get('core_theme', ''),
        'tone': brief.get('tone', ''),
        'broth': DEFAULT_COVER_BROTH,
        'selected_seasoning': execution_spec['selected_seasoning'],
        'selected_recipe_reason': brief.get('selected_recipe_reason', ''),
        'article_adaptations': adaptations,
        'cover_message': cover_message,
        'subject': execution_spec['subject'],
        'scene': execution_spec['scene'],
        'composition': execution_spec['composition'],
        'lighting': execution_spec['lighting'],
        'color_palette': execution_spec['color_palette'],
        'aspect_ratio': DEFAULT_ASPECT_RATIO,
        'must_include': include,
        'must_avoid': negative,
    }
    return {
        'template': 'wechat-cover-broth-seasoning',
        'article_context': {
            'title': article.title,
            'source_type': article.source_type,
            'source_url': article.source_url or '',
            'core_theme': brief.get('core_theme', ''),
            'tone': brief.get('tone', ''),
            'reader_takeaway': brief.get('reader_takeaway', ''),
        },
        'cover_recipe': {
            'broth': DEFAULT_COVER_BROTH,
            'selected_recipe_id': recipe_id,
            'selected_recipe': recipe,
            'article_adaptations': adaptations,
        },
        'review_spec': review_spec,
        'execution_spec': execution_spec,
        'image_request': execution_spec,
        'output_contract': {
            'return': 'one finished image',
            'no_watermark': True,
            'no_unrequested_borders': True,
            'no_unrequested_extra_text': not allow_text_overlay,
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
    execution_spec = image_spec.get('execution_spec') or image_spec.get('image_request') or image_spec
    return (
        'Use the following JSON as the authoritative image specification for execution. '
        'Generate exactly one premium editorial WeChat cover image that follows it faithfully. '
        'Keep the broth + seasoning recipe coherent; only vary the article_adaptations. '
        'If any field is empty, infer it conservatively from source_prompt.\n\n'
        + json.dumps(execution_spec, ensure_ascii=False, indent=2)
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


def run_lark_cli(args: list[str], *, cwd: str | None = None) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or 'lark-cli command failed')
    return json.loads(completed.stdout)


def strip_leading_hero_images(markdown: str) -> str:
    stripped = LEADING_IMAGE_TAG_RE.sub('', markdown).lstrip('\n')
    return stripped


def insert_hero_into_feishu_doc_top(*, doc: str, image_path: Path, identity: str = 'user', replace_existing_top_image: bool = True) -> dict[str, Any]:
    placeholder = '__HERMES_HERO_PLACEHOLDER__'
    original = fetch_lark_doc(doc, identity=identity)
    original_markdown = original.get('markdown', '') or ''
    body_markdown = strip_leading_hero_images(original_markdown) if replace_existing_top_image else original_markdown

    try:
        run_lark_cli(
            ['lark-cli', 'docs', '+update', '--as', identity, '--doc', doc, '--mode', 'overwrite', '--markdown', placeholder],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / image_path.name
            tmp_path.write_bytes(image_path.read_bytes())
            insert_result = run_lark_cli(
                ['lark-cli', 'docs', '+media-insert', '--as', identity, '--doc', doc, '--file', f'./{tmp_path.name}'],
                cwd=tmpdir,
            )
        fetched_after_insert = fetch_lark_doc(doc, identity=identity)
        inserted_markdown = fetched_after_insert.get('markdown', '') or ''
        match = IMAGE_TAG_RE.search(inserted_markdown)
        if not match:
            raise RuntimeError('Failed to locate inserted hero image tag in Feishu document markdown')
        hero_markdown = match.group(0)
        final_markdown = hero_markdown if not body_markdown.strip() else f'{hero_markdown}\n\n{body_markdown.strip()}\n'
        run_lark_cli(
            ['lark-cli', 'docs', '+update', '--as', identity, '--doc', doc, '--mode', 'overwrite', '--markdown', final_markdown],
        )
        return {
            'doc_id': original.get('doc_id') or extract_lark_doc_token(doc),
            'doc_url': original.get('source_url') or (doc if doc.startswith(('http://', 'https://')) else ''),
            'insert_result': insert_result.get('data') or {},
            'replaced_existing_top_image': replace_existing_top_image and body_markdown != original_markdown,
        }
    except Exception:
        restore_cmd = ['lark-cli', 'docs', '+update', '--as', identity, '--doc', doc, '--mode', 'overwrite', '--markdown', original_markdown]
        run_lark_cli(restore_cmd)
        raise


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
        sub.add_argument('--insert-into-feishu-doc-top', action='store_true', help='After generation, insert the hero image at the top of the Feishu doc body')
        sub.add_argument('--replace-existing-top-image', action=argparse.BooleanOptionalAction, default=True, help='When inserting into Feishu doc top, replace an existing leading hero image instead of stacking another one')
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

        if args.insert_into_feishu_doc_top:
            if args.command != 'from-feishu-doc':
                return fail('--insert-into-feishu-doc-top currently requires from-feishu-doc so the target doc is explicit', 2)
            insert_meta = insert_hero_into_feishu_doc_top(
                doc=args.doc,
                image_path=output,
                identity=args.identity,
                replace_existing_top_image=args.replace_existing_top_image,
            )
            print(f'feishu_doc_hero_inserted=true')
            print(f'feishu_doc_id={insert_meta.get("doc_id", "")}')
            if insert_meta.get('doc_url'):
                print(f'feishu_doc_url={insert_meta.get("doc_url")}')
            print(f'replaced_existing_top_image={str(insert_meta.get("replaced_existing_top_image", False)).lower()}')

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
