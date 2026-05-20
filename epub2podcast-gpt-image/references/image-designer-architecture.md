# Image Designer Architecture Notes

Session-derived design notes for the GPT-Image-2 visual mode in `epub2podcast-local-optimized`.

## Core correction

Do not treat generated visuals as text-free backgrounds. In this environment, `image_generate` maps to GPT-Image-2 and should be used to generate complete visual pages, including accurate Chinese text, when prompted correctly.

## User preference

The visual output must not look like stiff PPT pages. Use GPT-Image-2's visual strength aggressively:

- knowledge comic frames
- infographics
- cinematic poster frames
- documentary editorial images
- concept metaphor images
- quote posters
- map/timeline visuals

The image ratio should remain 4:3 with a 1080p-class target (`1440x1080`). For early experiments, use the tool's `landscape` parameter first and evaluate the result before implementing crop/fit logic.

## Required module

Introduce an `image_designer` module between script generation and image generation.

Responsibilities:

1. Read `book.json`, `script.json`, chapter structure, segment timing, and neighboring segment context.
2. Create an episode-level style bible.
3. For each segment, decide the visual strategy.
4. Extract the exact information that should appear in that image.
5. Build a GPT-Image-2 prompt with exact required Chinese text.
6. Run visual QA and retry when the frame is weak, PPT-like, off-topic, misspelled, or includes unwanted extra text.

## Segment dependency rule

Every image must be derived from its corresponding segment. A good-looking generic image is a failure if it does not carry the current segment's message.

Suggested inputs per frame:

- `bookTitle`
- chapter / section context
- current `segment.text`
- previous and next segment summaries
- segment duration
- segment index / total segments
- episode `style_bible`

## ImageDesignSpec sketch

```json
{
  "segmentIndex": 5,
  "strategy": "knowledge-comic",
  "title": "一件器物的远行",
  "subtitle": "古物记录了贸易，也记录了人的迁徙",
  "requiredText": [
    "一件器物的远行",
    "贸易背后，是人的移动"
  ],
  "visualHook": "a split-panel comic showing an ancient artifact passing through different hands across cities",
  "contentLogic": "show how trade routes are also human migration routes",
  "avoid": ["PPT look", "generic business icons", "random English text"]
}
```

## Architecture shape

```text
Ebook -> Parser -> Script Engine -> image_designer -> image_generate(GPT-Image-2, landscape) -> Vision QA / Retry -> PNG frames -> FFmpeg -> Final MP4
```

HTML slide generation remains a fallback only.

## QA rubric

Reject or retry if:

- image looks like a corporate slide / PPT template
- visual impact is weak
- required segment message is missing
- Chinese text is wrong, missing, or illegible
- random English, logo, watermark, or extra text appears
- frame does not fit the episode style bible
