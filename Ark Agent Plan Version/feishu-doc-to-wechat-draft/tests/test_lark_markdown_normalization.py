from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wechat_draft_publisher.lark_docs import normalize_lark_markdown


def test_strong_numbered_lines_become_ordered_list_items() -> None:
    source = """## 这个工具能做什么
简单说，它解决三个核心问题：
**1. 图片自动处理**
飞书文档里的图片会自动下载，上传到微信素材库，替换成微信 CDN 链接。你不需要手动一张张处理。
**2. 格式完整保留**
表格、引用块、代码块、分割线，这些在飞书里的格式，转成 HTML 后都能正确显示。特别是代码块，支持 Mac 风格的美化显示。
**3. 排版风格统一**
工具内置了 Doocs 风格的渲染方案，和我们平时在 md-editor 编辑器里看到的预览效果一致。标题、正文、引用都有统一的视觉风格。
"""
    normalized = normalize_lark_markdown(source)

    assert "1. **图片自动处理**\n\n   飞书文档里的图片会自动下载" in normalized
    assert "2. **格式完整保留**\n\n   表格、引用块、代码块、分割线" in normalized
    assert "3. **排版风格统一**\n\n   工具内置了 Doocs 风格的渲染方案" in normalized
    assert "**1. 图片自动处理**\n飞书文档里的图片" not in normalized


def test_standalone_strong_heading_keeps_paragraph_boundary() -> None:
    source = """## 使用之前需要准备三样东西：
**2. 微信公众号凭证**
登录微信公众号平台，在「开发」-「基本配置」里获取：
- AppID
- AppSecret（只显示一次，记得保存）
同时把你的服务器 IP 添加到「IP 白名单」，否则调用接口会报错。
"""
    normalized = normalize_lark_markdown(source)

    assert "2. **微信公众号凭证**\n\n   登录微信公众号平台，在「开发」-「基本配置」里获取：" in normalized
    assert "- AppID" in normalized
    assert "- AppSecret（只显示一次，记得保存）" in normalized
    assert "   - AppSecret（只显示一次，记得保存）\n\n   同时把你的服务器 IP 添加到「IP 白名单」" in normalized


def test_media_id_section_keeps_method_headings_and_lists() -> None:
    source = """## 前置准备
**3. 封面图的 media_id**
微信要求每篇文章必须有封面图。获取封面图 media_id 的方法有三种：
**方法一：微信公众平台后台（最简单）**
1. 登录微信公众平台
1. 左侧菜单 →「内容与互动」→「素材库」
**方法二：微信在线调试工具**
1. 访问微信公众平台接口调试工具（mp.weixin.qq.com/debug）
**方法三：使用代码上传**
如果你熟悉 Python，可以直接调用微信 API 上传：
```python
print('hi')
```
"""
    normalized = normalize_lark_markdown(source)

    assert "3. **封面图的 media_id**\n\n   微信要求每篇文章必须有封面图。获取封面图 media_id 的方法有三种：" in normalized
    assert "**方法一：微信公众平台后台（最简单）**\n\n1. 登录微信公众平台" in normalized
    assert "**方法二：微信在线调试工具**\n\n1. 访问微信公众平台接口调试工具（mp.weixin.qq.com/debug）" in normalized
    assert "**方法三：使用代码上传**\n\n如果你熟悉 Python，可以直接调用微信 API 上传：\n```python" in normalized


def test_lark_table_cells_can_contain_angle_bracket_placeholders() -> None:
    source = """<lark-table rows=\"2\" cols=\"2\" column-widths=\"200,200\">
  <lark-tr>
    <lark-td>选项</lark-td>
    <lark-td>描述</lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>`-m`, `--model <model>`</lark-td>
    <lark-td>覆盖本次运行的模型。</lark-td>
  </lark-tr>
</lark-table>
"""
    normalized = normalize_lark_markdown(source)

    assert "| 选项 | 描述 |" in normalized
    assert r"| `-m`, `--model <model>` | 覆盖本次运行的模型。 |" in normalized
