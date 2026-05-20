# GPT-Image Slide Visual Mode Design

## Context

`epub2podcast-local-optimized` is the experimental branch of the local EPUB/PDF/MOBI/AZW3 → two-host Chinese podcast pipeline. The original visual pipeline asks an LLM to write HTML slides, then uses Puppeteer screenshots as PNG frames. The optimized path should use Hermes `image_generate` / GPT-Image-2 to generate the final visual pages directly.

## Core Decision

Use GPT-Image-2 to generate complete, high-impact 4:3 podcast visual pages, including text.

Do **not** optimize toward stiff PPT slides. The output should feel like a sequence of visually rich editorial frames:

- knowledge comic pages
- infographic spreads
- cinematic poster frames
- documentary editorial covers
- dramatic concept art with precise Chinese typography
- magazine-style visual explainers

HTML/Puppeteer remains only as fallback, not the main visual direction.

## Resolution and Aspect

Final video/image target remains 4:3 1080p:

```text
1440x1080
```

Hermes `image_generate` currently exposes `landscape|portrait|square`, not a raw 4:3 size flag. Implementation should therefore use one of these strategies:

1. Prefer a direct GPT-Image-2 backend path if the configured provider exposes exact size such as `1440x1080` or equivalent.
2. If only `image_generate(aspect_ratio="landscape")` is available, prompt GPT-Image-2 to design a centered 4:3 frame with safe margins, then crop/fit to `1440x1080` with automated visual verification.

When post-processing is used, keep both:

- raw generated image
- final processed 1440x1080 image

## New Module: `image_designer`

Add an `image_designer` module between podcast script generation and image generation.

Responsibilities:

1. Read the full book metadata, chapter map, podcast script, and segment timing.
2. Design a global visual direction for the whole episode.
3. Classify each segment into an image strategy.
4. Produce structured `ImageDesignSpec` objects.
5. Convert each spec into a GPT-Image-2 prompt.
6. Validate generated images via vision QA and retry if needed.

Pipeline:

```text
book + chapters + script
  -> image_designer.createEpisodeStyleBible()
  -> image_designer.designFrame(segment)
  -> image_designer.buildPrompt(frameSpec)
  -> image_generate / GPT-Image-2
  -> image_designer.qaFrame(image, spec)
  -> final 1440x1080 PNG
  -> ffmpeg
```

## Image Strategy Palette

The designer should choose per segment, not use one template forever.

| Strategy | Best For | Visual Direction |
|---|---|---|
| `cinematic-poster` | chapter openers, emotional turning points | movie poster, strong subject, dramatic light, giant headline |
| `knowledge-comic` | anecdotes, biographies, processes | comic panels, expressive characters, visual metaphor |
| `infographic-spread` | facts, comparisons, systems, data | editorial infographic, diagrams, arrows, labels, dense but readable |
| `documentary-still` | historical/social scenes | realistic documentary frame, embedded title/caption |
| `concept-metaphor` | abstract ideas | symbolic visual metaphor, surreal/editorial impact |
| `quote-poster` | key quotes or punchlines | large quote typography integrated into art |
| `map-timeline` | geography/history/sequence | stylized map or timeline, clear labels |
| `closing-key-visual` | conclusion | iconic final image + concise takeaway |

## Episode Style Bible

Create once per book and save to `metadata/image_style_bible.json`.

Example:

```json
{
  "episodeTitle": "十件古物中的丝路文明史",
  "visualThesis": "文明在物的流动中彼此改写",
  "globalStyle": "premium Chinese editorial documentary, cinematic realism mixed with graphic infographic design",
  "palette": ["warm ivory", "deep ink black", "aged gold", "oxide red"],
  "typography": "bold readable Simplified Chinese editorial typography, accurate text, strong hierarchy",
  "compositionRules": [
    "4:3 frame, final 1440x1080",
    "large visual hook in every frame",
    "never look like a corporate PowerPoint slide",
    "text integrated into the image as poster/editorial typography",
    "safe margins around all text"
  ],
  "avoid": ["stiff PPT", "generic flat icons", "random English text", "watermark", "logo", "small unreadable text"]
}
```

## ImageDesignSpec Schema

Save all specs to `metadata/image_design_specs.json`.

```json
{
  "segmentIndex": 3,
  "strategy": "infographic-spread",
  "title": "文明在交易中流动",
  "subtitle": "丝路不是路线，而是交换系统",
  "requiredText": [
    "文明在交易中流动",
    "丝路不是路线，而是交换系统",
    "商品、技术、宗教与审美一起迁移"
  ],
  "visualHook": "a caravan route becoming a glowing network of objects, cities, and ideas",
  "contentLogic": "show that trade moves culture, not only goods",
  "sceneElements": ["camel caravan", "ancient coins", "silk fabric", "city silhouettes", "route lines"],
  "layoutDirection": "high-impact editorial infographic, not a presentation slide",
  "ratio": "4:3",
  "targetResolution": "1440x1080"
}
```

## GPT-Image-2 Prompt Rules

Every prompt should include:

1. Exact required Chinese text.
2. Strong visual strategy.
3. 4:3 / 1440x1080 requirement.
4. Explicit ban on PPT-like output.
5. No extra text beyond specified copy.
6. Text quality requirements.
7. Style Bible inheritance.

Prompt skeleton:

```text
Create a complete high-impact 4:3 editorial podcast visual page, final target 1440x1080.

This image is NOT a PowerPoint slide. It should look like a cinematic magazine poster / knowledge comic / premium infographic frame.

Visual strategy: infographic-spread.
Visual hook: a caravan route becoming a glowing network of objects, cities, and ideas.
Scene elements: camel caravan, ancient coins, silk fabric, city silhouettes, route lines.

Include ONLY these exact Simplified Chinese texts, clearly readable and correctly written:
Title: 「文明在交易中流动」
Subtitle: 「丝路不是路线，而是交换系统」
Key line: 「商品、技术、宗教与审美一起迁移」

Typography requirements:
- Chinese text must be accurate, legible, and not misspelled.
- No extra words, no random English, no watermark, no logo.
- Strong hierarchy: title large, subtitle medium, key line smaller but readable.
- Text should be integrated into the poster/infographic composition, not pasted as plain PPT boxes.

Global style: premium Chinese editorial documentary, cinematic realism mixed with graphic infographic design; warm ivory, deep ink black, aged gold, oxide red; dramatic lighting; strong visual impact; safe margins.
```

## QA Requirements

After image generation, run vision QA before accepting a frame.

Check:

- Does it avoid stiff PPT aesthetics?
- Is the frame visually striking?
- Is the required Chinese text present and legible?
- Are there spelling/character errors?
- Is there any extra random text, watermark, or logo?
- Is the final frame 4:3 and fit for 1440x1080 video?
- Does it follow the chosen strategy?
- Does it remain consistent with the episode style bible?

Failure handling:

1. Retry with stricter prompt and fewer required text lines.
2. If text still fails, reduce text to title + one key line.
3. If image generation fails entirely, fallback to old HTML slide and mark fallback in manifest.

## Output Directories

```text
metadata/image_style_bible.json
metadata/image_design_specs.json
metadata/image_prompts.json
metadata/image_qa.json

gpt_image_raw/000.png
gpt_image_slides/000.png
```

Keep existing compatibility outputs:

```text
smart_slides/
smart_slides_html/
```

## Proposed CLI Flags

```bash
epub2podcast-local-run \
  --epub ./book.epub \
  --visual-mode gpt-image-slide \
  --image-density segment \
  --aspect-ratio 4:3 \
  --resolution 1440x1080
```

Recommended defaults for this optimized skill:

- `visual-mode=gpt-image-slide`
- `image-density=segment`
- `aspect-ratio=4:3`
- `resolution=1440x1080`

## MVP Scope

1. Add `image_designer` spec generation without changing audio/script logic.
2. Generate prompts and persist them before calling GPT-Image-2.
3. Generate one image per segment by default.
4. Save raw image and final processed frame.
5. Run QA and retry failed frames.
6. Reuse existing ffmpeg PNG + audio assembly path.
7. Preserve HTML mode as fallback only.

## Prototype Finding: GPT-Image-2 Text Control

Initial sample generation with `image_generate(aspect_ratio="landscape")` on four real segments from 《十件古物中的丝路文明史》 showed:

- Visual impact is strong enough for the target direction; images do not look like stiff PPT slides.
- GPT-Image-2 can generate readable Chinese titles and key lines, but exact text still needs QA.
- First-pass prompts may substitute semantically similar but wrong phrases, e.g. wrong title/subtitle characters.
- A stricter retry prompt fixed the failed samples when it:
  - repeated the exact title explicitly;
  - limited required text to 2-3 lines;
  - said `Include ONLY these exact Simplified Chinese texts`;
  - listed forbidden wrong phrases/characters observed in the failed generation;
  - emphasized `no extra text, no random English, no logo, no watermark`.

Therefore, `image_designer` must include an exact-text QA/retry loop, not just one-shot prompt generation.
