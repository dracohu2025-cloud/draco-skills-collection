# WeChat draft publishing pitfalls: video insertion + nested markdown code blocks

## Feishu ` ```markdown ` blocks with nested fences

When a Feishu document intentionally contains a whole markdown snippet/code block, it may export as an outer ` ```markdown ` block that itself contains nested fences such as ` ```bash `.

Do **not** unwrap the outer block just to avoid parser confusion. The user may expect the whole region through the official-doc link or similar text to remain in a code block, while the next section heading must be outside it.

Safer behavior:

1. Preserve the outer code block as one `<pre><code>` region.
2. HTML-escape the inner markdown/fences instead of letting a Markdown parser treat nested fences as real delimiters.
3. Verify by checking semantic anchors, not just total `<pre>` counts:
   - the intended last line inside the block is inside `<pre>`
   - the next section heading is outside `<pre>`
   - `<pre>` / `</pre>` counts match

Example validation targets from the session:

- `官方完整文档` should be inside the code block.
- `工作习惯` and following prose should be outside.

## Embedded video in WeChat drafts

WeChat permanent video material upload effectively requires MP4 <= 10MB. Large Feishu videos may fail with connection reset / empty reply before a JSON error.

Workflow:

1. If video >10MB, compress before upload, e.g.:
   ```bash
   ffmpeg -y -i input.mp4 -vf 'scale=-2:720,fps=30' -c:v libx264 -preset medium -crf 28 -c:a aac -b:a 96k output.mp4
   ```
2. Upload as permanent material with `material/add_material?type=video` and JSON `description` containing title/introduction.
3. Call `material/get_material` for the uploaded `media_id` and extract `vid` (often `apiv_...`).
4. Insert a rich-pages iframe in article HTML using the returned vid, e.g. `class="video_iframe rich_pages" data-mpvid="<vid>"`.
5. Verify `draft/get` preserves:
   - one `video_iframe`
   - one `data-mpvid`
   - the exact returned `vid`

If upload still fails, use a video cover card as a graceful fallback, but do not leave public-facing text like “视频素材同步失败”.
