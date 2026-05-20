# GPT-Image slide prototype findings

Session context: prototype for replacing HTML screenshots with GPT-Image-2 generated full visual pages in the local EPUB2Podcast pipeline.

## What worked

- Generate a small sample set first: 3-5 representative segments before wiring the batch pipeline.
- Use real `metadata/script.json` segments, not invented demo copy. The sample must test actual script density and Chinese titles.
- One segment -> one image is the right default for high-impact video slides (`image-density=segment`).
- `image_generate(..., aspect_ratio="landscape")` produced usable 1536x1024 samples; evaluate before adding crop/rescale complexity.
- Let the image model generate the full page including Chinese text. Local text overlay was not needed in this prototype.

## Failure mode

GPT-Image-2 can replace Chinese text with semantically similar but wrong phrases.

Observed examples:

- `一只耳环的谈判` became `一日环游的谈判`
- `一枚钱币的远行` became `丝绸之路的远行`
- `从贵霜腹地，到东非修道院` became `到东罗马道院`

This is not a style issue; it is a hard QA failure.

## Prompt pattern that fixed it

For each image prompt, include an exact-text block:

```text
Include ONLY these exact Simplified Chinese texts:
1. 「...」
2. 「...」
3. 「...」

Do NOT write these incorrect phrases:
- 「...」
- 「...」
```

Keep the on-image text short. Prefer title + subtitle + 1-3 compact labels.

## Required QA / retry loop

For `gpt-image-slide` mode, every generated PNG must pass:

1. **Text accuracy**: all required Chinese strings are exact; no extra English, watermark, logo, or hallucinated title.
2. **Segment grounding**: the visual clearly represents the specific segment, not a generic book/road/ancient-history poster.
3. **Visual impact**: image feels like comic / infographic / cinematic poster / documentary spread, not a flat PPT slide.
4. **Legibility**: title readable at video scale; avoid crowded layouts.

If QA fails:

- Regenerate with a stricter exact-text block.
- Add the observed wrong phrases to `Do NOT write...`.
- Do not proceed to video composition with failed text.

## Batch integration rule

Do not connect full batch generation until a 3-5 image sample sheet has been reviewed. This prevents wasting many image calls on a weak style bible or broken text-control pattern.

Reference sample artifacts from the prototype session lived under:

```text
./deliveries/epub2podcast-gpt-image-samples/
```
