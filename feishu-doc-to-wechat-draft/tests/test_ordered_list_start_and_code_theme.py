from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.lark_docs import normalize_lark_markdown
from wechat_draft_publisher.renderer import render_markdown


def test_render_defaults_keep_article_content_left_aligned() -> None:
    md = """# 一级标题

## 二级标题

正文段落。

![alt](x.png "图注")

***
"""
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        font_size=14,
        caption_mode="title-first",
        hr_style="star",
    ).html
    assert "text-align: justify" not in html
    assert "text-align: center" not in html
    assert "margin: 2em auto" not in html
    assert "margin: 4em auto" not in html
    assert 'text-align: left' in html
    assert '<h1 class="md-h1" style="display: inline-block;' in html
    assert '<h2 class="md-h2 md-h2-solid" style="display: inline-block;' in html
    assert '<figcaption class="md-figure-caption" style="text-align: left;' in html


def test_ordered_list_keeps_start_attribute_when_markdown_starts_at_two() -> None:
    md = "2. 第二项\n3. 第三项\n"
    html = render_markdown(md, profile="doocs", theme="grace", font_size=14).html
    assert '<span class="md-ordered-index"' in html
    assert '>2.</span>' in html
    assert '>3.</span>' in html
    assert '<ol start="2">' not in html
    assert '<li class="md-li"' not in html


def test_lark_lazy_ordered_lists_are_renumbered_across_images_quotes_and_prose() -> None:
    md = """1. 下载

![image](lark-image://a)

1. 安装

> 提示

1. 配置
  1. Gateway
  1. Base URL
  1. API Key

普通说明段仍属于这个松散编号组。

![image](lark-image://b)

1. 重启

---

1. 新章节第一项
"""
    normalized = normalize_lark_markdown(md)
    numbered_lines = [line for line in normalized.splitlines() if re.match(r"\s*\d+\.\s", line)]
    assert numbered_lines == [
        "1. 下载",
        "2. 安装",
        "3. 配置",
        "    1. Gateway",
        "    2. Base URL",
        "    3. API Key",
        "4. 重启",
        "1. 新章节第一项",
    ]

    html = render_markdown(normalized, profile="doocs", theme="grace", font_size=14).html
    assert '>1.</span>' in html
    assert '>2.</span>' in html
    assert '>3.</span>' in html
    assert '>4.</span>' in html


def test_lark_exported_loose_project_list_does_not_render_all_as_one() -> None:
    md = """1. Draco-Skills-Collection

<quote-container>
这个仓库里放了十几个基础工作流：
- 飞书文档推送公众号；
- 生成教学视频；
</quote-container>

1. 网页版山海经V0.1版：

<quote-container>
https://hermes.aigc.green/shanhaijing/
</quote-container>

<image token="img1" width="100" height="100"/>

1. Graphics Academy：AI风格影像馆

用来刻意练习图片风格鉴别能力。

<image token="img2" width="100" height="100"/>

1. 迷你剧skill

《臭猫视频placeholder！》

1. 在测试和探索阿里新发布的“悟空”

---

最后，讨论一个问题。
"""
    normalized = normalize_lark_markdown(md)
    numbered_lines = [line for line in normalized.splitlines() if re.match(r"\d+\.\s", line)]
    assert numbered_lines == [
        "1. Draco-Skills-Collection",
        "2. 网页版山海经V0.1版：",
        "3. Graphics Academy：AI风格影像馆",
        "4. 迷你剧skill",
        "5. 在测试和探索阿里新发布的“悟空”",
    ]

    html = render_markdown(normalized, profile="doocs", theme="grace", font_size=14).html
    indexes = re.findall(r'class="md-ordered-index"[^>]*>([^<]+)</span>', html)
    assert indexes == ["1.", "2.", "3.", "4.", "5."]
    assert len(set(indexes)) > 1


def test_code_blocks_use_same_light_background_under_default_github_theme() -> None:
    md = '```bash\necho hello\n```\n\n```python\nprint("hi")\n```\n'
    html = render_markdown(
        md,
        profile="doocs",
        theme="grace",
        code_theme="github",
        mac_code_block=True,
        font_size=14,
    ).html
    assert html.count('background: #f6f8fa;') >= 2
    assert 'background: #24292f;' not in html


def test_ordered_list_items_preserve_block_paragraphs() -> None:
    md = """1. **图片自动处理**

   飞书文档里的图片会自动下载。

2. **格式完整保留**

   表格、引用块、代码块都能显示。
"""
    html = render_markdown(md, profile="doocs", theme="grace", font_size=14).html
    assert '<section class="md-ordered-item"' in html
    assert '<section class="md-ordered-text"' in html
    assert '<span class="md-ordered-text"><p' not in html
    assert '飞书文档里的图片会自动下载。' in html


def test_media_id_methods_render_as_separate_blocks() -> None:
    md = """3. **封面图的 media_id**

   微信要求每篇文章必须有封面图。获取封面图 media_id 的方法有三种：

**方法一：微信公众平台后台（最简单）**

1. 登录微信公众平台
1. 左侧菜单 →「内容与互动」→「素材库」

**方法三：使用代码上传**

如果你熟悉 Python，可以直接调用微信 API 上传：
```python
print('hi')
```
"""
    html = render_markdown(md, profile="doocs", theme="grace", font_size=14).html
    assert '封面图的 media_id</strong></p>' in html
    assert '方法一：微信公众平台后台（最简单）' in html
    assert '登录微信公众平台</section>' in html
    assert '方法三：使用代码上传' in html
    assert '<pre class="code-block md-pre md-pre-mac"' in html or '<pre class="code-block md-pre"' in html


def test_major_block_containers_are_explicitly_left_aligned() -> None:
    md = """引言。

> 引用内容。

1. 第一项

   项目说明。

- 无序项

![alt](x.png "图注")
"""
    html = render_markdown(md, profile="doocs", theme="grace", font_size=14, caption_mode="title-first").html
    assert "text-align: justify" not in html
    assert "text-align: center" not in html
    for marker in [
        'class="wechat-blockquote md-blockquote"',
        'class="md-list md-list-ordered"',
        'class="md-ordered-item"',
        'class="md-ordered-text"',
        'class="md-list md-list-unordered"',
        'class="md-bullet-item"',
        'class="md-bullet-text"',
        'class="md-figure"',
        'class="md-figure-caption"',
    ]:
        start = html.index(marker)
        opening_tag = html[start:html.index(">", start)]
        assert "text-align: left" in opening_tag, marker


def test_nested_unordered_lists_render_as_nested_blocks() -> None:
    md = """目前有三个Hermes Agents：

- Hermes：
  - 模型：GPT-5.4 High；
  - 用来完成各种需要复杂coding的任务，例如网站建设、封装复杂skills、Remote/Manim等复杂动效生成；
  - 宿主：腾讯云轻应用服务器4核8G版本实例 - 曼谷节点；
"""
    html = render_markdown(md, profile="doocs", theme="grace", font_size=14).html
    assert html.count('class="md-list md-list-unordered"') >= 2
    assert '<ul class="md-ul"' not in html
    assert '<li class="md-li"' not in html
    assert '<section class="md-bullet-text" style="flex: 1 1 auto; min-width: 0; text-align: left;">Hermes：' in html
    assert '模型：GPT-5.4 High；' in html
    assert '宿主：腾讯云轻应用服务器4核8G版本实例 - 曼谷节点；' in html


def test_unordered_lists_still_render_bullets_when_article_contains_hr() -> None:
    md = """先来一段前言。

---

- 轻量应用服务器Lighthouse，自带流量和带宽，对绝大多数新手来说性价比友好；
- 2核4G或以上配置；
"""
    html = render_markdown(md, profile="doocs", theme="grace", font_size=14).html
    assert 'class="md-bullet-dot"' in html
    assert '<ul class="md-ul"' not in html
    assert '•</span>' in html
