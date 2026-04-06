from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.renderer import render_markdown


def test_ordered_list_keeps_start_attribute_when_markdown_starts_at_two() -> None:
    md = "2. 第二项\n3. 第三项\n"
    html = render_markdown(md, profile="doocs", theme="grace", font_size=14).html
    assert '<ol start="2">' in html
    assert '>第二项</li>' in html
    assert '>第三项</li>' in html


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
