---
name: wechat-publishing-workflow
description: "Use when extracting WeChat articles, rendering Markdown for official-account drafts, generating covers, or publishing Feishu/Markdown content into WeChat workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, publishing, official-account, productivity]
    related_skills: []
---

# WeChat Publishing Workflow

## Overview
A class-level entry for WeChat Official Account production: source extraction, Markdown rendering, cover generation, media upload, draft creation, and Feishu-to-WeChat handoff.

## When to Use
- A task mentions 微信公众号, WeChat Official Account, article extraction, cover art, Doocs-like rendering, or draft publishing.
- You need to move content from Feishu/Markdown/browser pages into a WeChat draft.
- You need to choose between BrowserUse, Camofox, official APIs, or local renderers.

## Workflow Router
- **Extraction:** use Camofox/local anti-detection browser for difficult public article pages; BrowserUse is a cloud-browser fallback.
- **Rendering:** use a Doocs-like theme/profile layer for Markdown-to-WeChat HTML before publishing.
- **Cover generation:** derive article theme/style, confirm the prompt, generate 2.35:1 cover art, then upload if needed.
- **Draft publishing:** use official account API: token, media upload, cover upload, then `draft_add`.
- **Feishu source:** fetch Feishu native doc content first, then route through rendering and draft publishing.

## Common Pitfalls
**Publisher-native since 2026-08-27** (canonical repo `feishu-doc-to-wechat-draft`, covered by `tests/test_native_publish_fixes.py`): locked-width wrapping code blocks at 12px, Feishu `<grid>/<column>` → fixed-layout tables, long Mac code block height cap (>30 lines → `max-height: 480px` + fixed dots header), two trailing blank paragraphs in every payload, no implicit `content_source_url` (explicit `--source-url` only), and playable `rich_pages video_iframe` embeds when video upload + `material/get_material` vid resolution succeed (neutral poster card without failure wording otherwise). The repair rules below (20/21c/21g/24) remain as the post-publish fix path for drafts created before these behaviors were native, or when WeChat strips something.

1. Do not publish before the user confirms final generated image prompt when the user explicitly asks to review/approve the cover prompt. For routine Feishu-doc draft pushes, do not ask for extra confirmation just to satisfy this rule; generate a sensible cover, QA it, and publish with `--cover-image` unless the user requested manual review.
1a. For WeChat article/engagement visuals, do **not** hand-draw production artwork with PIL unless the user explicitly asks for deterministic/icon-only output. It reads as crude engineering art. Use `image_generate` / `image_gen` to create the complete article cover, including public-facing text; only crop/resize/compress/upload locally. If the user asks for pixel/voxel style, prefer polished voxel/3D editorial cover style over rough pixel blocks.
2. For WeChat article engagement banners / footer CTA images (e.g. “点赞、转发、在看 / 一键三连”), do **not** hand-draw crude pixel/PIL graphics as the primary visual. For article covers, generate the complete visual including text directly with `image_generate` / `image_gen`; do not add exact Chinese copy locally. For non-cover engagement banners, local text overlay is allowed only when explicitly requested. If the user asks for voxel/体素风, prompt for high-end 3D voxel editorial cover style, warm Doocs orange-red `#FA5151`, cream background, three clean glowing icons, generous negative space, and no watermarks/text. Always run vision QA after both generation and local text overlay, explicitly checking icon clarity and exact Chinese OCR.
3. WeChat body images and cover images use different upload endpoints and media IDs.
3. Public article pages are noisy; prefer accessibility snapshot plus WeChat-specific cleanup.
4. Keep dry-run/preview output until API credentials and content formatting are verified.
5. Feishu tables can render badly in WeChat if long cells squeeze the first column. Force all exported tables to `table-layout: fixed; width: 100%` and add cell `word-break` / `overflow-wrap`; verify the updated draft via `draft/get` rather than creating duplicates.
5a. WeChat draft storage strips external `<a>` anchors from article content, leaving plain text. If the user wants links to *look* clickable, render them as visual spans instead of anchors: `<span class="md-link" style="color: #1e6bd6; text-decoration: underline; text-underline-offset: 2px;">URL</span>`. Verify with `draft/get` after publish/update; do not trust dry-run HTML containing `<a>` tags.
6. When publishing a Feishu doc with a newly generated cover, pass the exact local cover path via `--cover-image`; otherwise the Feishu pipeline may fall back to the article’s first embedded image. Current canonical pipeline can publish without `--cover-image`/`--thumb-media-id` if the Feishu doc has a first embedded image: it auto-downloads that image, uploads it as cover, and uses the returned `thumb_media_id`. Still run preview → dry-run → publish → `draft/get`/`draft/batchget` verification.
7. If the user explicitly says to call `image_generate` for the cover, do exactly that first; do not substitute a different image backend just because another cover skill mentions Nano Banana/OpenRouter.
8. Runtime path may differ from old archived examples. On this machine the active Feishu→WeChat publisher can be the canonical standalone project at `publisher/scripts/run.py`; check path existence before assuming `~/.hermes/skills/.../scripts/run.py` exists.
12. For the user's WeChat draft pushes, preserve the Doocs visual default as orange + grace/elegant + 15px unless explicitly changed. Avoid bare `--profile doocs` defaults that drift to blue or 16px; use the default style config or explicit flags: `--profile doocs --theme grace --primary-color '#FA5151' --font-size 15`. After publishing, verify `draft/get` actually contains the orange color, 15px font sizing where expected, and no `var(--md-primary-color)` residue; WeChat may strip root CSS variables, so theme accents must be inlined.
12b. For this user's default “不填原文链接” convention, do not trust omission of `--source-url`: the current standalone Feishu publisher may still set `content_source_url` to the Feishu doc URL internally. After publish, inspect `draft/get` `news_item[0].content_source_url`; if non-empty, call `draft/update` for index 0 with the existing article payload and `content_source_url: ""`, then verify again. **Never change the article title to work around update errors; the WeChat draft title must match the Feishu document title exactly unless the user explicitly asks otherwise.** When using the raw `draft/get` article as the update payload, strip server-side/read-only fields such as `url`, `is_deleted`, `update_time`, `create_time`, `thumb_url`, and `article_type`; ensure `need_open_comment` and `only_fans_can_comment` exist (default `0`) before POSTing to `draft/update`. The `draft/update` envelope is `{"media_id": ..., "index": 0, "articles": <single article object>}`—`articles` is an object, not a one-element array; the array form returns WeChat `47001 data format error`.  Send WeChat `draft/update` JSON as raw UTF-8 with `json.dumps(payload, ensure_ascii=False).encode('utf-8')` plus `Content-Type: application/json; charset=utf-8`; Python `requests.post(json=payload)` escapes Chinese as `\uXXXX` and can trigger misleading `45003 title size out of limit` even for short titles. The READ side has the mirror-image pitfall: `resp.json()` on `draft/get` can misdecode the UTF-8 body as ISO-8859-1 (WeChat omits charset), yielding mojibake like `æå°è£`. If you then round-trip that mojibake string back through `draft/update`, you permanently store garbled Chinese in the draft (the WeChat editor will show 乱码). Always decode reads explicitly: `json.loads(resp.content.decode('utf-8'))`, and sanity-check the decoded title for mojibake before using it as update payload; if in doubt, rebuild the update payload from the local publish-output JSON instead of from `draft/get`. If clearing `content_source_url` still conflicts with keeping the exact title, preserve the exact title and report the blocker instead of silently shortening it. Then re-run both the packaged verifier and a direct `draft/get` source-url/title check; the packaged verifier currently does not report `content_source_url`.
9. `lark-cli docs +fetch` uses `--doc` for either URL or token; do not use the stale/nonexistent `--doc-token` flag. If the publisher fails with `need_user_authorization`, the lark-cli user token has expired/been cleared; use `--identity bot` (publisher flag, maps to `lark-cli --as bot`) for both preview and publish, and tell the user `lark-cli auth login` is needed to restore user identity.
10. Dry-run for Feishu docs may still contain `lark-image://` placeholders because it validates payload structure without uploading/replacing all images. Judge image replacement only after formal publish and `draft/get`.
10b. Native Feishu image captions live in raw Docx image blocks as `image.caption.content`; `lark-cli docs +fetch` Markdown may omit them. The canonical publisher must query `/open-apis/docx/v1/documents/:document_id/blocks`, map captions by image token, and feed them into Markdown image alt text before rendering. Publish with `--caption-mode alt-first`, then verify final `draft/get` has one gray small `<figcaption>` per genuinely captioned image. Do not re-create separate bold caption paragraphs. Feishu images without native captions normalize to generic alt text such as `image`; treat `image`, `img`, `picture`, `photo`, `图片`, and `图像` as placeholders, never render them as `<figcaption>`. Preserve a real title/alt caption when present, and verify the final draft contains zero literal `>image</figcaption>` entries.
11. Formal `publish-feishu-doc` can print a huge JSON payload plus noisy `lark-cli` fetch output. Redirect/tee stdout/stderr to files, then parse/summarize with Python; do not paste raw payload back to the user. For image-heavy docs, run as a background process and poll so the user is not left staring at silence.
12. If the source Feishu doc contains embedded videos/files, final WeChat `draft/get` image count may exceed the source `<image>` count because video poster/material cards can become additional `<img>` elements. Verify `lark-image://` residue is 0 rather than expecting preview/source image counts to match exactly.
12a. For image-heavy Feishu docs, source fetch dimensions can be misleading: an image block may show `width="100" height="100"` even when the WeChat draft renders it responsively. After formal publish, inspect final `draft/get` `<img>` tags for literal `width=100`/`height=100` attrs and confirm responsive width styling before reporting success.
12c. WeChat may reject extreme-dimension Lark PNG screenshots with `40137 invalid image format` even when the file is a valid PNG (observed 18018×24477 RGBA PNG downloaded with a `.jpg` filename). The active publisher should downsample these before upload; if this recurs, inspect the failing `lark_img_<token>.jpg` with `file`, then use/patch `_ensure_wechat_supported_image()` to stream-downsample giant PNGs to JPEG rather than loading the full bitmap with PIL, which can trigger decompression-bomb or OOM issues.
13. After successful publish, the publisher stores WeChat stable token cache at `~/.cache/wechat-draft-publisher/access_token_<appid>.json`; use it for manual `draft/get` and `draft/batchget` verification when the CLI has no built-in verify command. A reusable verifier is available at `scripts/verify_wechat_draft.py <draft_media_id>` inside this skill directory; if the standalone publisher repo lacks that helper, run the skill-packaged path (`scripts/verify_wechat_draft.py`) rather than treating it as a missing capability. It reports title/author/thumb, image counts, `lark-image://` residue, style markers, table layout, bad renderer markers, and batch visibility. Current verifier output may not include `content_source_url`; for this user's default “不填原文链接”, still manually query `draft/get` and inspect `news_item[0].content_source_url`, then run `draft/update` to clear it if needed. If the verifier returns WeChat `42001` (`access_token expired`) for an older draft, treat it as a stale cached-token problem, not proof the draft is missing; refresh via `stable_token` or the publish pipeline, then retry `draft/get`/`batchget`.
14. For the canonical `publish-feishu-doc-default` JSON output, do not expect `thumb_media_id` at the top level; it may be `null` there while the real cover ID is in `payload.articles[0].thumb_media_id`. Verify cover presence from `draft/get` (`news_item[0].thumb_media_id`) rather than the top-level wrapper.
15. For this user's WeChat draft pushes, default to generating a dedicated cover image unless the user explicitly says to reuse the article’s existing first image/old cover, or says only text changed. Do not silently fall back to the first embedded image. Generate a complete 2.35:1 cover via `image_generate` / `image_gen` (text included in the generated image), pass it via `--cover-image`, then dry-run/formal publish and `draft/get`/`draft/batchget` verification. Report a compact table: title, author, draft media_id, thumb present, generated cover path/media status, image count, `mmbiz.qpic.cn` count, `lark-image://` residue, `<grid`/`<column` residue = 0 (repair via rule 21g if non-zero), style markers, and bad marker counts. If the article body has no headings/accent blocks, final `draft/get` may contain zero `#FA5151` even though dry-run style resolution is correct; don’t treat that alone as failure—verify font size and bad-marker absence too.
16. If the user updates only text in the same Feishu article, do not re-generate or re-upload assets by default. Reuse the previous `thumb_media_id` and previously uploaded `mmbiz.qpic.cn` body image URLs when the new dry-run still has the same ordered image count. Replace `lark-image://...` placeholders in the new dry-run payload by order, then call `draft/add` directly and verify. Abort reuse if counts/order differ.
17. Cover OCR beats literal fidelity. If the article title is long or visually dense and vision/OCR misreads one character (for example confusing “共识” and “认识”, or dropping/garbling “来了”), simplify the generated cover text to 2–3 short high-signal lines, increase font size in the next image_generate prompt, remove decorative chips/tags, and rerun vision QA rather than forcing the full title. Verify OCR against the exact intended overlay strings before publishing. Also simplify subtitle/tag copy if vision QA partially misreads small text (e.g. cost/算粒 labels); prefer fewer, larger labels over dense explanatory copy.
18. If the user corrects the source URL/document after an initial wrong link, explicitly discard the earlier source and restart extraction/publish from the corrected Feishu doc. Do not merge context, title, cover idea, or digest from the stale source.
19. For large Feishu docs with many images, formal publish may keep stdout/stderr empty until the final JSON is flushed; observed successful 279-image runs can sit at 0-byte logs for ~18 minutes. To avoid false hangs and silent stalls, run it as a tracked background process, poll process status, inspect child process only if needed, and wait for completion rather than killing solely because logs are empty. Report progress by polling assets/process state, not just log tails.
20. Code-block QA must inspect the final `draft/get`, not only dry-run HTML. WeChat may strip styles from `<code>` while preserving `<pre>`, Mac dot `<span>`, and inner code-line `<span>` styles. For Mac-style code blocks, keep the dot row at `padding:10px 14px 0`, add durable code-line wrappers with `padding-left:14px`, and add `padding-top:8px` on the first code-line wrapper for breathing room. Do not rely on `<code>` padding, SVG margin, or spacer spans; async WeChat sanitization can revert/strip them. Long code lines must not be clipped on mobile, but the old fix (horizontal scroll wrapper `md-code-scroll-wrap` + natural-width `<pre>` with `display:inline-block; min-width:100%; max-width:none`) caused a mobile bug: on overflowing lines the pre physically grows past the viewport and paints its light background into the off-screen area to the right. The durable pattern is now **locked width + line folding**: wrapper `overflow-x: hidden` (no horizontal scroll), pre `display: block; width: 100%; max-width: 100%; white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere;`, and Mac code-line spans get `max-width: 100%; box-sizing: border-box` so they fold inside the locked pre. Put the wrap rules on `<pre>` as well as `<code>` because WeChat strips `<code>` styles. Wrapping preserves all content, so the no-clipping requirement still holds. Exception: line-number mode keeps horizontal scroll (wrapped lines would misalign the number column). Verify final/dry-run HTML has zero `overflow-x: auto` / `max-width: none` in code blocks and contains the pre-wrap/overflow-wrap markers. Code-block body text defaults to 12px: set `font-size: 12px` on the `<pre>` (WeChat strips `<code>` styles); inline `md-inline-code` stays at 90%. After `draft/update`, WeChat may normalize `#FA5151` to `rgb(250, 81, 81)`, so count both when verifying orange styling. See `references/wechat-mac-code-block-alignment.md` for the repro, durable HTML pattern, and verification counts.
20a. List/quote QA must inspect the final `draft/get`, not only dry-run HTML or source Markdown. In the WeChat editor, native `<ul>/<ol>/<li>` markers can be repeated on wrapped visual lines, while flex-based custom lists can split a marker from its text after sanitization. The durable pattern is one ordinary `<p>` per item, with exactly one inline marker span immediately followed by one inline text span; use hanging indent (`padding-left` + negative `text-indent`) for continuation lines. For unordered items emit the standard U+2022 BULLET through the numeric entity `&#8226;` (not the Chinese middle dot U+00B7 / `·` typed by an IME); for ordered items emit `1.`, `2.`, etc. Do not emit native `<ul>/<ol>/<li>`, `display:flex`, or `list-style` for user-facing items. Verify the final HTML: native-list tag counts, flex count, and renderer sentinel tags are all 0; each unordered marker count equals the item count; ordered marker/text share one paragraph. Nested lists are publisher-native since 2026-09-17 (tests/test_nested_list_indent.py): each nesting level renders as its own block section with progressive indent (padding-left 1.6em per level, text-indent stays -1.6em), nested items keep per-item <p> structure, and nested sections are hoisted out of the parent item's inline span as block siblings. Verify with `padding-left: 3.2em` / `md-list-depth-1` counts in final draft/get.
21. Feishu may export terminal snippets as fences like `javascript {wrap}` or `yaml`. If shell commands containing `# ~/.path` are highlighted as JavaScript, Pygments emits red error borders and comments are not gray. Normalize command-looking blocks to Bash before highlighting; verify `border: 1px solid #F00` is 0, comment gray `#6A737D` is present, and spacing before comments survives as `&nbsp;`.
21a. HTTP header-only fences like `Content-Type: application/json` / `Authorization: Bearer; ...` may be highlighted as Pygments error spans and survive into final `draft/get` as `style="border: 1px solid #F00"`. If discovered after publish, do not create a duplicate draft just for this: fetch the draft article, replace the red-border error span style with a neutral readable style (e.g. `color: #24292f;`), keep `content_source_url: ""`, strip read-only fields, call `draft/update`, then re-run verifier plus an explicit red-border count check.
21b. If final `draft/get` shows `lark-image://` residue or escaped `&lt;figure ... lark-image://...&gt;`, do not report success. Inspect the fetched Feishu Markdown for nested or orphaned code fences, especially outer ```markdown blocks containing inner ```bash/plaintext fences. Fix/unwrap the Markdown fence normalization, re-run dry-run until all source images render as real `<img>` placeholders, then republish or update. After creating a clean replacement draft, delete any earlier bad duplicate draft.
21c. Feishu embedded `.mp4` handling: WeChat permanent video material upload has a hard practical limit from the official docs: MP4 and <=10MB. If the source video is larger, compress it first (e.g. `ffmpeg -vf "fps=30,scale='min(1280,iw)':-2" -c:v libx264 -crf 28 -c:a aac -b:a 96k -movflags +faststart`). Upload with `material/add_material?type=video`; then call `material/get_material` on the returned video `media_id` to obtain `vid` such as `apiv_...`. Insert playable video into article HTML as `<iframe class="rich_pages video_iframe" data-vidtype="2" data-mpvid="<vid>" data-cover="<mmbiz poster>" data-src="https://mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl&action=mpvideo&auto=0&vid=<vid>">`. Verify final `draft/get` preserves `<iframe`, `video_iframe`, `data-mpvid`, and the `apiv_...` vid. If video upload still fails, do not leave public-facing “视频素材同步失败” text; fall back to a neutral poster card and keep `content_source_url: ""`.

**Post-publish repair for pipelines that only create video cards:** some Feishu publishers can successfully upload permanent video materials yet render captions such as “已同步到公众号视频素材库；公众号正文暂不支持内嵌播放” instead of an iframe. Do not accept this as final. Read `video_materials` from the publisher JSON (which may be preceded by warning lines, so parse from the first `{`), then for each successful `media_id` call `material/get_material` to resolve `vid`. Replace its matching `<figure class="... md-video-card ...">` in the `draft/get` article with the `rich_pages video_iframe` above, submit `draft/update`, and re-fetch. `material/get_material` may return an empty `cover_url`; use the non-empty `cover_url` recorded in the publisher's `video_materials` item as the fallback. Final QA requires `video_iframe` / `apiv_` counts equal to the number of successfully uploaded videos, zero public failure wording, and neutral cards only for genuinely failed uploads.
21d. For Feishu code blocks declared as ```markdown that contain nested fences such as ```bash, preserve the user's intended outer code block. Markdown parsers will otherwise either unwrap it into正文 headings/lists or let the inner fence prematurely close the block. The durable fix is to extract the outer block from the Feishu source, HTML-escape its full text, render it as one explicit `<pre><code>...</code></pre>`, and verify terms inside the block have an unmatched `<pre>` before them while the next section title has equal `<pre>` / `</pre>` counts before it. Do not report success from API image checks alone when the user points out source code-block intent.
21e. WeChat backend editor can visually confuse a tiny Mac-style `<pre>` immediately before a link + `<hr>` + next section, even when API `draft/get` shows balanced `</pre>`. If the user reports content below a short command block looks swallowed, replace that tiny command `<pre>` with a non-`pre` command card made of `<section><code>...</code></section>`, then verify target terms have equal `<pre>` and `</pre>` counts before them.

21f. Feishu `<grid>/<column>` parallel layouts are NOT understood

21g. Very long code blocks (e.g. appendix lists, 100+ lines) should be height-capped for mobile readability. Post-publish repair: find the long `<pre>` (`<br>` count > 30), extract the leading Mac-dots `<span>` into a fixed `<section>` header above the pre (background `#f6f8fa`, `border-radius: 8px 8px 0 0`), then on the pre replace `overflow: visible` with `overflow-y: auto; overflow-x: visible; max-height: 480px` and set `border-radius: 0 0 8px 8px`. Keep the locked-width wrap pattern from rule 20 intact (no horizontal scroll; long lines fold inside the pre). `max-height` + `overflow-y: auto` survive WeChat sanitization (verified via `draft/get` after `draft/update`). by the publisher: it passes literal `<grid cols="2">`/`<column width="50">` strings into the draft body and renders the images stacked. Post-publish repair: parse the source fetch for each grid's column widths and image tokens (token order in fetch == figure order in draft, both == source `<image>` count), then for each grid replace the whole `<grid …>…</grid>` span in `draft/get` content with `<table style="width:100%; table-layout:fixed; border-collapse:collapse; margin:1.5em 0;"><tbody><tr><td style="width:X%; padding:0 4px; vertical-align:top;">FIG</td>…</tr></tbody></table>`, using the Feishu column widths as td percentages and normalizing figure margin `1.5em 8px` → `0`. Text+image grids work too: wrap the column text in a styled `<p>` as the other td. WeChat preserves these tables (verified: 15 tables / 74 figures survive `draft/update` + re-fetch). Finish with `draft/update` (UTF-8 raw, strip read-only fields) and verify table count, figure count, and zero `<grid`/`<column` residue.

23. When synchronizing this WeChat publishing skill across multiple Hermes profiles, do not leave backup copies under any active `skills/` tree. Backup directories that still contain a `SKILL.md` can create skill-name collisions and make `skill_view('wechat-publishing-workflow')` fail. Move backups outside active skill roots, for example `~/.hermes/skill-sync-backups/wechat-publishing-workflow/`. If a profile already imports the canonical default skill library via `skills.external_dirs: [~/.hermes/skills]`, prefer that canonical copy instead of duplicating a local profile copy.
24. Every article pushed to the WeChat draft box must end with two extra trailing blank lines so the last content block is not visually glued to the editor bottom / 阅读原文 area. Before `draft/add` (and on any `draft/update` that rewrites the body), append exactly two empty spacer paragraphs at the very end of the article HTML: `<p><br></p><p><br></p>` (plain empty paragraphs are WeChat-stable; do not use styled sections or `&nbsp;` fillers that can be stripped into nothing). Verify via `draft/get` that the content tail ends with the two spacer paragraphs; note WeChat normalizes `<br>` to `<br  />` after `draft/update`, and may wrap them as `<p><span leaf=""><br  /></span></p>` followed by a hidden `<p style="display: none;"><mp-style-type ...></p>` marker — so verify by checking for two trailing empty `<p>` paragraphs immediately before that hidden marker, not an exact string match.
25. When the user asks to (re)push a Feishu doc to the draft box, first check session history and existing drafts for the same doc: the article may already have a pushed draft with a user-approved cover, manual edits, and post-publish repairs (grid tables, video iframes, height caps). Reusing that context avoids duplicates and regressions. Before publishing, state whether this is a new draft or an update of an existing one, and which cover is being used and why. If a previous draft exists but the user wants a fresh push, still reuse prior decisions (cover, repairs) unless told otherwise; verify an old `draft/get` returning `40007 invalid media_id` means the draft was deleted. When re-pushing a doc that previously had playable video iframes, the publisher may fail video re-uploads and emit public "视频素材同步失败" fallback cards; instead of re-uploading, recover the previously working `<iframe class="video_iframe rich_pages">` tags (e.g. `wxv_...` vids) from the local archived `draft/get` JSON of the earlier push and replace the video cards positionally (same doc ⇒ same video order). Final QA: `video_iframe` count matches source video count, zero `md-video-card` failure wording.

## WeChat Cover Art Direction: “汤底 + 佐料”

### Hard constraint: WeChat article covers
For this user, every WeChat Official Account **article cover** must be generated as a complete finished image via `image_generate` / `image_gen`, including title, subtitle, tags, and public-facing text. Do **not** generate a background and then add/repair cover text with PIL, HTML, SVG, canvas, screenshots, or other code. Code is allowed only for format-only operations: crop, resize, compress, rename, upload. If generated text/OCR fails, regenerate with simpler/fewer/larger words; do not fix it locally with code unless the user explicitly overrides this rule for that single task.


For this user's WeChat Official Account covers, follow the Xiaoxiaodong-style reusable cover method: keep a strong reusable base prompt (“汤底”), then choose 1–2 article-specific style ingredient sets (“佐料”). This is now part of the default cover standard, especially after the user flagged recent cover taste drift.

### Base prompt / 汤底
- Do not merely typeset the title; first understand why the article deserves attention.
- Distill the article into: one strong main title, one value subtitle, a few restrained cues/proofs/scenes.
- Prioritize mobile readability: large clear text, clean hierarchy, breathing whitespace, no dense copy.
- Use premium poster/card judgment: Apple-like restraint, credible recommendation tone, high signal in 3 seconds.
- Extract the article/project/brand/text “visual DNA” and extend it into one coherent cover.
- The output should feel seriously selected, understood, and recommended — not information搬运.

### Reusable cover prompt template / 可直接复用模板

```text
请根据用户提供的公众号文章/标题/摘要，生成一张高质感微信公众号封面。封面比例默认 2.35:1。

你要先理解这篇文章为什么值得被看见，而不是把标题简单排版。请提炼它的核心价值、适合人群、情绪判断、传播理由与可信线索。不要写成资料搬运，不要写成说明书，不要堆满小字。

画面必须让手机端用户 3 秒内看懂：这是什么、为什么值得点开、它真正打动人的地方在哪里。

最终画面应自然收束为：
- 一个强主标题；
- 一句点明价值的副标题；
- 少量核心看点、证据、场景或情绪余韵；
- 清晰层级、足够留白、可读的大字。

视觉上请提取文章/项目/品牌/文本气质的视觉 DNA，并选择 1–2 组最匹配的“佐料”作为统一风格系统。版式、图形、颜色、文字节奏都应从内容气质自然生长，不要套廉价模板。

质量目标：高级、清晰、抓人、可信，有一种被认真筛选、认真理解、认真推荐过的感觉。避免泛 AI 壁纸、文字硬贴图、随机图标拼贴、过度装饰、小字过密、移动端不可读。
```

### Ingredient sets / 佐料候选
Pick only what matches the article mood; do not stack everything.
- 建筑图纸：空间秩序 + 中轴网格 + 细密注释 + 工程字体 + 石墨灰。
- 科技极简：居中排版 + 小字点缀 + 设计黑体 + 莫兰迪/渐变 + 韩系几何。
- 力量暗色：暗色渐变 + 多层次小字 + 情绪字体 + 象征插画。
- 东方文人：留白意境 + 题跋章法 + 印章小字 + 水墨抽象 + 朱砂红。
- 电影片头：宽银幕 + 克制神秘 + 字幕排版 + 暗金 + 叙事情绪。
- 手账生活：日期天气小字 + 手写感 + 温柔极简 + 鼠尾草绿。
- 线条治愈：圆体 + 线条艺术 + 柔和渐变 + 治愈配色。
- 产品手册：蓝色强调 + 手册秩序 + 多层小字 + 产品感插画。
- 艺术展览：诗性留白 + 碎片小字 + 抽象插画 + 雾紫。
- 综艺预告：贴纸小字 + 爆梗标题 + 明亮极简 + 柠檬黄。

### Quality bar
Before publishing, reject covers that look like: generic AI wallpaper, text pasted on image, overfull小字, illegible mobile thumbnail, random icon collage, weak article understanding, or no clear style ingredient.

Local Chinese text overlays are forbidden for routine WeChat article covers. If the user explicitly overrides this for a one-off, measure text with `textbbox`, use generous padding, and verify no overflow or baseline sinking.

For small tag chips/buttons on covers, avoid low-contrast combinations such as white/pale fill with white text. Use dark solid fill + orange border, or orange solid fill + white text. Verify tag text remains readable at thumbnail size. If multiple color tags are requested horizontally, measure/QA that the tag rectangles do not overlap or visually collide; leave obvious spacing between tags. If the cover is already content-dense, or tag text shows OCR/shape distortion after QA, remove the chips entirely rather than forcing decorative labels.

For WeChat article covers, always use `image_generate` / `image_gen` to produce the complete visual, including requested tags/text/reference-inspired elements. Never substitute a local PIL/HTML/SVG/code composition that adds text, badges, or pasted logo/reference elements after the fact. Only do format operations such as crop/resize/compress/upload. Run vision QA and regenerate if OCR/tag spacing fails.

Footer/meta text on covers is optional. If QA/OCR misreads small nonessential footer labels, brand signatures, or context text (for example confusing “技术教程” as another word), delete that footer/meta line and rely on the main title + value subtitle. Tiny decorative copy is not worth a second failed OCR pass.

Do not put internal production labels on public-facing WeChat covers, such as “公众号草稿封面”, “草稿”, “测试”, or workflow/debug wording. Footer/meta copy should read like audience-facing editorial context, e.g. “技术教程”, “实战指南”, “案例拆解”, or the author/brand only. Include this in vision QA: exact OCR, no internal labels, no watermark/QR/gibberish.

Recent user preference: for WeChat covers, avoid the recurring dull/dark palette drift. Unless the article clearly requires a serious dark mood, bias toward a brighter, more vivid color system: electric blue, lemon yellow, orange-red, mint/cyan, warm cream, high but tasteful saturation, crisp lighting, and mobile-readable contrast. Dark gradients are acceptable only as local text-safety overlays, not as the whole cover mood. Add “色盘鲜亮不暗淡” to vision QA when the user mentions cover taste or when generating routine official-account covers.

## Feishu Doc + Generated Cover Fast Path

For the user's routine Feishu-doc → WeChat draft pushes, a dedicated generated cover is the default, even if the user only says “推送到公众号草稿箱”. See `references/feishu-doc-default-cover-publish.md` for the concise command recipe. See `references/wechat-cover-imagegen-only-cross-profile.md` for the hard imagegen-only cover rule and the cross-profile propagation checklist. 更多 durable 技术细节见 `references/`：`wechat-mac-code-block-alignment.md`（代码块对齐）、`video-and-markdown-codeblock-pitfalls.md`（嵌套 fence 与视频 iframe）、`wechat-engagement-cta-banner.md`（一键三连横幅）、`wechat-cover-imagegen-only-cross-profile.md`（封面 imagegen-only 规则）、`feishu-doc-default-cover-publish.md`（默认封面快路径命令），以及 6 个被吸收窄 skill 的原文档（`absorbed-*.md`）。

When the user asks to push a Feishu doc to WeChat draft and generate a cover:

Default metadata for this user's WeChat drafts:
- `--author 'DracoVibeCoding'`
- Do **not** pass `--source-url` unless the user explicitly asks to fill the original-link field.

1. Fetch the Feishu doc with `lark-cli docs +fetch --doc <url-or-token> --format pretty` to confirm title, body, image count, and source readability.
2. Generate the cover with `image_generate` / `image_gen` as a complete publication-ready cover by default, including all public-facing title/subtitle/tag text. Do not build the cover by composing a generated background plus local PIL/HTML/SVG/code text overlay. Format-only crop/resize/compress/upload to `2350×1000` is allowed.
3. Export the cover to the final WeChat file first (crop/resize/compress only; `2350×1000` for the default 2.35:1 export), then run `vision_analyze` on that exact final file—not merely on the generator output. Re-OCR every required overlay string after the format operation: a vertical source image may pass OCR before a centered 2.35:1 crop yet lose or distort a character after crop/resize. If any public text fails OCR, regenerate a simpler complete cover; never repair text locally. Also check aspect ratio, theme fit, no text/logo/watermark, and thumbnail readability. Treat 2.35:1 as the project’s chosen WeChat cover export ratio unless the user asks for another ratio.
4. Run preview with the canonical publisher and pass the exact cover path: `--cover-image /abs/path/cover.png`. **CLI pitfall:** `render-preview-feishu-doc` requires an explicit `--output /abs/path/preview.html`; it does not emit preview HTML to stdout, so redirecting stdout alone fails argument validation.
5. Run dry-run with `--thumb-media-id DRY_RUN_MEDIA_ID` to check title/author/digest/body size and renderer regressions; `lark-image://` may remain here and is not a failure.
6. Publish formally with `--cover-image`; for image-heavy docs, run in the background and poll progress. Capture `draft_media_id` and payload `thumb_media_id`.
7. Verify with current WeChat `stable_token` + `draft/get` and `draft/batchget`. If needed, read the cached token from `~/.cache/wechat-draft-publisher/access_token_<appid>.json`, or run the packaged helper: `python <skill_dir>/scripts/verify_wechat_draft.py <draft_media_id>`. Decode response bytes as UTF-8 explicitly; terminal mojibake can otherwise make Chinese titles look corrupted even when API data is fine.
8. Final checks to report: title, author, `draft_media_id`, `thumb_present`, `<img>` count, `mmbiz.qpic.cn` count, `lark-image://` residue = 0, table fixed layout count, orange `#FA5151` / 15px style presence, and absence of known bad renderer markers (`white-space: nowrap`, `display: -webkit-box`).

Reference: `references/video-and-markdown-codeblock-pitfalls.md` captures session-proven details for preserving Feishu outer ` ```markdown ` blocks with nested fences and for inserting compressed MP4 video via WeChat permanent material `vid` / `video_iframe`.

## Interactive Style Selection Card (Feishu → WeChat draft)

每次推送前可选的「卡片选风格」流程（2026-09 落地，已实测通过）：

1. `python scripts/style_select_card.py --token <TASKID> --title "<文章标题>" --doc-url <飞书链接> --output /tmp/card_<TASKID>.json` — 自动读取 publisher `list-styles` 的 ui_schema v2，生成含 7 个下拉控件（主题色/字号/字体/标题样式/代码主题/图注/Mac代码块）+ 提交按钮的卡片，推荐值已预选。
2. `feishu-card --as user --chat-id <oc_...> --json /tmp/card_<TASKID>.json` 发卡。
3. `python scripts/wait_style_choice.py --token <TASKID> --output /tmp/style_<TASKID>.json --timeout 600`（后台跑）— lark-oapi WS 长连接收 `card.action.trigger`，按 token 匹配，把选项映射成 publisher label 格式 style JSON，并回 toast。
4. 收到选择后：`publish-feishu-doc-default ... --style-json "$(cat /tmp/style_<TASKID>.json)"`；超时则走默认风格（活力橙/grace/15px）。

关键事实（别踩坑）：
- 卡片回调是**回调订阅**（不是事件订阅）：开发者后台 → 事件与回调 → **回调配置** Tab → 添加「卡片回传交互 card.action.trigger」→ 长连接接收。应用是 lark-cli 所用的那个飞书自建应用（`lark-cli profile list` 可查 App ID）。
- `lark-cli event +subscribe` 只收事件订阅帧，**收不到卡片回调**；必须用 lark-oapi `EventDispatcherHandler.register_p2_card_action_trigger` + `lark.ws.Client`。
- lark-cli 凭据在文件 keychain：`~/.local/share/lark-cli/master.key` + `appsecret_<appid>.enc`（AES-256-GCM，12B nonce 前缀），脚本内自解密。
- 飞书表单只提交**被用户改动过**的控件值；缺省键 = publisher 推荐默认，无需补齐。
- bool 控件值会以 `True`/`False` 字符串回传，映射时按 BOOL_TRUE 集合判断。

## Same-Article Text Update Asset Reuse

Use this when the source Feishu doc is the same article and the user says only text changed:

1. Run `publish-feishu-doc-default --dry-run --thumb-media-id <old_thumb_media_id>` to rebuild the payload from the current Feishu text without uploading media.
2. Extract old `mmbiz.qpic.cn` body image URLs from the last known-good `draft/get` content, preserving order.
3. Extract new dry-run `lark-image://` placeholders. If the counts differ, stop and use the normal publish path or upload/rewrite the new assets; positional reuse is no longer safe.
4. Replace each new `lark-image://...` image `src` with the corresponding old `mmbiz.qpic.cn` URL. Keep the old cover `thumb_media_id`.
5. If the user asks to “更新公众号草稿箱” / include latest edits in the same existing draft, call `draft/update` on the existing `media_id` + `index: 0` instead of creating a duplicate. Strip read-only fields if starting from `draft/get`; for dry-run payloads, set `thumb_media_id` to the old cover, `content_source_url: ""`, and default comment flags.
6. Only use `draft/add` when the desired outcome is a new replacement draft rather than mutating the existing draft.
7. Verify with `draft/get` and `draft/batchget`: updated tail/text, correct author, thumb present, expected image count, all images are `mmbiz.qpic.cn`, `lark-image://` residue = 0, original-link field empty, orange/15px style retained, no renderer bad markers, and `<pre>` counts balanced.
8. Delete older duplicate drafts only after the new draft passes verification.

## Verification Checklist
- [ ] Extracted article body excludes menus, ads, and related-post noise.
- [ ] Rendered preview matches the target style profile.
- [ ] Access token/media IDs are current.
- [ ] Draft URL or API response is captured for handoff.
- [ ] For Feishu-doc drafts, confirm `draft/get` title/author/thumb, `draft/batchget` visibility, `lark-image://` residue = 0, expected `<img>` count, and no known renderer regressions such as `white-space: nowrap` or `display: -webkit-box`.

## Consolidated knowledge: absorbed narrow skills

The following narrow session skills were absorbed here during the umbrella consolidation pass. Their full original SKILL.md files are preserved under `references/` for recoverability; use this section as the routing index.

### article-to-wechat-cover
- **When it matters:** Cover generation is one stage of WeChat article publishing.
- **Preserved detail:** `references/absorbed-article-to-wechat-cover.md`
- **CTA/banner note:** for “一键三连 / 点赞、转发、在看” engagement images, use the polished cover pipeline and local text overlay; see `references/wechat-engagement-cta-banner.md`.

### doocs-like-wechat-rendering
- **When it matters:** Doocs-like rendering is the styling layer of WeChat draft publishing.
- **Preserved detail:** `references/absorbed-doocs-like-wechat-rendering.md`

### feishu-doc-to-wechat-draft
- **When it matters:** Feishu-to-WeChat draft is a source-to-publish route in the WeChat workflow.
- **Preserved detail:** `references/absorbed-feishu-doc-to-wechat-draft.md`

### wechat-article-browseruse
- **When it matters:** BrowserUse extraction is one backend for WeChat article ingestion.
- **Preserved detail:** `references/absorbed-wechat-article-browseruse.md`

### wechat-article-camofox
- **When it matters:** Camofox extraction is one backend for WeChat article ingestion.
- **Preserved detail:** `references/absorbed-wechat-article-camofox.md`

### wechat-official-account-draft-publisher
- **When it matters:** Official draft publishing is the final API stage of the WeChat workflow.
- **Preserved detail:** `references/absorbed-wechat-official-account-draft-publisher.md`

