# YouTube title/description rules for EPUB2Podcast

Session learning: when publishing podcast delivery pages, fallback YouTube `description` must preserve the original project's intent instead of inventing a generic delivery blurb.

## Source-of-truth behavior

In the source project, `scriptService.generateMarketingContent(...)` builds marketing assets from a `script outline with timestamps`:

- The LLM generates only `title` and `description`.
- The thumbnail prompt is generated separately from extracted hook/CTR logic.
- Description requirements:
  - engaging summary
  - key takeaways
  - accurate timestamps
  - timestamps formatted as `[MM:SS] Topic`
  - at least 5 timestamps covering intro, key concepts, conclusion
  - hashtags at the end

## Pitfalls

- Do **not** write “这期用双人播客的方式……” in the YouTube description. That describes the production format, not the content value.
- Do **not** paste raw dialogue lines as timestamps. YouTube timestamps are section labels / content divisions.
- Do **not** derive timestamps from arbitrary fixed indices when better metadata exists.

## Fallback generation rule

When `metadata/marketing.json` is missing and `publish_podcast_site.py` must synthesize fallback marketing:

1. Title: content-focused and high-CTR, but not hardcoded to a specific book/topic.
2. Description shape:
   - one short paragraph describing the book/content focus
   - `你会看到：` bullets for key takeaways
   - `时间轴：` with `MM:SS 主题` lines
   - hashtags at the end
3. Timestamp labels:
   - prefer `visualPrompt.title`, `subtitle`, `keyLine`, or `visualHook`
   - parse structured prompt titles such as `【标题】...`
   - use neutral section labels like `开场与核心问题` / `总结与延伸思考`
   - only use dialogue text as last-resort signal, condensed into a topic label; never copy the line verbatim

## Verification

Before publishing a delivery page, inspect the rendered/asset description and confirm:

- no “双人播客方式” filler
- no timestamp line is a full dialogue quote
- there are at least 5 meaningful timestamp sections when the script is long enough
- thumbnail prompt remains separate from description generation
