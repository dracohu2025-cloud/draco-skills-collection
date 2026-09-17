# Feishu Doc → WeChat Draft with Default Generated Cover

Session learning: when the user asks to push a Feishu doc to the official-account draft box, generate a dedicated cover by default. Do not silently reuse the first embedded image unless explicitly requested.

## Recommended flow

1. Fetch source:

```bash
lark-cli docs +fetch --doc "$DOC" --format pretty > /tmp/feishu_fetch.txt
```

Check title, `<image>` count, `<file>` count, and rough topic.

2. Generate cover art:
- Use `image_generate` / `image_gen` to generate the **complete publication-ready cover**, including the intended title/subtitle/tags/text.
- Do **not** generate a blank/background image and then add Chinese title text locally with PIL/HTML/SVG/code, unless the user explicitly overrides this hard rule for that single task.
- Code may only perform format-only operations such as crop/resize/compress/upload; it must not add, edit, or typeset public-facing cover text.
- Run vision QA on the generated cover. If OCR/text fails, regenerate with fewer/larger words rather than fixing text locally.

3. Dry-run with default Doocs style:

```bash
python3 scripts/run.py publish-feishu-doc-default \
  --doc "$DOC" \
  --author 'DracoVibeCoding' \
  --thumb-media-id DRY_RUN_MEDIA_ID \
  --dry-run \
  --profile doocs --theme grace --primary-color '#FA5151' --font-size 15 \
  > /tmp/wechat_dryrun.log 2>&1
```

4. Formal publish with the generated cover:

```bash
python3 scripts/run.py publish-feishu-doc-default \
  --doc "$DOC" \
  --author 'DracoVibeCoding' \
  --cover-image /abs/path/cover_2350x1000.png \
  --profile doocs --theme grace --primary-color '#FA5151' --font-size 15 \
  > /tmp/wechat_publish.log 2>&1
```

For image-heavy docs, run as background and poll; stdout may stay quiet until the command completes.

5. Verify with `draft/get` and `draft/batchget`:
- title exactly matches the Feishu document title / author
- `thumb_media_id` present
- draft visible in batch list
- `<img>` count and `mmbiz.qpic.cn` count
- `lark-image://` residue = 0
- `#FA5151` / `15px` style markers where applicable
- bad markers = 0: `white-space: nowrap`, `display: -webkit-box`
- `content_source_url` is empty for this user's default “不填原文链接” convention

If formal publish still writes the Feishu doc URL into `content_source_url`, immediately call WeChat `draft/update` instead of creating a duplicate draft. Use the existing verified article payload, set `article["content_source_url"] = ""`, then POST:

```json
{
  "media_id": "<draft_media_id>",
  "index": 0,
  "articles": { "...existing article fields...": "..." }
}
```

to the WeChat `draft/update` endpoint. Re-run `draft/get` and require `content_source_url == ""` before reporting success. A `table-layout: fixed` count of `0` is fine when the source doc has no tables; do not flag it as a failure.

## Reporting

Return a compact table plus the generated cover file as `MEDIA:/abs/path.png` when useful.

Include:
- title
- author
- draft `media_id`
- cover generated/uploaded
- image counts
- video material count if present
- draft-box verification status
