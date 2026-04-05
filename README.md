# Draco Skills Collection

这是一个用来收集和整理 Draco使用 **Hermes Agent** 封装的skills的公开仓库。

## 这个仓库里有什么

目前已经收录：

### `feishu-doc-to-wechat-draft/`

将飞书（Feishu/Lark）文档一键转换为微信公众号草稿，支持精美排版和图片自动上传。

**核心功能：**
- 🚀 从飞书文档 URL 直接生成微信草稿
- 🎨 Doocs 风格渲染（优雅主题 + 活力橘），与 md-editor 编辑器效果一致
- 📸 自动下载飞书图片并上传至微信素材库
- 👁️ 支持本地 HTML 预览，确认效果后再发布

**快速开始：**
```bash
cd feishu-doc-to-wechat-draft
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 生成预览
python3 scripts/run.py render-preview-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --output /tmp/preview.html

# 发布到微信草稿箱
python3 scripts/run.py publish-feishu-doc-default \
  --doc "https://your-domain.feishu.cn/docx/DocID" \
  --thumb-media-id "your_cover_image_media_id"
```

更多详情查看 [`feishu-doc-to-wechat-draft/README.md`](./feishu-doc-to-wechat-draft/README.md)

---

### `epub2podcast/`

这是当前仓库中的 podcast skill / 项目，主要覆盖电子书到视频播客的完整工作流，包括：

- 在飞书中将电子书EPUB文件上传给 Hermes Agent
- 把 EPUB 转成双人中文播客脚本
- 生成分段音频，并合成完整音频
- 生成 Smart Slide
- 合成最终 MP4 视频
- 提供视频压缩脚本，方便后续分享或上传

当前已经完成真实端到端验证，可独立安装、构建和运行。

发布状态：**v0.1.0 early standalone release**

示例页面预览：

<table>
  <tr>
    <td width="50%" valign="top">
      <img src="./epub2podcast/assets/example-slide-cover.png" alt="epub2podcast 示例封面页" />
      <p><strong>封面页风格</strong><br/>适合放在视频开头，用来介绍书名、主题和整体气质。</p>
    </td>
    <td width="50%" valign="top">
      <img src="./epub2podcast/assets/example-slide-infographic.png" alt="epub2podcast 示例信息图页" />
      <p><strong>信息图风格</strong><br/>适合在视频中段解释观点、拆解结构，或者展示一个主题的关键信息。</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <img src="./epub2podcast/assets/example-slide-split-layout.png" alt="epub2podcast 左右分栏版式示例" />
      <p><strong>左右分栏版式</strong><br/>适合做“引言 + 分点展开”的讲述页。</p>
    </td>
    <td width="50%" valign="top">
      <img src="./epub2podcast/assets/example-slide-card-layout.png" alt="epub2podcast 三卡片版式示例" />
      <p><strong>三卡片版式</strong><br/>适合把一个主题拆成多个并列重点。</p>
    </td>
  </tr>
</table>

更多截图、流程图和说明，请查看：
- [`epub2podcast/README.md`](./epub2podcast/README.md)

目录里目前包含：

- `SKILL.md`：核心技能说明
- `README.md`：面向普通读者的介绍
- `scripts/epub2podcast_local_run.sh`：主运行脚本
- `scripts/epub2podcast_local_regenerate_slide.sh`：重生成单页 slide
- `scripts/epub2podcast_local_compress_feishu_video.sh`：压缩视频文件



