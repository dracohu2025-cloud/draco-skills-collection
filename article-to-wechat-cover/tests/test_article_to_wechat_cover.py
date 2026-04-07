from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(ROOT))

from article_to_wechat_cover import (  # noqa: E402
    DEFAULT_ASPECT_RATIO,
    build_final_image_prompt,
    build_image_spec,
    extract_sections,
    load_markdown_article,
    markdown_to_plain_text,
    resolve_output_path,
    strip_leading_hero_images,
)


def test_load_markdown_article_uses_frontmatter_title(tmp_path):
    article_path = tmp_path / 'demo.md'
    article_path.write_text(
        '---\n'
        'title: 测试标题\n'
        'author: DracoVibeCoding\n'
        '---\n\n'
        '# 正文一级标题\n\n'
        '这里是正文。\n',
        encoding='utf-8',
    )

    article = load_markdown_article(str(article_path))

    assert article.title == '测试标题'
    assert '这里是正文' in article.markdown


def test_markdown_to_plain_text_removes_basic_markdown_syntax():
    markdown = '# 标题\n\n- 列表项\n\n这是 **加粗** 文本，还有 [链接](https://example.com) 和 `code`。'
    text = markdown_to_plain_text(markdown)
    assert '标题' in text
    assert '列表项' in text
    assert '加粗' in text
    assert '链接' in text
    assert 'https://example.com' not in text
    assert '`' not in text


def test_build_image_spec_forces_wechat_cover_aspect_ratio():
    class Article:
        title = 'AI Agent 的产品化路径'
        source_type = 'markdown'
        source_url = None

    brief = {
        'core_theme': 'AI Agent 从 demo 到产品化的关键路径',
        'tone': '理性、未来感',
        'reader_takeaway': '理解真正可落地的 agent 设计方法',
        'subject': '抽象化智能体工作流与产品界面融合的主视觉',
        'scene': '未来感工作台中，一条清晰的 agent workflow 向前延伸',
        'visual_direction': '高端编辑感横幅封面',
        'composition': '横向延展，主体偏左，右侧留白',
        'lighting': '冷静的科技感边缘光',
        'palette': '深蓝与活力橘对比',
        'style_keywords': ['editorial', 'cinematic', 'clean'],
        'must_include': ['workflow path'],
        'must_avoid': ['watermark'],
        'text_overlay': '',
    }

    spec = build_image_spec(
        article=Article(),
        brief=brief,
        allow_text_overlay=False,
        must_include=['clean focal point'],
        must_avoid=['二维码'],
    )

    image_request = spec['image_request']
    assert image_request['aspect_ratio'] == DEFAULT_ASPECT_RATIO
    assert 'workflow path' in image_request['must_include']
    assert 'clean focal point' in image_request['must_include']
    assert '二维码' in image_request['must_avoid']
    assert image_request['text_rendering'] == ''


def test_extract_sections_limits_count():
    markdown = '\n'.join([f'## 第{i}节' for i in range(1, 12)])
    sections = extract_sections(markdown, limit=5)
    assert len(sections) == 5
    assert sections[0] == '第1节'


def test_resolve_output_path_corrects_extension_for_mime():
    adjusted = resolve_output_path('/tmp/wechat-cover.png', 'image/jpeg')
    assert str(adjusted).endswith('.jpg') or str(adjusted).endswith('.jpeg')


def test_build_final_image_prompt_contains_image_spec_json():
    prompt = build_final_image_prompt({'image_request': {'aspect_ratio': '2.35:1', 'subject': 'AI Agent'}})
    assert 'authoritative image specification' in prompt
    assert '2.35:1' in prompt
    assert 'AI Agent' in prompt


def test_strip_leading_hero_images_removes_only_leading_image_tags():
    markdown = '<image token="abc" width="100" height="50" align="center"/>\n\n# 标题\n\n正文\n'
    assert strip_leading_hero_images(markdown) == '# 标题\n\n正文\n'
